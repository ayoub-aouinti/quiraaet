import { BadRequestException, ConflictException, Injectable, NotFoundException } from '@nestjs/common';
import { DatabaseService } from '../db/database.service.js';
import { RULING_FULL_COLS, rulingBriefJson, rulingFullJson } from '../common/sql.js';
import { ReviewLogService } from './review-log.service.js';

export type Decision = 'verify' | 'reject';

const REJECT_PREFIX = 'رُدَّ في المراجعة: ';
const MANUAL_CONFIDENCE = 'أدخله المراجِعُ يدوياً من الكتاب';
const RULING_FULL_COLS_PLAIN = RULING_FULL_COLS.replace(/r\./g, '');

/** حقولُ النصّ التي يعدّلها المراجِع؛ الفارغُ منها يصير NULL إلا raw فلا يَفرَغ. */
const EDITABLE_TEXT = ['raw', 'symbol', 'term', 'note'] as const;

export interface RulingPatch {
  raw?: string;
  symbol?: string | null;
  term?: string | null;
  category?: string | null;
  approx?: boolean;
  note?: string | null;
  reason?: string;
}

@Injectable()
export class ReviewService {
  constructor(
    private readonly db: DatabaseService,
    private readonly log: ReviewLogService,
  ) {}

  /**
   * طابورُ المراجعة: الأحكامُ المقترَحةُ التي لم يُقضَ فيها بعد، على ترتيب
   * المصحف. ومع كلِّ حكمٍ ما يقوله غيرُه في الموضع نفسه — للاستئناس، ولا
   * يُحتجّ به على الكتاب، ولا يُحسَب منه اتفاق.
   */
  async queue(source: string | undefined, limit: number, after?: { seq: number; source: string }) {
    const logged = await this.log.available();
    const params: unknown[] = [];
    const where = [`r.status = 'proposed'`];
    if (source) {
      params.push(source);
      where.push(`r.source = $${params.length}`);
    }
    if (logged) {
      where.push(`NOT EXISTS (SELECT 1 FROM review_log l WHERE l.entity = 'ruling'
                    AND l.key @> jsonb_build_object('seq', r.seq, 'source', r.source))`);
    }
    const countWhere = where.join(' AND ');
    if (after) {
      params.push(after.seq, after.source);
      where.push(`(r.seq, r.source) > ($${params.length - 1}, $${params.length})`);
    }
    params.push(limit);

    const items = await this.db.query<{ word: unknown; ruling: unknown; others: unknown }>(
      `SELECT json_build_object('seq', w.seq, 'sura', w.sura, 'sura_name', w.sura_name,
                                'ayah', w.ayah, 'wpos', w.wpos, 'text', w.text) AS word,
              ${rulingFullJson('q')} AS ruling,
              (SELECT COALESCE(json_agg(${rulingBriefJson('o')} ORDER BY o.source), '[]')
                 FROM rulings o WHERE o.seq = q.seq AND o.source <> q.source) AS others
         FROM (SELECT r.* FROM rulings r WHERE ${where.join(' AND ')}
                ORDER BY r.seq, r.source LIMIT $${params.length}) q
         JOIN words w ON w.seq = q.seq
        ORDER BY q.seq, q.source`,
      params,
    );

    const countParams = source ? [source] : [];
    const remaining = await this.db.one<{ n: number }>(
      `SELECT count(*) AS n FROM rulings r WHERE ${countWhere}`,
      countParams,
    );
    return { items, remaining: remaining?.n ?? 0 };
  }

  /**
   * قرارُ المراجِع في حكمٍ واحد. الاعتمادُ يرفع الحالَ إلى verified.
   * والردُّ لا يحذف الحكم ولا يُخفيه: يبقى مقترَحاً، ويُضاف سببُ الردّ إلى
   * review بعد ما فيه — فما كان فيه من تعليمٍ سابقٍ لا يُمحى.
   */
  async decide(seq: number, source: string, decision: Decision, reason: string | undefined, actor: string) {
    await this.log.require();
    if (decision === 'reject' && !reason?.trim()) {
      throw new BadRequestException('الردُّ يحتاج سبباً يُثبَت مع الحكم.');
    }
    return this.db.tx(async (c) => {
      const cur = await c.query(
        `SELECT ${RULING_FULL_COLS} FROM rulings r WHERE r.seq = $1 AND r.source = $2 FOR UPDATE`,
        [seq, source],
      );
      const before = cur.rows[0];
      if (!before) throw new NotFoundException('لا حكمَ لهذا المصدر في هذا الموضع.');
      if (before.status === 'verified') throw new ConflictException('الحكمُ محقَّقٌ من قبل.');

      let after;
      if (decision === 'verify') {
        const r = await c.query(
          `UPDATE rulings r SET status = 'verified' WHERE seq = $1 AND source = $2
           RETURNING ${RULING_FULL_COLS}`,
          [seq, source],
        );
        after = r.rows[0];
      } else {
        const r = await c.query(
          `UPDATE rulings r
              SET review = CASE WHEN review IS NULL OR review = '' THEN $3
                                ELSE review || ' · ' || $3 END
            WHERE seq = $1 AND source = $2
           RETURNING ${RULING_FULL_COLS}`,
          [seq, source, REJECT_PREFIX + reason!.trim()],
        );
        after = r.rows[0];
      }

      await this.log.write(c, {
        actor,
        entity: 'ruling',
        key: { seq, source },
        action: decision,
        before,
        after,
        reason: reason?.trim() || null,
      });
      return { ok: true as const };
    });
  }

