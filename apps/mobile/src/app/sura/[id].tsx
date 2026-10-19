import { memo, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { Stack, router, useLocalSearchParams } from 'expo-router';
import { arNum, color, sourceColor, sourceShort, type Ayah, type ReaderWord } from '@jamei/shared';
import { api } from '../../lib/api';
import { useMeta } from '../../lib/meta';
import { useAsync } from '../../lib/useAsync';
import { row } from '../../lib/rtl';
import { QURAN_FONT, styles } from '../../theme';

export default function SuraReader() {
  const { id, from: fromParam } = useLocalSearchParams<{ id: string; from?: string }>();
  const sura = Math.min(Math.max(Number(id) || 1, 1), 114);
  const [from, setFrom] = useState(Number(fromParam) || 1);
  const { hidden } = useMeta();
  const page = useAsync(() => api.ayat(sura, from), [sura, from]);
  const p = page.data;

  return (
    <View style={styles.screen}>
      <Stack.Screen options={{ title: p ? `سورة ${p.sura.name}` : '' }} />
      {page.error && <Text style={[styles.error, styles.pad]}>{page.error.message}</Text>}
      {!p && !page.error && <ActivityIndicator style={{ marginTop: 40 }} />}
      {p && (
        <FlatList
          data={p.ayat}
          keyExtractor={(a) => String(a.ayah)}
          contentContainerStyle={s.list}
          ListHeaderComponent={
            <Text style={[styles.muted, styles.small, s.range]}>
              الآيات {arNum(p.from)}–{arNum(p.to)} من {arNum(p.sura.ayat)} · اضغط الكلمةَ المظلَّلة لترى أقوال المصادر
            </Text>
          }
          renderItem={({ item }) => <AyahView ayah={item} hidden={hidden} />}
          ListFooterComponent={
            <View style={[row, s.nav]}>
              {p.prev ? (
                <Pressable style={styles.btn} onPress={() => setFrom(p.prev!.from)}>
                  <Text style={styles.btnText}>السابقة</Text>
                </Pressable>
              ) : (
                <View />
              )}
              {p.next ? (
                <Pressable style={[styles.btn, styles.btnPrimary]} onPress={() => setFrom(p.next!.from)}>
                  <Text style={styles.btnPrimaryText}>التالية</Text>
                </Pressable>
              ) : sura < 114 ? (
                <Pressable
                  style={[styles.btn, styles.btnPrimary]}
                  onPress={() => router.replace({ pathname: '/sura/[id]', params: { id: String(sura + 1) } })}
                >
                  <Text style={styles.btnPrimaryText}>السورة التالية</Text>
                </Pressable>
              ) : (
                <View />
              )}
            </View>
          }
        />
      )}
    </View>
  );
}

const AyahView = memo(function AyahView({ ayah, hidden }: { ayah: Ayah; hidden: Set<string> }) {
  return (
    <View style={[row, s.ayah]}>
      {ayah.words.map((w) => (
        <WordView key={w.seq} word={w} hidden={hidden} />
      ))}
      <Text style={s.ayahNo}>﴿{arNum(ayah.ayah)}﴾</Text>
    </View>
  );
});

function WordView({ word, hidden }: { word: ReaderWord; hidden: Set<string> }) {
  const active = word.rulings.filter((r) => !hidden.has(r.source));
  if (!active.length) return <Text style={s.word}>{word.text}</Text>;
  return (
    <Pressable
      onPress={() => router.push({ pathname: '/word/[seq]', params: { seq: String(word.seq) } })}
      style={({ pressed }) => [s.marked, pressed && { backgroundColor: color.highlightOn }]}
      accessibilityRole="button"
      accessibilityLabel={`${word.text}: ${active.map((r) => `${sourceShort(r.source)} ${r.raw}`).join('، ')}`}
      hitSlop={4}
    >
      <View style={[row, s.dots]}>
        {active.map((r) => (
          <View key={r.source} style={[s.dot, { backgroundColor: sourceColor(r.source) }]} />
        ))}
      </View>
      <Text style={s.word}>{word.text}</Text>
    </Pressable>
  );
}

const s = StyleSheet.create({
  list: { padding: 12, paddingBottom: 40 },
  range: { marginBottom: 8 },
  ayah: {
    flexWrap: 'wrap',
    alignItems: 'flex-end',
    columnGap: 6,
    rowGap: 4,
    backgroundColor: color.paper,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderBottomWidth: 1,
    borderBottomColor: color.rule,
  },
  word: { fontFamily: QURAN_FONT, fontSize: 24, lineHeight: 50, color: color.ink },
  marked: { backgroundColor: color.highlight, borderBottomWidth: 2, borderBottomColor: '#B9A77E', paddingHorizontal: 3, borderRadius: 2 },
  dots: { justifyContent: 'center', gap: 2, height: 7 },
  dot: { width: 6, height: 6, borderRadius: 3 },
  ayahNo: { fontFamily: QURAN_FONT, fontSize: 18, lineHeight: 50, color: color.ochre },
  nav: { justifyContent: 'space-between', marginTop: 16 },
});
