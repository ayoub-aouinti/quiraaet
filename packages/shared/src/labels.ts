import type { Category, RulingBrief, RulingStatus, SourceState } from './types';

/** أسماءُ الحالات. «مقترَح» يُسمّى مقترَحاً، ولا يُعرَض معروضَ المستورَد. */
export const statusLabel: Record<RulingStatus, string> = {
  imported: 'مستورَد',
  proposed: 'مقترَح',
  verified: 'محقَّق',
};

export const sourceStateLabel: Record<SourceState, string> = {
  pending: 'ينتظر النصّ',
  proposed: 'مقترَح',
  imported: 'مستورَد',
  verified: 'محقَّق',
  mixed: 'مختلط',
};

/** علامةُ المقابلة التقريبية: تُعرَض ≈ قبل رمز الفئة. */
export const APPROX = '≈';

/** نصُّ الخلوّ: خلوُّ الموضع من حكمٍ ليس نفياً للحكم. */
export const SILENCE_NOTE =
  'خلوُّ الموضع من حكمٍ عند مصدرٍ ليس نفياً للوقف: قد يكون نقصَ مصدرٍ أو إسقاطَ محاذاة.';

/** تنبيهُ الفئات: هي للّون، ولا يُستدَلّ بها على اتفاق. */
export const CATEGORY_NOTE =
  'الفئةُ العامّة للّون وحده. فـ«صالح» عند مصدرٍ و«جائز» عند آخر قد يقعان في فئةٍ واحدة وليسا قولاً واحداً.';

/** عنوانُ تنبيهٍ من تنبيهات books.json: المفتاحُ نفسُه بلا الشَّرطة. */
export function caveatTitle(key: string): string {
  return key.replace(/^_+/, '');
}

/** نصُّ التنبيه كما هو، وإن كان قائمةً أو كائناً عُرض بنيتُه. */
export function caveatText(value: unknown): string {
  if (typeof value === 'string') return value;
  if (Array.isArray(value)) return value.map(caveatText).join('، ');
  return JSON.stringify(value, null, 1);
}

/**
 * رمزُ الفئة كما يُعرَض على الشارة: ≈ إن كانت المقابلةُ تقريبية.
 * فإن لم تُفهَم الفئة (category = NULL) عُرض «؟» ولم يُخمَّن.
 */
export function categoryBadge(
  r: Pick<RulingBrief, 'category' | 'approx'>,
  cats: Record<string, Category>,
): { text: string; color: string; label: string } {
  if (!r.category || !cats[r.category]) {
    return { text: '؟', color: '#8A857B', label: 'رمزٌ لم يُفهَم — ينتظر المراجعة' };
  }
  const c = cats[r.category];
  return {
    text: (r.approx ? APPROX : '') + c.symbol,
    color: c.color,
    label: c.label + (r.approx ? ' (مقابلةٌ تقريبية)' : ''),
  };
}
