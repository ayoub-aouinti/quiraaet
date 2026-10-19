import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { DatabaseService } from '../db/database.service.js';
import { ReviewLogService } from '../review/review-log.service.js';

export interface TermPatch {
  reviewed?: boolean;
  category?: string | null;
  approx?: boolean;
}

const TERM_COLS = 'source, symbol, term, category, approx, reviewed';

@Injectable()
export class TermsService {
  constructor(
    private readonly db: DatabaseService,
    private readonly log: ReviewLogService,
  ) {}

  list(source?: string) {
    return source
      ? this.db.query(`SELECT ${TERM_COLS} FROM terms WHERE source = $1 ORDER BY source, symbol`, [source])
      : this.db.query(`SELECT ${TERM_COLS} FROM terms ORDER BY source, symbol`);
  }

  /**
   * ضبطُ مقابلةِ مصطلحٍ بالفئة العامّة. يمسّ جدولَ المصطلحات وحده: لا يُعيد
   * كتابةَ فئات الأحكام ولا يمسّ لفظَ المصدر (raw) ولا مصطلحَه (term) —
   * فالمصطلحُ لا يُستبدَل، والفئةُ للّون.
   */
  async patch(source: string, symbol: string, patch: TermPatch, actor: string) {
    await this.log.require();
    const sets: string[] = [];
    const params: unknown[] = [source, symbol];
    if (patch.reviewed !== undefined) {
      params.push(patch.reviewed);
      sets.push(`reviewed = $${params.length}`);
    }
    if (patch.approx !== undefined) {
      params.push(patch.approx);
      sets.push(`approx = $${params.length}`);
    }
    if (patch.category !== undefined) {
      if (patch.category !== null) {
        const ok = await this.db.one('SELECT 1 AS ok FROM categories WHERE id = $1', [patch.category]);
        if (!ok) throw new BadRequestException(`لا فئةَ بالمعرّف ${patch.category}.`);
      }
      params.push(patch.category);
      sets.push(`category = $${params.length}`);
    }
    if (!sets.length) throw new BadRequestException('لا شيءَ يُعدَّل.');

    return this.db.tx(async (c) => {
      const cur = await c.query(`SELECT ${TERM_COLS} FROM terms WHERE source = $1 AND symbol = $2 FOR UPDATE`, [
        source,
        symbol,
      ]);
      const before = cur.rows[0];
      if (!before) throw new NotFoundException('لا مصطلحَ بهذا الرمز لهذا المصدر.');
      const upd = await c.query(
        `UPDATE terms SET ${sets.join(', ')} WHERE source = $1 AND symbol = $2 RETURNING ${TERM_COLS}`,
        params,
      );
      const after = upd.rows[0];
      await this.log.write(c, { actor, entity: 'term', key: { source, symbol }, action: 'patch', before, after });
      return after;
    });
  }
}
