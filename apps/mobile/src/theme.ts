import { StyleSheet } from 'react-native';
import { color } from '@jamei/shared';
import { alignStart, row, textRight } from './lib/rtl';

export const QURAN_FONT = 'AmiriQuran_400Regular';

export const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: color.leaf },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 8, padding: 24, backgroundColor: color.leaf },
  centerText: { textAlign: 'center' },
  pad: { padding: 16 },
  card: { backgroundColor: color.paper, borderWidth: 1, borderColor: color.rule, padding: 14, ...alignStart },
  row: { ...row, alignItems: 'center', gap: 8 },
  h1: { fontSize: 22, fontWeight: '600', color: color.ink, ...textRight },
  h2: { fontSize: 17, fontWeight: '600', color: color.ink, ...textRight },
  text: { fontSize: 15, color: color.ink, lineHeight: 24, ...textRight },
  muted: { color: color.muted, ...textRight },
  small: { fontSize: 12.5 },
  error: { color: color.carmine, ...textRight },
  quran: { fontFamily: QURAN_FONT, color: color.ink, ...textRight },
  btn: {
    minHeight: 44,
    paddingHorizontal: 16,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: color.rule,
    backgroundColor: color.paper,
    alignItems: 'center',
    justifyContent: 'center',
  },
  btnText: { color: color.ink, fontSize: 15 },
  btnPrimary: { backgroundColor: color.lapis, borderColor: color.lapis },
  btnPrimaryText: { color: color.paper },
  input: {
    minHeight: 44,
    borderWidth: 1,
    borderColor: color.rule,
    borderRadius: 4,
    backgroundColor: color.paper,
    paddingHorizontal: 12,
    fontSize: 15,
    color: color.ink,
    ...textRight,
  },
  sep: { height: 1, backgroundColor: color.rule },
});
