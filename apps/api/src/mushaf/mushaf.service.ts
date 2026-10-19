import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { DatabaseService } from '../db/database.service.js';
import { normalizedSql, RULING_BRIEF_JSON, RULING_FULL_COLS, WORD_COLS } from '../common/sql.js';

import { MAX_AYAT, pageBackward, pageForward, type AyahSize } from './pagination.js';

@Injectable()
export class MushafService {
  constructor(private readonly db: DatabaseService) {}

  private async sura(sura: number) {
    const s = await this.db.one<{ sura: number; name: string; ayat: number; words: number; first_seq: number }>(
      `SELECT sura, min(sura_name) AS name, max(ayah)::int AS ayat,
              count(*)::int AS words, min(seq) AS first_seq
         FROM words WHERE sura = $1 GROUP BY sura`,
      [sura],
    );
    if (!s) throw new NotFoundException(`لا سورةَ برقم ${sura}.`);
    return s;
  }

  /** أحجامُ الآيات بالكلمات، لتقسيم السورة صفحاتٍ متقاربة. */
  private ayahSizes(sura: number) {
    return this.db.query<AyahSize>(
      'SELECT ayah, count(*)::int AS n FROM words WHERE sura = $1 GROUP BY ayah ORDER BY ayah',
      [sura],
    );
  }

  /**
   * آياتٌ من سورةٍ بكلماتها، ومع كلِّ كلمةٍ أحكامُ كلِّ مصادرها.
   * الحكمُ هنا موجَزٌ (بلا العلّة)، والعلّةُ كاملةً في تفصيل الموضع.
   */
  async ayat(sura: number, fromQ?: number, toQ?: number) {
    const meta = await this.sura(sura);
    const sizes = await this.ayahSizes(sura);
    const from = Math.min(Math.max(fromQ ?? 1, 1), meta.ayat);
    let to: number;
    if (toQ !== undefined) {
      if (toQ < from) throw new BadRequestException('to أقلُّ من from.');
      to = Math.min(toQ, meta.ayat, from + MAX_AYAT - 1);
    } else {
      to = pageForward(sizes, from).to;
    }

    const rows = await this.db.query<{ ayah: number; words: unknown[] }>(
      `SELECT w.ayah,
              json_agg(json_build_object(
                'seq', w.seq, 'sura', w.sura, 'sura_name', w.sura_name, 'ayah', w.ayah,
                'wpos', w.wpos, 'text', w.text, 'rulings', w.rulings) ORDER BY w.seq) AS words
         FROM (
           SELECT ${WORD_COLS},
                  COALESCE(json_agg(${RULING_BRIEF_JSON} ORDER BY r.source)
                           FILTER (WHERE r.source IS NOT NULL), '[]') AS rulings
             FROM words w
             LEFT JOIN rulings r ON r.seq = w.seq
            WHERE w.sura = $1 AND w.ayah BETWEEN $2 AND $3
            GROUP BY w.seq
         ) w
        GROUP BY w.ayah
        ORDER BY w.ayah`,
      [sura, from, to],
    );

    return {
      sura: meta,
      from,
      to,
      ayat: rows.map((r) => ({ sura, ayah: r.ayah, words: r.words })),
      prev: from > 1 ? pageBackward(sizes, from) : null,
      next: to < meta.ayat ? pageForward(sizes, to + 1) : null,
    };
  }

