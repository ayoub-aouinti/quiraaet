import { Injectable, ServiceUnavailableException } from '@nestjs/common';
import type pg from 'pg';
import { DatabaseService } from '../db/database.service.js';

export interface LogEntry {
  actor: string;
  entity: 'ruling' | 'term';
  key: Record<string, unknown>;
  action: string;
  before: unknown;
  after: unknown;
  reason?: string | null;
}

/**
 * سجلُّ المراجعة (db/app_schema.sql). لا تقع كتابةٌ بلا سجلّ: فإن لم يُطبَّق
 * الجدولُ بعدُ رُفضت طلباتُ الكتابة، وبقيت القراءةُ تعمل.
 */
@Injectable()
export class ReviewLogService {
  private present: boolean | undefined;

  constructor(private readonly db: DatabaseService) {}

  async available(): Promise<boolean> {
    if (this.present) return true;
    const r = await this.db.one<{ t: string | null }>(`SELECT to_regclass('review_log')::text AS t`);
    this.present = !!r?.t;
    return this.present;
  }

  async require() {
    if (!(await this.available())) {
      throw new ServiceUnavailableException(
        'سجلُّ المراجعة غيرُ مُنشأ، فالكتابةُ موقوفة. طبِّق db/app_schema.sql (npm run db:app).',
      );
    }
  }

  async write(c: pg.PoolClient, e: LogEntry) {
    await c.query(
      `INSERT INTO review_log (actor, entity, key, action, before, after, reason)
       VALUES ($1, $2, $3, $4, $5, $6, $7)`,
      [e.actor, e.entity, JSON.stringify(e.key), e.action, JSON.stringify(e.before), JSON.stringify(e.after), e.reason ?? null],
    );
  }

  /** عددُ الأحكام المقترَحة التي لم يقع عليها قرارُ مراجِعٍ بعد. */
  async pendingCount(): Promise<number> {
    if (!(await this.available())) {
      const r = await this.db.one<{ n: number }>(`SELECT count(*) AS n FROM rulings WHERE status = 'proposed'`);
      return r?.n ?? 0;
    }
    const r = await this.db.one<{ n: number }>(
      `SELECT count(*) AS n FROM rulings r
        WHERE r.status = 'proposed'
          AND NOT EXISTS (SELECT 1 FROM review_log l
                           WHERE l.entity = 'ruling'
                             AND l.key @> jsonb_build_object('seq', r.seq, 'source', r.source))`,
    );
    return r?.n ?? 0;
  }
}
