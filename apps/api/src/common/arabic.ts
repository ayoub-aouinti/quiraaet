// نسخةٌ من normalizeArabic في packages/shared/src/arabic.ts. وتُنسَخ لأنّ
// الواجهةَ البرمجية تُترجَم إلى ESM بـtsc وتلك حزمةٌ مصدريّة. فإن عدَّلتَ
// إحداهما فعدِّل الأخرى ونظيرتَهما في SQL (normalizedSql في sql.ts).

const MARKS_RE = /[ؐ-ًؚ-ٰٟۖ-ۭـ]/g;

export function normalizeArabic(s: string): string {
  return s
    .replace(MARKS_RE, '')
    .replace(/[ٱأإآ]/g, 'ا')
    .replace(/ى/g, 'ي')
    .replace(/\s+/g, ' ')
    .trim();
}
