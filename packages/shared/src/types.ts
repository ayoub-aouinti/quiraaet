// أنواعُ ما تُرجِعه الواجهةُ البرمجية. وهي مرآةُ db/schema.sql، فإن تغيَّر
// المخطَّطُ تغيَّرت هذه معه.

/** الفئاتُ العامّة: للّون وحده، ولا يُحسَب منها اتفاقٌ ولا اختلاف. */
export type CategoryId = 'tam' | 'kafi' | 'hasan' | 'jaiz' | 'mamnu' | 'muanaqa';

/**
 * حالُ الحكم. `proposed` لا يُعرَض قطُّ على أنه `imported`، و`verified`
 * ما اعتمده مراجعٌ بعد النظر.
 */
export type RulingStatus = 'imported' | 'proposed' | 'verified';

export interface Category {
  id: CategoryId;
  label: string;
  symbol: string;
  color: string;
  ord: number;
}

/** حالُ المصدر في جملته، محسوبٌ من حالات أحكامه. */
export type SourceState = 'pending' | 'proposed' | 'imported' | 'verified' | 'mixed';

export interface SourceCounts {
  total: number;
  imported: number;
  proposed: number;
  verified: number;
  approx: number;
  review: number;
}

export interface Source {
  id: string;
  name: string;
  author: string | null;
  died: string | null;
  kind: 'book' | 'mushaf';
  edition: string | null;
  has_text: boolean;
  verified: boolean;
  sura_lo: number | null;
  sura_hi: number | null;
  owner_unattributed: boolean;
  owner: string[];
  /** تنبيهاتُ books.json بمفاتيحها كما هي — شرطُ الأمانة في العرض. */
  caveats: Record<string, unknown>;
  counts: SourceCounts;
  state: SourceState;
}

export interface Sura {
  sura: number;
  name: string;
  ayat: number;
  words: number;
  first_seq: number;
}

/** الحكمُ في عرض القارئ: بلا العلّة الطويلة، وهي في تفصيل الموضع. */
export interface RulingBrief {
  source: string;
  /** لفظُ الكتاب بعينه — لا يُستبدَل أبداً. */
  raw: string;
  symbol: string | null;
  term: string | null;
  category: CategoryId | null;
  approx: boolean;
  status: RulingStatus;
  alt_term: string | null;
  has_note: boolean;
}

/** الحكمُ كاملاً، ومعه العلّةُ بلفظ المؤلف دون تلخيص. */
export interface Ruling extends Omit<RulingBrief, 'has_note'> {
  alt_symbol: string | null;
  note: string | null;
  review: string | null;
  confidence: string | null;
  context: string | null;
}

export interface Word {
  seq: number;
  sura: number;
  sura_name: string;
  ayah: number;
  wpos: number | null;
  text: string;
}

export interface ReaderWord extends Word {
  rulings: RulingBrief[];
}

export interface Ayah {
  sura: number;
  ayah: number;
  words: ReaderWord[];
}

export interface AyahRange {
  from: number;
  to: number;
}

export interface AyatPage {
  sura: Sura;
  from: number;
  to: number;
  ayat: Ayah[];
  prev: AyahRange | null;
  next: AyahRange | null;
}

export interface RiwayaWord {
  pos: number;
  text: string;
  hafs_seq: number | null;
  align: 'exact' | 'variant' | 'unmatched' | null;
}

export interface Riwaya {
  id: string;
  name: string | null;
  line: string | null;
  region: string | null;
  script: string | null;
  word_count: number;
  has_text: boolean;
}

export interface RiwayaText {
  riwaya: string;
  sura: number;
  from: number;
  to: number;
  words: RiwayaWord[];
}

/** موقعُ مصدرٍ ساكتٍ من الموضع: هل هو داخلَ حدود نسخته المعتمدة؟ */
export interface SourceCoverage {
  source: string;
  in_range: boolean;
}

export interface WordDetail {
  word: Word;
  rulings: Ruling[];
  /** المصادرُ التي ليس لها حكمٌ هنا — وخلوُّها ليس نفياً للوقف. */
  silent: SourceCoverage[];
  riwayat: { riwaya: string; words: RiwayaWord[] }[];
}

export interface SearchHit extends Word {
  rulings_count: number;
}

export interface Term {
  source: string;
  symbol: string;
  term: string;
  category: CategoryId | null;
  approx: boolean;
  reviewed: boolean;
}

export interface Stats {
  words: number;
  words_with_rulings: number;
  rulings: number;
  by_status: Record<RulingStatus, number>;
  review_flags: number;
  unknown_symbol: number;
  terms: { total: number; reviewed: number };
  sources: number;
  pending_review: number;
}

export interface ReviewItem {
  word: Word;
  ruling: Ruling;
  /** ما يقوله غيره في الموضع نفسه — للاستئناس، ولا يُحتجّ به على الكتاب. */
  others: RulingBrief[];
}

export interface ReviewQueue {
  items: ReviewItem[];
  remaining: number;
}

/**
 * قرارُ المراجع. `verify` يرفع الحالَ إلى `verified`.
 * `reject` لا يحذف الحكمَ — يُبقيه مقترَحاً ويُثبِت سببَ الردّ في `review`،
 * فما لم يُتحقَّق منه يُعلَّم ولا يُمحى.
 */
export type ReviewDecision = 'verify' | 'reject';

export interface ReviewDecisionBody {
  decision: ReviewDecision;
  reason?: string;
}

/**
 * ما يعدّله المراجِعُ في حكمٍ قائم. كلُّ تعديلٍ يُقيَّد في سجلّ المراجعة بقيمته
 * قبلُ وبعدُ، فلفظُ الكتاب الأصليُّ يبقى في السجلّ وإن غُيِّر هنا.
 * `''` أو `null` يُفرِغ الحقلَ، وغيابُ الحقل يتركه.
 */
export interface RulingPatchBody {
  raw?: string;
  symbol?: string | null;
  term?: string | null;
  category?: CategoryId | null;
  approx?: boolean;
  note?: string | null;
  reason?: string;
}

/** حكمٌ يُدخِله المراجِعُ يدوياً من الكتاب على كلمةٍ لا حكمَ فيها لهذا المصدر. */
export interface RulingCreateBody extends RulingPatchBody {
  source: string;
  raw: string;
}

export interface TermPatch {
  reviewed?: boolean;
  category?: CategoryId | null;
  approx?: boolean;
}
