import { ActivityIndicator, ScrollView, StyleSheet, Text, View } from 'react-native';
import { useLocalSearchParams } from 'expo-router';
import { SILENCE_NOTE, arNum, color, sourceColor, sourceShort } from '@jamei/shared';
import { RulingView } from '../../components/RulingView';
import { api } from '../../lib/api';
import { useMeta } from '../../lib/meta';
import { useAsync } from '../../lib/useAsync';
import { row, textRight } from '../../lib/rtl';
import { QURAN_FONT, styles } from '../../theme';

/** تفصيلُ الموضع: كلُّ ما قالته المصادرُ بعد الكلمة، بلفظها وعللها. */
export default function WordDetail() {
  const { seq } = useLocalSearchParams<{ seq: string }>();
  const meta = useMeta();
  const { data, error } = useAsync(() => api.word(Number(seq)), [seq]);

  if (error) return <Text style={[styles.error, styles.pad]}>{error.message}</Text>;
  if (!data) return <ActivityIndicator style={{ marginTop: 40 }} />;

  const shown = data.rulings.filter((r) => !meta.hidden.has(r.source));
  const off = data.rulings.length - shown.length;

  return (
    <ScrollView style={styles.screen} contentContainerStyle={s.body}>
      <View style={s.head}>
        <Text style={[styles.muted, styles.small]}>الوقف بعد</Text>
        <Text style={s.word}>{data.word.text}</Text>
        <Text style={[styles.muted, styles.small]}>
          {data.word.sura_name} {arNum(data.word.sura)}:{arNum(data.word.ayah)}
        </Text>
      </View>

      <Text style={styles.h2}>أقوالُ المصادر ({arNum(shown.length)})</Text>
      {off > 0 && <Text style={[styles.muted, styles.small]}>وأُخفي {arNum(off)} من مصادر أطفأتَها.</Text>}
      {shown.length === 0 && <Text style={styles.muted}>لا حكمَ عند المصادر المختارة هنا.</Text>}
      <View style={s.gap}>
        {shown.map((r) => (
          <RulingView key={r.source} ruling={r} source={meta.sourceById[r.source]} categories={meta.categories} />
        ))}
      </View>

      {data.silent.length > 0 && (
        <View style={s.gap}>
          <Text style={styles.h2}>مصادرُ ساكتةٌ هنا</Text>
          <Text style={[styles.muted, styles.small]}>{SILENCE_NOTE}</Text>
          {data.silent.map((x) => (
            <View key={x.source} style={[row, s.silent]}>
              <View style={[s.dot, { backgroundColor: sourceColor(x.source) }]} />
              <Text style={styles.text}>
                {sourceShort(x.source, meta.sourceById[x.source]?.name)}
                {!x.in_range ? ' — خارجَ حدود نسخته' : ''}
              </Text>
            </View>
          ))}
        </View>
      )}

      {data.riwayat.length > 0 && (
        <View style={s.gap}>
          <Text style={styles.h2}>الموضعُ في الروايات</Text>
          {data.riwayat.map((r) => (
            <View key={r.riwaya} style={[row, s.riw]}>
              <Text style={[styles.muted, s.riwName]}>{meta.riwayat.find((x) => x.id === r.riwaya)?.name ?? r.riwaya}</Text>
              <Text style={s.riwText}>{r.words.map((w) => w.text).join(' ')}</Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  body: { padding: 16, gap: 12, paddingBottom: 40 },
  head: { borderBottomWidth: 3, borderBottomColor: color.lapis, paddingBottom: 8 },
  word: { fontFamily: QURAN_FONT, fontSize: 34, lineHeight: 64, color: color.ink, ...textRight },
  gap: { gap: 8 },
  silent: { alignItems: 'center', gap: 8 },
  dot: { width: 9, height: 9, borderRadius: 5 },
  riw: { alignItems: 'center', gap: 10 },
  riwName: { width: 120 },
  riwText: { flex: 1, fontFamily: QURAN_FONT, fontSize: 22, lineHeight: 44, color: color.ink, ...textRight },
});
