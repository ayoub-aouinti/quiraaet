// أدواتُ النصّ العربي، مشتركةٌ بين الويب والجوال.

/** يكتب العددَ بالأرقام الغربية (0-9)، مع فاصل الآلاف «,». */
export function arNum(n: number | null | undefined): string {
  if (n == null) return '—';
  return Math.trunc(n)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/** علاماتُ الضبط والتطويل وعلاماتُ المصحف الصغيرة التي تُسقَط عند البحث. */
export const MARKS_RE = /[ؐ-ًؚ-ٰٟۖ-ۭـ]/g;

/**
 * يُطبِّع الكلمةَ للبحث: يُسقِط الضبطَ ويوحِّد صورَ الألف والياء.
 * وهو للبحث وحده، ولا يُكتَب به في القاعدة شيء.
 */
export function normalizeArabic(s: string): string {
  return s
    .replace(MARKS_RE, '')
    .replace(/[ٱأإآ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/\s+/g, ' ')
    .trim();
}
