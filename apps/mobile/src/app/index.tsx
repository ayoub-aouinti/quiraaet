import { useMemo, useState } from 'react';
import { FlatList, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { Link, router } from 'expo-router';
import { arNum, color, normalizeArabic } from '@jamei/shared';
import { useMeta } from '../lib/meta';
import { row, textRight } from '../lib/rtl';
import { styles } from '../theme';

export default function SuraList() {
  const { suras, sources } = useMeta();
  const [q, setQ] = useState('');
  const list = useMemo(() => {
    const n = normalizeArabic(q);
    if (!n) return suras;
    return suras.filter((s) => normalizeArabic(s.name).includes(n) || String(s.sura) === q.trim());
  }, [q, suras]);
  const total = sources.reduce((n, s) => n + s.counts.total, 0);

  return (
    <View style={styles.screen}>
      <FlatList
        data={list}
        keyExtractor={(s) => String(s.sura)}
        keyboardShouldPersistTaps="handled"
        ListHeaderComponent={
          <View style={s.header}>
            <Text style={styles.h1}>أين يقف القارئ، وبِمَ احتجّ العلماء</Text>
            <Text style={[styles.muted, styles.small]}>
              {arNum(total)} حكماً من {arNum(sources.length)} مصدراً، كلُّ حكمٍ بلفظ كتابه.
            </Text>
            <View style={[row, s.actions]}>
              <Link href="/search" asChild>
                <Pressable style={StyleSheet.flatten([styles.btn, s.flex])}>
                  <Text style={styles.btnText}>البحث في المصحف</Text>
                </Pressable>
              </Link>
              <Link href="/sources" asChild>
                <Pressable style={StyleSheet.flatten([styles.btn, s.flex])}>
                  <Text style={styles.btnText}>المصادر</Text>
                </Pressable>
              </Link>
            </View>
            <TextInput
              style={styles.input}
              placeholder="اسمُ السورة أو رقمُها"
              placeholderTextColor={color.faint}
              value={q}
              onChangeText={setQ}
              accessibilityLabel="تصفية السور"
            />
          </View>
        }
        ItemSeparatorComponent={() => <View style={styles.sep} />}
        renderItem={({ item }) => (
          <Pressable
            style={({ pressed }) => [row, s.item, pressed && { backgroundColor: color.highlight }]}
            onPress={() => router.push({ pathname: '/sura/[id]', params: { id: String(item.sura) } })}
            accessibilityRole="button"
            accessibilityLabel={`سورة ${item.name}`}
          >
            <Text style={s.no}>{arNum(item.sura)}</Text>
            <Text style={s.name}>{item.name}</Text>
            <Text style={[styles.muted, styles.small]}>{arNum(item.ayat)} آية</Text>
          </Pressable>
        )}
      />
    </View>
  );
}

const s = StyleSheet.create({
  header: { padding: 16, gap: 10 },
  actions: { gap: 8 },
  flex: { flex: 1 },
  item: { alignItems: 'center', gap: 12, minHeight: 52, paddingHorizontal: 16, backgroundColor: color.paper },
  no: { width: 34, color: color.ochre, fontSize: 15, textAlign: 'center' },
  name: { flex: 1, fontSize: 16, color: color.ink, ...textRight },
});
