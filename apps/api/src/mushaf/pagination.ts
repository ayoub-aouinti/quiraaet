// تقسيمُ السورة صفحاتٍ في القارئ. وليست صفحاتِ المصحف المطبوع: في words
// لا رقمَ صفحة، فتُقسَم السورةُ نطاقاتٍ متقاربةً بعدد الكلمات.

/** نحوُ عددِ كلمات صفحة المصحف. */
export const PAGE_WORDS = 150;
export const MAX_AYAT = 40;

export interface AyahSize {
  ayah: number;
  n: number;
}

/** نطاقٌ يبدأ من آيةٍ ويمتدّ حتى يقارب صفحة. الآيةُ الطويلةُ وحدها صفحة. */
export function pageForward(sizes: AyahSize[], from: number) {
  let total = 0;
  let to = from;
  for (const s of sizes) {
    if (s.ayah < from) continue;
    if (total > 0 && (total + s.n > PAGE_WORDS || s.ayah - from >= MAX_AYAT)) break;
    total += s.n;
    to = s.ayah;
  }
  return { from, to };
}

/** النطاقُ السابقُ الذي ينتهي قبل آيةٍ ما. */
export function pageBackward(sizes: AyahSize[], before: number) {
  let total = 0;
  let from = before - 1;
  for (let i = sizes.length - 1; i >= 0; i--) {
    const s = sizes[i];
    if (s.ayah >= before) continue;
    if (total > 0 && (total + s.n > PAGE_WORDS || before - 1 - s.ayah >= MAX_AYAT)) break;
    total += s.n;
    from = s.ayah;
  }
  return { from, to: before - 1 };
}
