// قطعُ SQL مشتركة بين الوحدات.

/** حقولُ الحكم في عرض القارئ: بلا العلّة الطويلة، ومعها عَلَمُ وجودها. */
export function rulingBriefJson(a = 'r'): string {
  return `json_build_object(
  'source', ${a}.source, 'raw', ${a}.raw, 'symbol', ${a}.symbol, 'term', ${a}.term,
  'category', ${a}.category, 'approx', ${a}.approx, 'status', ${a}.status,
  'alt_term', ${a}.alt_term, 'has_note', (${a}.note IS NOT NULL AND ${a}.note <> ''))`;
}

export const RULING_BRIEF_JSON = rulingBriefJson('r');

/** حقولُ الحكم كاملةً — العلّةُ بلفظ المؤلف كما هي، لا تُلخَّص ولا تُقطَع. */
export function rulingFullCols(a = 'r'): string {
  return ['source', 'raw', 'symbol', 'term', 'category', 'approx', 'status', 'alt_symbol',
    'alt_term', 'note', 'review', 'confidence', 'context'].map((c) => `${a}.${c}`).join(', ');
}

export const RULING_FULL_COLS = rulingFullCols('r');

/** الحكمُ كاملاً كائنَ JSON. */
export function rulingFullJson(a = 'r'): string {
  const cols = ['source', 'raw', 'symbol', 'term', 'category', 'approx', 'status', 'alt_symbol',
    'alt_term', 'note', 'review', 'confidence', 'context'];
  return `json_build_object(${cols.map((c) => `'${c}', ${a}.${c}`).join(', ')})`;
}

export const WORD_COLS = `w.seq, w.sura, w.sura_name, w.ayah, w.wpos, w.text`;

/**
 * تطبيعُ النصّ العربي للبحث في Postgres، مطابقٌ لـ normalizeArabic في
 * packages/shared: يُسقِط الضبطَ والتطويل ويوحِّد صورَ الألف والياء.
 */
export function normalizedSql(col: string): string {
  return `translate(regexp_replace(${col}, '[\\u0610-\\u061A\\u064B-\\u065F\\u0670\\u06D6-\\u06ED\\u0640]', '', 'g'), 'ٱأإآى', 'ااااي')`;
}
