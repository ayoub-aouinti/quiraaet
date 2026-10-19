import { useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { color, sourceColor, sourceShort, type Category, type Ruling, type Source } from '@jamei/shared';
import { row, startBorder, textRight } from '../lib/rtl';
import { CategoryBadge, StatusBadge } from './Badges';

/**
 * حكمُ مصدرٍ واحد. لفظُ الكتاب (raw) أوّلاً وبعينه، والفئةُ شارةٌ للّون،
 * والعلّةُ كاملةً كما هي — لا تُلخَّص ولا تُقطَع.
 */
export function RulingView({
  ruling,
  source,
  categories,
}: {
  ruling: Ruling;
  source: Source | undefined;
  categories: Record<string, Category>;
}) {
  const [ctx, setCtx] = useState(false);
  const showTerm = ruling.term && ruling.term !== ruling.raw;
  return (
    <View style={[s.box, startBorder(4, sourceColor(ruling.source))]}>
      <View style={[row, s.head]}>
        <View style={s.srcCol}>
          <Text style={s.src}>{sourceShort(ruling.source, source?.name)}</Text>
          {source && <Text style={s.book}>{source.name}</Text>}
        </View>
        <StatusBadge status={ruling.status} />
      </View>

      <Text style={s.raw} accessibilityHint="لفظُ الكتاب بعينه">
        {ruling.raw}
      </Text>
      <View style={[row, s.meta]}>
        <CategoryBadge category={ruling.category} approx={ruling.approx} categories={categories} withLabel />
      </View>
      {(showTerm || ruling.symbol) && (
        <Text style={s.term}>
          {showTerm ? `المصطلح: ${ruling.term}` : ''}
          {ruling.symbol ? `${showTerm ? ' · ' : ''}الرمز (${ruling.symbol})` : ''}
        </Text>
      )}
      {ruling.alt_term && (
        <Text style={[s.term, { color: color.ochre }]}>
          وقولٌ آخرُ في الموضع: {ruling.alt_term}
          {ruling.alt_symbol ? ` (${ruling.alt_symbol})` : ''}
        </Text>
      )}
      {ruling.note && (
        <View style={s.note}>
          <Text style={s.label}>العلّة والعزو</Text>
          <Text style={s.noteText} selectable>
            {ruling.note}
          </Text>
        </View>
      )}
      {ruling.confidence && <Text style={s.small}>ثقةُ المحاذاة: {ruling.confidence}</Text>}
      {ruling.review && <Text style={[s.small, { color: color.carmine }]}>للمراجعة: {ruling.review}</Text>}
      {ruling.context && (
        <Pressable onPress={() => setCtx((v) => !v)} accessibilityRole="button" accessibilityState={{ expanded: ctx }} hitSlop={8}>
          <Text style={[s.small, { color: color.lapis }]}>{ctx ? 'أخفِ نصَّ الكتاب' : 'نصُّ الكتاب في الموضع'}</Text>
        </Pressable>
      )}
      {ctx && ruling.context && (
        <Text style={s.noteText} selectable>
          {ruling.context}
        </Text>
      )}
    </View>
  );
}

const s = StyleSheet.create({
  box: { backgroundColor: color.paper, padding: 12, gap: 6 },
  head: { alignItems: 'flex-start', justifyContent: 'space-between', gap: 8 },
  srcCol: { flex: 1 },
  src: { fontSize: 15, fontWeight: '600', color: color.ink, ...textRight },
  book: { fontSize: 12, color: color.muted, ...textRight },
  raw: { fontSize: 19, fontWeight: '600', color: color.ink, ...textRight },
  meta: { alignItems: 'center', gap: 8 },
  term: { fontSize: 13.5, color: color.ink, ...textRight },
  note: { backgroundColor: color.leaf, padding: 9, gap: 2 },
  label: { fontSize: 11.5, color: color.muted, ...textRight },
  noteText: { fontSize: 14.5, lineHeight: 26, color: color.ink, ...textRight },
  small: { fontSize: 12.5, color: color.muted, ...textRight },
});
