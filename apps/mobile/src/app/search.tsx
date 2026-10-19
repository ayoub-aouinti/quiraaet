import { useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { router } from 'expo-router';
import { arNum, color, type SearchHit } from '@jamei/shared';
import { api } from '../lib/api';
import { row, textRight } from '../lib/rtl';
import { QURAN_FONT, styles } from '../theme';

export default function Search() {
  const [q, setQ] = useState('');
  const [hits, setHits] = useState<SearchHit[] | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = async () => {
    if (q.trim().length < 2) return;
    setBusy(true);
    setErr(null);
    try {
      setHits(await api.search(q.trim(), 100));
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <View style={styles.screen}>
      <View style={s.bar}>
        <TextInput
          style={styles.input}
          placeholder="كلمةٌ أو عبارة، بلا ضبط"
          placeholderTextColor={color.faint}
          value={q}
          onChangeText={setQ}
          onSubmitEditing={run}
          returnKeyType="search"
          autoFocus
          accessibilityLabel="عبارة البحث"
        />
        <Text style={[styles.muted, styles.small]}>يُسقَط الضبطُ وتُوحَّد صورُ الألف. والعبارةُ كلماتٌ متتالية.</Text>
      </View>
      {busy && <ActivityIndicator />}
      {err && <Text style={[styles.error, styles.pad]}>{err}</Text>}
      {hits && (
        <FlatList
          data={hits}
          keyExtractor={(h) => String(h.seq)}
          ItemSeparatorComponent={() => <View style={styles.sep} />}
          ListEmptyComponent={<Text style={[styles.muted, styles.pad]}>لا نتائج.</Text>}
          renderItem={({ item }) => (
            <Pressable
              style={({ pressed }) => [row, s.hit, pressed && { backgroundColor: color.highlight }]}
              onPress={() => router.push({ pathname: '/word/[seq]', params: { seq: String(item.seq) } })}
            >
              <Text style={s.word}>{item.text}</Text>
              <View>
                <Text style={[styles.muted, styles.small]}>
                  {item.sura_name} {arNum(item.sura)}:{arNum(item.ayah)}
                </Text>
                <Text style={styles.small}>{item.rulings_count ? `${arNum(item.rulings_count)} أحكام` : 'لا حكمَ مسجَّلاً'}</Text>
              </View>
            </Pressable>
          )}
        />
      )}
    </View>
  );
}

const s = StyleSheet.create({
  bar: { padding: 12, gap: 6 },
  hit: { alignItems: 'center', gap: 12, paddingHorizontal: 16, minHeight: 60, backgroundColor: color.paper },
  word: { flex: 1, fontFamily: QURAN_FONT, fontSize: 22, lineHeight: 44, color: color.ink, ...textRight },
});
