import { I18nManager, type TextStyle, type ViewStyle } from 'react-native';

// الواجهةُ عربيةٌ من اليمين إلى اليسار أيّاً كانت لغةُ الجهاز. فإن كان
// التخطيطُ قد انقلب أصلاً (I18nManager.isRTL) تُرِك على حاله، وإلّا قُلِب هنا.
const native = I18nManager.isRTL;

/** صفٌّ يبدأ من اليمين. */
export const row: ViewStyle = { flexDirection: native ? 'row' : 'row-reverse' };

/** نصٌّ يُحاذى إلى اليمين. */
export const textRight: TextStyle = {
  textAlign: native ? 'left' : 'right',
  writingDirection: 'rtl',
};

/** محاذاةُ عناصر العمود إلى اليمين. */
export const alignStart: ViewStyle = { alignItems: native ? 'flex-start' : 'flex-end' };

/** حدُّ البداية (اليمين) — لشريط لون المصدر. */
export function startBorder(width: number, color: string): ViewStyle {
  return native
    ? { borderLeftWidth: width, borderLeftColor: color }
    : { borderRightWidth: width, borderRightColor: color };
}
