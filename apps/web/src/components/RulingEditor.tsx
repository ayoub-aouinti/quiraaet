import { useEffect, useMemo, useState, type FormEvent, type ReactNode } from 'react';
import { sourceShort, type CategoryId, type Ruling, type RulingPatchBody } from '@jamei/shared';
import { api } from '../lib/api';
import { useMeta } from '../lib/meta';
import { useAsync } from '../lib/useAsync';

interface Draft {
  raw: string;
  symbol: string;
  term: string;
  category: CategoryId | '';
  approx: boolean;
  note: string;
  reason: string;
}

type Initial = Partial<Pick<Ruling, 'raw' | 'symbol' | 'term' | 'category' | 'approx' | 'note'>>;

const toDraft = (r: Initial): Draft => ({
  raw: r.raw ?? '',
  symbol: r.symbol ?? '',
  term: r.term ?? '',
  category: r.category ?? '',
  approx: r.approx ?? false,
  note: r.note ?? '',
  reason: '',
});

/**
 * نموذجُ حكمٍ يملؤه المراجِع: لفظُ المصدر (raw) ورمزُه ومصطلحُه والفئةُ العامّة
 * وعلّتُه بلفظ المؤلف. وجدولُ مصطلحات المصدر يُقترَح منه ما يوافق الرمزَ ولا
 * يُطبَّق من تلقاء نفسه — فالرمزُ يختلف معناه بين الكتب، ولكلِّ كتابٍ جدولُه.
 *
 * يُرسِل `onSave` ما تغيَّر وحدَه عند التعديل، وكلَّ الحقول عند الإنشاء.
 */
export function RulingEditor({
  source,
  initial,
  create,
  busy,
  onSave,
  onCancel,
  extra,
}: {
  source: string;
  initial: Initial;
  /** إنشاءٌ لا تعديل: تُرسَل كلُّ الحقول، ولا يُشترَط تغيُّرٌ لتفعيل الحفظ. */
  create?: boolean;
  busy: boolean;
  onSave: (body: RulingPatchBody) => void;
  onCancel?: () => void;
  /** أزرارٌ إضافية بجانب الحفظ، مثل «احفظ واعتمد». */
  extra?: (ctx: { dirty: boolean; body: RulingPatchBody }) => ReactNode;
}) {
  const meta = useMeta();
  const base = useMemo(() => toDraft(initial), [initial]);
  const [d, setD] = useState<Draft>(base);
  useEffect(() => setD(base), [base, source]);

  const terms = useAsync(() => api.terms(source), [source]);
  const suggestion = terms.data?.find((t) => t.symbol === d.symbol.trim());
  const set = <K extends keyof Draft>(k: K, v: Draft[K]) => setD((x) => ({ ...x, [k]: v }));

  const body: RulingPatchBody = {};
  const changed = (k: 'raw' | 'symbol' | 'term' | 'note') => create || d[k].trim() !== base[k].trim();
  if (changed('raw')) body.raw = d.raw.trim();
  if (changed('symbol')) body.symbol = d.symbol.trim() || null;
  if (changed('term')) body.term = d.term.trim() || null;
  if (changed('note')) body.note = d.note.trim() || null;
  if (create || d.category !== base.category) body.category = d.category || null;
  if (create || d.approx !== base.approx) body.approx = d.approx;
  if (d.reason.trim()) body.reason = d.reason.trim();
  const dirty = Object.keys(body).some((k) => k !== 'reason');
  const valid = !!d.raw.trim();

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (valid && (dirty || create)) onSave(body);
  };

  return (
    <form className="ruling-editor" onSubmit={submit}>
      <p className="muted small">
        المصدر: <b>{sourceShort(source, meta.sourceById[source]?.name)}</b>. لفظُ الكتاب الأصليُّ يبقى في سجلّ المراجعة وإن عدَّلتَه.
      </p>

      <label className="field">
        <span>لفظُ المصدر (raw) — كما في الكتاب بعينه</span>
        <input type="text" value={d.raw} onChange={(e) => set('raw', e.target.value)} required />
      </label>

      <div className="ruling-editor-row">
        <label className="field">
          <span>الرمز</span>
          <input type="text" value={d.symbol} onChange={(e) => set('symbol', e.target.value)} list="ruling-symbols" dir="auto" />
          <datalist id="ruling-symbols">
            {(terms.data ?? []).map((t) => (
              <option key={t.symbol} value={t.symbol}>
                {t.term}
              </option>
            ))}
          </datalist>
        </label>
        <label className="field">
          <span>المصطلح</span>
          <input type="text" value={d.term} onChange={(e) => set('term', e.target.value)} />
        </label>
      </div>

      {suggestion && (suggestion.term !== d.term.trim() || (suggestion.category ?? '') !== d.category || suggestion.approx !== d.approx) && (
        <p className="notice small">
          في جدول مصطلحات هذا المصدر: «{suggestion.symbol}» = {suggestion.term}
          {suggestion.reviewed ? '' : ' (لم تُراجَع بعد)'}.{' '}
          <button
            type="button"
            className="link-btn"
            onClick={() => setD((x) => ({ ...x, term: suggestion.term, category: suggestion.category ?? '', approx: suggestion.approx }))}
          >
            طبِّق المصطلحَ والفئة
          </button>
        </p>
      )}

      <div className="ruling-editor-row">
        <label className="field">
          <span>الفئة العامّة (للّون فقط)</span>
          <select value={d.category} onChange={(e) => set('category', e.target.value as CategoryId | '')}>
            <option value="">— بلا فئة —</option>
            {meta.categoryList.map((c) => (
              <option key={c.id} value={c.id}>
                {c.label}
              </option>
            ))}
          </select>
        </label>
        <label className="check">
          <input type="checkbox" checked={d.approx} onChange={(e) => set('approx', e.target.checked)} />
          المقابلةُ تقريبية (≈)
        </label>
      </div>

      <label className="field">
        <span>العلّة بلفظ المؤلف — تُنقَل كما هي ولا تُلخَّص</span>
        <textarea rows={5} value={d.note} onChange={(e) => set('note', e.target.value)} />
      </label>

      <label className="field">
        <span>سببُ التعديل (اختياري، يُقيَّد في السجلّ)</span>
        <input type="text" value={d.reason} onChange={(e) => set('reason', e.target.value)} />
      </label>

      <div className="decide">
        <button type="submit" className="btn primary" disabled={busy || !valid || (!create && !dirty)}>
          {create ? 'أثبِت الحكم' : 'احفظ التعديل'}
        </button>
        {extra?.({ dirty, body })}
        {onCancel && (
          <button type="button" className="btn" disabled={busy} onClick={onCancel}>
            إلغاء
          </button>
        )}
      </div>
    </form>
  );
}
