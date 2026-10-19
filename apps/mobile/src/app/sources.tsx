import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Switch, Text, View } from 'react-native';
import { arNum, caveatText, caveatTitle, color, sourceColor, sourceShort } from '@jamei/shared';
import { SourceStateBadge } from '../components/Badges';
import { useMeta } from '../lib/meta';
import { row, startBorder, textRight } from '../lib/rtl';
import { styles } from '../theme';

/** المصادر: إظهارُها وإخفاؤها في القارئ، وحالُ كلٍّ منها وتنبيهاتُ نسخته. */
export default function Sources() {
  const { sources, hidden, toggleSource, setAllHidden } = useMeta();
  const [open, setOpen] = useState<string | null>(null);
  const anyHidden = hidden.size > 0;
  return (
    <ScrollView style={styles.screen} contentContainerStyle={s.body}>
      <View style={[row, s.top]}>
        <Text style={[styles.muted, styles.small, { flex: 1 }]}>المُطفأُ لا يظهر في القارئ ولا في تفصيل الموضع.</Text>
        <Pressable onPress={() => setAllHidden(!anyHidden)} hitSlop={8}>
          <Text style={{ color: color.lapis }}>{anyHidden ? 'أظهر الكلّ' : 'أخفِ الكلّ'}</Text>
        </Pressable>
      </View>
      {sources.map((x) => {
        const on = !hidden.has(x.id);
        const expanded = open === x.id;
        return (
          <View key={x.id} style={[s.card, startBorder(4, sourceColor(x.id))]}>
            <View style={[row, s.head]}>
              <Switch
                value={on}
                onValueChange={() => toggleSource(x.id)}
                trackColor={{ true: sourceColor(x.id), false: color.rule }}
                accessibilityLabel={`إظهار ${x.name}`}
              />
              <Pressable style={s.titleCol} onPress={() => setOpen(expanded ? null : x.id)} accessibilityRole="button" accessibilityState={{ expanded }}>
                <Text style={[s.title, !on && { color: color.muted }]}>{sourceShort(x.id, x.name)}</Text>
                <Text style={[styles.muted, styles.small]}>{x.name}</Text>
              </Pressable>
              <View style={s.end}>
                <SourceStateBadge state={x.state} />
                <Text style={[styles.muted, styles.small]}>{arNum(x.counts.total)}</Text>
              </View>
            </View>
            {expanded && (
              <View style={s.more}>
                <Text style={styles.text}>
                  {x.author}
                  {x.died ? ` · ${x.died}` : ''}
                </Text>
                {x.edition && <Text style={[styles.muted, styles.small]}>{x.edition}</Text>}
                <Text style={[styles.muted, styles.small]}>
                  مقترَح {arNum(x.counts.proposed)} · مستورَد {arNum(x.counts.imported)} · محقَّق {arNum(x.counts.verified)} · تقريبية{' '}
                  {arNum(x.counts.approx)}
                </Text>
                {Object.entries(x.caveats).map(([k, v]) => (
                  <View key={k} style={[s.caveat, startBorder(3, color.ochre)]}>
                    <Text style={s.caveatTitle}>{caveatTitle(k)}</Text>
                    <Text style={styles.text}>{caveatText(v)}</Text>
                  </View>
                ))}
              </View>
            )}
          </View>
        );
      })}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  body: { padding: 12, gap: 8, paddingBottom: 40 },
  top: { alignItems: 'center', gap: 10, marginBottom: 4 },
  card: { backgroundColor: color.paper, padding: 12 },
  head: { alignItems: 'center', gap: 10 },
  titleCol: { flex: 1 },
  title: { fontSize: 16, fontWeight: '600', color: color.ink, ...textRight },
  end: { alignItems: 'center', gap: 2 },
  more: { marginTop: 10, gap: 6 },
  caveat: { backgroundColor: color.highlight, padding: 8 },
  caveatTitle: { fontWeight: '600', color: color.ink, ...textRight },
});