  /**
   * تفصيلُ موضعٍ واحد: أحكامُ كلِّ المصادر فيه كاملةً بعللها، والمصادرُ
   * الساكتةُ عنه (وسكوتُها ليس نفياً)، ومقابِلُه في كلِّ رواية.
   */
  async word(seq: number) {
    const word = await this.db.one(`SELECT ${WORD_COLS} FROM words w WHERE w.seq = $1`, [seq]);
    if (!word) throw new NotFoundException(`لا كلمةَ بالتسلسل ${seq}.`);

    const [rulings, silent, riw] = await Promise.all([
      this.db.query(
        `SELECT ${RULING_FULL_COLS} FROM rulings r WHERE r.seq = $1 ORDER BY r.source`,
        [seq],
      ),
      // كلُّ مصدرٍ لا حكمَ له هنا، ومعه: هل الموضعُ داخلَ حدود نسخته؟
      this.db.query(
        `SELECT s.id AS source,
                (s.sura_lo IS NULL OR $2 >= s.sura_lo) AND (s.sura_hi IS NULL OR $2 <= s.sura_hi) AS in_range
           FROM sources s
          WHERE NOT EXISTS (SELECT 1 FROM rulings r WHERE r.seq = $1 AND r.source = s.id)
          ORDER BY s.id`,
        [seq, (word as { sura: number }).sura],
      ),
      this.db.query<{ riwaya: string; pos: number; text: string; hafs_seq: number; align: string }>(
        `SELECT riwaya, pos, text, hafs_seq, align FROM riwaya_words
          WHERE hafs_seq = $1 ORDER BY riwaya, pos`,
        [seq],
      ),
    ]);

    const byRiwaya = new Map<string, { pos: number; text: string; hafs_seq: number; align: string }[]>();
    for (const { riwaya, ...w } of riw) {
      if (!byRiwaya.has(riwaya)) byRiwaya.set(riwaya, []);
      byRiwaya.get(riwaya)!.push(w);
    }

    return {
      word,
      rulings,
      silent,
      riwayat: [...byRiwaya].map(([riwaya, words]) => ({ riwaya, words })),
    };
  }

  /**
   * نصُّ روايةٍ لنطاق آياتٍ من فهرس حفص. يُؤخَذ مدى المواضع من أوّل كلمةٍ
   * مُحاذاةٍ إلى آخرها، فتدخل الكلماتُ غيرُ المُحاذاة (unmatched) في مكانها
   * ولا تسقط.
   */
  async riwayaText(riwaya: string, sura: number, from: number, to: number) {
    const exists = await this.db.one('SELECT 1 AS ok FROM riwayat WHERE id = $1', [riwaya]);
    if (!exists) throw new NotFoundException(`لا روايةَ بالمعرّف ${riwaya}.`);
    const span = await this.db.one<{ lo: number | null; hi: number | null }>(
      `SELECT min(rw.pos) AS lo, max(rw.pos) AS hi
         FROM riwaya_words rw JOIN words w ON w.seq = rw.hafs_seq
        WHERE rw.riwaya = $1 AND w.sura = $2 AND w.ayah BETWEEN $3 AND $4`,
      [riwaya, sura, from, to],
    );
    const words =
      span?.lo == null
        ? []
        : await this.db.query(
            `SELECT pos, text, hafs_seq, align FROM riwaya_words
              WHERE riwaya = $1 AND pos BETWEEN $2 AND $3 ORDER BY pos`,
            [riwaya, span.lo, span.hi],
          );
    return { riwaya, sura, from, to, words };
  }

  /** بحثٌ في كلمات المصحف بعد إسقاط الضبط. يُرجِع الموضعَ وعددَ أحكامه. */
  async search(q: string, limit: number) {
    const words = q.split(' ').filter(Boolean).slice(0, 4);
    if (!words.length) return [];
    // العبارةُ متتاليةٌ: الكلمةُ الأولى ثم ما يليها في تسلسل المصحف
    const joins = words
      .slice(1)
      .map(
        (_, i) =>
          `JOIN words w${i + 1} ON w${i + 1}.seq = w.seq + ${i + 1}
             AND ${normalizedSql(`w${i + 1}.text`)} LIKE $${i + 2}`,
      )
      .join('\n');
    const params: unknown[] = words.map((w, i) => (i === 0 ? `%${escapeLike(w)}%` : `${escapeLike(w)}%`));
    params.push(limit);
    return this.db.query(
      `SELECT ${WORD_COLS},
              (SELECT count(*) FROM rulings r WHERE r.seq = w.seq) AS rulings_count
         FROM words w
         ${joins}
        WHERE ${normalizedSql('w.text')} LIKE $1
        ORDER BY w.seq
        LIMIT $${params.length}`,
      params,
    );
  }
}

function escapeLike(s: string) {
  return s.replace(/[\\%_]/g, (c) => '\\' + c);
}
