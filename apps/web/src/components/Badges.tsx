import {
  categoryBadge,
  sourceStateLabel,
  statusLabel,
  type Category,
  type CategoryId,
  type RulingStatus,
  type SourceState,
} from '@jamei/shared';

/** شارةُ الفئة العامّة: للّون وحده، و≈ إن كانت المقابلةُ تقريبية. */
export function CategoryBadge({
  category,
  approx,
  categories,
  withLabel = false,
}: {
  category: CategoryId | null;
  approx: boolean;
  categories: Record<string, Category>;
  withLabel?: boolean;
}) {
  const b = categoryBadge({ category, approx }, categories);
  return (
    <span className="cat" title={b.label}>
      {withLabel && <span className="cat-label">{b.label}</span>}
      <span className="cat-chip" style={{ background: b.color }} aria-label={b.label}>
        {b.text}
      </span>
    </span>
  );
}

/** حالُ الحكم. «مقترَح» بإطارٍ متقطِّع، فلا يُلتبَس بالمستورَد. */
export function StatusBadge({ status }: { status: RulingStatus }) {
  if (status === 'imported') return <span className="status status-imported">{statusLabel.imported}</span>;
  return <span className={`status status-${status}`}>{statusLabel[status]}</span>;
}

export function SourceStateBadge({ state }: { state: SourceState }) {
  return <span className={`status status-${state}`}>{sourceStateLabel[state]}</span>;
}
