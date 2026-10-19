import { sourceColor, sourceShort, type Category, type Ruling, type Source } from '@jamei/shared';
import { CategoryBadge, StatusBadge } from './Badges';

/**
 * حكمُ مصدرٍ واحدٍ في موضع. يُقدَّم لفظُ الكتاب (raw) بعينه، ثم مصطلحُه
 * المعياريّ، والفئةُ شارةٌ للّون. والعلّةُ تُنقَل كاملةً كما هي.
 */
export function RulingCard({
  ruling,
  source,
  categories,
}: {
  ruling: Ruling;
  source: Source | undefined;
  categories: Record<string, Category>;
}) {
  const showTerm = ruling.term && ruling.term !== ruling.raw;
  return (
    <article className="ruling" style={{ borderInlineStartColor: sourceColor(ruling.source) }}>
      <header className="ruling-head">
        <span className="ruling-src">
          <span className="ruling-src-name">{sourceShort(ruling.source, source?.name)}</span>
          {source && <span className="ruling-src-book">{source.name}</span>}
        </span>
        <StatusBadge status={ruling.status} />
        <CategoryBadge category={ruling.category} approx={ruling.approx} categories={categories} withLabel />
      </header>

      <p className="ruling-raw" title="لفظُ الكتاب بعينه">
        {ruling.raw}
      </p>
      {(showTerm || ruling.symbol) && (
        <p className="ruling-term">
          {showTerm && <span>المصطلح: {ruling.term}</span>}
          {ruling.symbol && <span className="muted"> · الرمز ({ruling.symbol})</span>}
        </p>
      )}
      {ruling.alt_term && (
        <p className="ruling-alt">
          وقولٌ آخرُ في الموضع: {ruling.alt_term}
          {ruling.alt_symbol ? ` (${ruling.alt_symbol})` : ''}
        </p>
      )}

      {ruling.note && (
        <div className="ruling-note">
          <span className="ruling-note-label">العلّة والعزو</span>
          <p>{ruling.note}</p>
        </div>
      )}

      {(ruling.confidence || ruling.review) && (
        <dl className="ruling-meta">
          {ruling.confidence && (
            <>
              <dt>ثقةُ المحاذاة</dt>
              <dd>{ruling.confidence}</dd>
            </>
          )}
          {ruling.review && (
            <>
              <dt>للمراجعة</dt>
              <dd className="flag">{ruling.review}</dd>
            </>
          )}
        </dl>
      )}

      {ruling.context && (
        <details className="ruling-context">
          <summary>نصُّ الكتاب في الموضع</summary>
          <p>{ruling.context}</p>
        </details>
      )}
    </article>
  );
}
