import { StyleSheet, Text, View } from 'react-native';
import {
  categoryBadge,
  color,
  sourceStateLabel,
  statusLabel,
  type Category,
  type CategoryId,
  type RulingStatus,
  type SourceState,
} from '@jamei/shared';
import { row } from '../lib/rtl';

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
    <View style={[row, s.cat]} accessibilityLabel={b.label}>
      <View style={[s.chip, { backgroundColor: b.color }]}>
        <Text style={s.chipText}>{b.text}</Text>
      </View>
      {withLabel && <Text style={s.catLabel}>{b.label}</Text>}
    </View>
  );
}

/** حالُ الحكم. «مقترَح» بإطارٍ متقطِّع أحمر، فلا يُلتبَس بالمستورَد. */
export function StatusBadge({ status }: { status: RulingStatus }) {
  const st = status === 'proposed' ? s.proposed : status === 'verified' ? s.verified : null;
  return (
    <View style={[s.status, st]}>
      <Text style={[s.statusText, status === 'proposed' && { color: color.carmine }, status === 'verified' && { color: '#1B5E3F' }]}>
        {statusLabel[status]}
      </Text>
    </View>
  );
}

export function SourceStateBadge({ state }: { state: SourceState }) {
  const st = state === 'proposed' || state === 'pending' ? s.proposed : state === 'verified' ? s.verified : null;
  return (
    <View style={[s.status, st]}>
      <Text style={[s.statusText, state === 'proposed' && { color: color.carmine }]}>{sourceStateLabel[state]}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  cat: { alignItems: 'center', gap: 6 },
  chip: { minWidth: 28, height: 22, paddingHorizontal: 5, borderRadius: 2, alignItems: 'center', justifyContent: 'center' },
  chipText: { color: color.paper, fontSize: 12 },
  catLabel: { fontSize: 12, color: color.muted },
  status: { paddingHorizontal: 7, paddingVertical: 1, borderRadius: 2, borderWidth: 1, borderColor: color.rule },
  statusText: { fontSize: 11, color: color.muted },
  proposed: { borderStyle: 'dashed', borderColor: color.carmine },
  verified: { borderColor: '#1B5E3F' },
});