  /**
   * تعديلُ المراجِع حكماً قائماً: لفظَ المصدر ورمزَه ومصطلحَه وفئتَه العامّة
   * وعلّتَه. لا يمسّ الحالَ (الاعتمادُ قرارٌ مستقلّ)، ويُقيَّد بقيمته قبلُ
   * وبعدُ، فلفظُ الكتاب الأصليُّ يبقى في السجلّ وإن صُحِّح في الحكم.
   */
  async patchRuling(seq: number, source: string, patch: RulingPatch, actor: string) {
    await this.log.require();
    const sets: string[] = [];
    const params: unknown[] = [seq, source];
    const set = (col: string, v: unknown) => {
      params.push(v);
      sets.push(`${col} = $${params.length}`);
    };
    for (const col of EDITABLE_TEXT) {
      if (patch[col] !== undefined) set(col, patch[col]);
    }
    if (patch.category !== undefined) {
      await this.checkCategory(patch.category);
      set('category', patch.category);
    }
    if (patch.approx !== undefined) set('approx', patch.approx);
    if (!sets.length) throw new BadRequestException('لا شيءَ يُعدَّل.');

    return this.db.tx(async (c) => {
      const cur = await c.query(
        `SELECT ${RULING_FULL_COLS} FROM rulings r WHERE r.seq = $1 AND r.source = $2 FOR UPDATE`,
        [seq, source],
      );
      const before = cur.rows[0];
      if (!before) throw new NotFoundException('لا حكمَ لهذا المصدر في هذا الموضع.');
      const upd = await c.query(
        `UPDATE rulings r SET ${sets.join(', ')} WHERE seq = $1 AND source = $2 RETURNING ${RULING_FULL_COLS}`,
        params,
      );
      const after = upd.rows[0];
      await this.log.write(c, {
        actor,
        entity: 'ruling',
        key: { seq, source },
        action: 'patch',
        before,
        after,
        reason: patch.reason?.trim() || null,
      });
      return after;
    });
  }

  /**
   * حكمٌ يُدخِله المراجِعُ من الكتاب على كلمةٍ ليس لهذا المصدر فيها حكم.
   * يُقيَّد محقَّقاً لأنّ مراجِعاً أدخله بنفسه، وعلى `confidence` ما يدلّ على
   * ذلك، فلا يُحسَب مستورَداً. وخلوُّ الموضع من حكمٍ ليس نفياً، فلا يُستنتَج
   * من الإدخال شيءٌ عن غيره.
   */
  async createRuling(seq: number, source: string, body: RulingPatch & { raw: string }, actor: string) {
    await this.log.require();
    if (!body.raw?.trim()) throw new BadRequestException('لفظُ المصدر (raw) مطلوب.');
    if (body.category !== undefined) await this.checkCategory(body.category);
    return this.db.tx(async (c) => {
      const w = await c.query('SELECT 1 FROM words WHERE seq = $1', [seq]);
      if (!w.rows[0]) throw new NotFoundException('لا كلمةَ بهذا الرقم.');
      const s = await c.query('SELECT 1 FROM sources WHERE id = $1', [source]);
      if (!s.rows[0]) throw new BadRequestException(`لا مصدرَ بالمعرّف ${source}.`);
      const dup = await c.query('SELECT 1 FROM rulings WHERE seq = $1 AND source = $2', [seq, source]);
      if (dup.rows[0]) throw new ConflictException('لهذا المصدر حكمٌ في هذا الموضع، فعدِّله ولا تُنشئ.');
      const ins = await c.query(
        `INSERT INTO rulings (seq, source, raw, symbol, term, category, approx, note, status, confidence)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'verified', $9)
         RETURNING ${RULING_FULL_COLS_PLAIN}`,
        [seq, source, body.raw, body.symbol ?? null, body.term ?? null, body.category ?? null,
          body.approx ?? false, body.note ?? null, MANUAL_CONFIDENCE],
      );
      const after = ins.rows[0];
      await this.log.write(c, {
        actor,
        entity: 'ruling',
        key: { seq, source },
        action: 'create',
        before: null,
        after,
        reason: body.reason?.trim() || null,
      });
      return after;
    });
  }

  private async checkCategory(id: string | null) {
    if (id === null) return;
    const ok = await this.db.one('SELECT 1 AS ok FROM categories WHERE id = $1', [id]);
    if (!ok) throw new BadRequestException(`لا فئةَ بالمعرّف ${id}.`);
  }
}

