import { Injectable } from '@nestjs/common';
import { DatabaseService } from '../db/database.service.js';
import { ReviewLogService } from '../review/review-log.service.js';

type SourceState = 'pending' | 'proposed' | 'imported' | 'verified' | 'mixed';

@Injectable()
export class CatalogService {
  constructor(
    private readonly db: DatabaseService,
    private readonly log: ReviewLogService,
  ) {}

  categories() {
    return this.db.query('SELECT id, label, symbol, color, ord FROM categories ORDER BY ord');
  }

  /**
   * المصادرُ وحالُ كلٍّ منها. والحالُ يُحسَب من أحكامه، فيظهر في الواجهة أنّ
   * المصدرَ مقترَحٌ كلُّه أو مختلط، ولا يُعرَض المقترَحُ معروضَ المستورَد.
   */
  async sources() {
    const rows = await this.db.query<{
      id: string;
      total: number;
      imported: number;
      proposed: number;
      verified: number;
      approx: number;
      review: number;
      [k: string]: unknown;
    }>(`
      SELECT s.id, s.name, s.author, s.died, s.kind, s.edition, s.has_text, s.verified,
             s.sura_lo, s.sura_hi, s.owner_unattributed, s.owner, s.caveats,
             count(r.seq)                                         AS total,
             count(r.seq) FILTER (WHERE r.status = 'imported')    AS imported,
             count(r.seq) FILTER (WHERE r.status = 'proposed')    AS proposed,
             count(r.seq) FILTER (WHERE r.status = 'verified')    AS verified,
             count(r.seq) FILTER (WHERE r.approx)                 AS approx,
             count(r.seq) FILTER (WHERE r.review IS NOT NULL)     AS review
        FROM sources s
        LEFT JOIN rulings r ON r.source = s.id
       GROUP BY s.id
       ORDER BY count(r.seq) DESC, s.id`);
    return rows.map(({ total, imported, proposed, verified, approx, review, ...s }) => ({
      ...s,
      counts: { total, imported, proposed, verified, approx, review },
      state: sourceState(total, imported, proposed, verified),
    }));
  }

  suras() {
    return this.db.query(`
      SELECT sura, min(sura_name) AS name, max(ayah)::int AS ayat,
             count(*)::int AS words, min(seq) AS first_seq
        FROM words GROUP BY sura ORDER BY sura`);
  }

  riwayat() {
    return this.db.query(
      `SELECT id, name, line, region, script, word_count, has_text FROM riwayat
        ORDER BY has_text DESC, word_count DESC, id`,
    );
  }

  async stats() {
    const s = await this.db.one<{
      words: number;
      words_with_rulings: number;
      rulings: number;
      imported: number;
      proposed: number;
      verified: number;
      review_flags: number;
      unknown_symbol: number;
      terms_total: number;
      terms_reviewed: number;
      sources: number;
    }>(`
      SELECT (SELECT count(*) FROM words)                                   AS words,
             (SELECT count(DISTINCT seq) FROM rulings)                      AS words_with_rulings,
             (SELECT count(*) FROM rulings)                                 AS rulings,
             (SELECT count(*) FROM rulings WHERE status = 'imported')       AS imported,
             (SELECT count(*) FROM rulings WHERE status = 'proposed')       AS proposed,
             (SELECT count(*) FROM rulings WHERE status = 'verified')       AS verified,
             (SELECT count(*) FROM rulings WHERE review IS NOT NULL)        AS review_flags,
             (SELECT count(*) FROM rulings WHERE category IS NULL)          AS unknown_symbol,
             (SELECT count(*) FROM terms)                                   AS terms_total,
             (SELECT count(*) FROM terms WHERE reviewed)                    AS terms_reviewed,
             (SELECT count(*) FROM sources)                                 AS sources`);
    if (!s) throw new Error('تعذَّرت قراءةُ الإحصاء.');
    return {
      words: s.words,
      words_with_rulings: s.words_with_rulings,
      rulings: s.rulings,
      by_status: { imported: s.imported, proposed: s.proposed, verified: s.verified },
      review_flags: s.review_flags,
      unknown_symbol: s.unknown_symbol,
      terms: { total: s.terms_total, reviewed: s.terms_reviewed },
      sources: s.sources,
      pending_review: await this.log.pendingCount(),
    };
  }
}

export function sourceState(total: number, imported: number, proposed: number, verified: number): SourceState {
  if (!total) return 'pending';
  if (proposed === total) return 'proposed';
  if (imported === total) return 'imported';
  if (verified === total) return 'verified';
  return 'mixed';
}
