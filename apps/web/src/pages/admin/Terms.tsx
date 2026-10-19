import { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { CATEGORY_NOTE, arNum, sourceShort, type CategoryId, type Term, type TermPatch } from '@jamei/shared';
import { CategoryBadge } from '../../components/Badges';
import { api } from '../../lib/api';
import { useMeta } from '../../lib/meta';
import { useAsync } from '../../lib/useAsync';
import { useStored } from '../../lib/useStored';
import type { AdminCtx } from './AdminLayout';

/**
 * جدولُ المصطلحات: مقابلةُ مصطلح كلِّ مصدرٍ بالفئة العامّة. التعديلُ هنا
 * يمسّ المقابلةَ وحدها، ولا يمسّ لفظَ أيِّ حكمٍ ولا مصطلحَه.
 */
export function Terms() {
  const meta = useMeta();
  const { canWrite } = useOutletContext<AdminCtx>();
  const [source, setSource] = useStored<string>('terms.source', '');
  const [onlyUnreviewed, setOnlyUnreviewed] = useStored<boolean>('terms.unreviewed', false);
  const list = useAsync(() => api.terms(source || undefined), [source]);
  const [rows, setRows] = useState<Record<string, Term>>({});
  const [err, setErr] = useState<string | null>(null);

  const key = (t: Term) => `${t.source}|${t.symbol}`;
  const view = (list.data ?? []).map((t) => rows[key(t)] ?? t).filter((t) => !onlyUnreviewed || !t.reviewed);

  const patch = async (t: Term, p: TermPatch) => {
    setErr(null);
    try {
      const next = await api.patchTerm(t.source, t.symbol, p);
      setRows((r) => ({ ...r, [key(t)]: next }));
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  const total = list.data?.length ?? 0;
  const reviewed = (list.data ?? []).filter((t) => (rows[key(t)] ?? t).reviewed).length;

  return (
    <div>
      <h1>المصطلحات</h1>
      <p className="muted">
        {arNum(reviewed)} من {arNum(total)} مراجَعة. {CATEGORY_NOTE} وضبطُ المقابلة هنا لا يُعيد كتابةَ فئات الأحكام المخزَّنة.
      </p>
      <div className="toolbar">
        <label className="field inline">
          <span>المصدر</span>
          <select value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="">الكلّ</option>
            {meta.sources.map((s) => (
              <option key={s.id} value={s.id}>
                {sourceShort(s.id, s.name)}
              </option>
            ))}
          </select>
        </label>
        <label className="check">
          <input type="checkbox" checked={onlyUnreviewed} onChange={(e) => setOnlyUnreviewed(e.target.checked)} />
          غيرُ المراجَعة وحدها
        </label>
      </div>
      {!canWrite && <p className="notice">للاطّلاع وحده. ادخل برمز مراجِعٍ لتضبط المقابلة.</p>}
      {err && <p className="error">{err}</p>}
      {list.error && <p className="error">{list.error.message}</p>}
      <table className="table">
        <thead>
          <tr>
            <th>المصدر</th>
            <th>الرمز</th>
            <th>مصطلحُ المصدر</th>
            <th>الفئة العامّة</th>
            <th>تقريبية</th>
            <th>روجِعت</th>
          </tr>
        </thead>
        <tbody>
          {view.map((t) => (
            <tr key={key(t)} className={t.reviewed ? '' : 'unreviewed'}>
              <td>{sourceShort(t.source)}</td>
              <td className="sym">{t.symbol}</td>
              <td>{t.term}</td>
              <td>
                <span className="cell-flex">
                  <CategoryBadge category={t.category} approx={t.approx} categories={meta.categories} />
                  <select
                    aria-label={`فئة ${t.term}`}
                    disabled={!canWrite}
                    value={t.category ?? ''}
                    onChange={(e) => patch(t, { category: (e.target.value || null) as CategoryId | null })}
                  >
                    <option value="">— غير محدَّدة —</option>
                    {meta.categoryList.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.label}
                      </option>
                    ))}
                  </select>
                </span>
              </td>
              <td>
                <input
                  type="checkbox"
                  aria-label={`مقابلة تقريبية: ${t.term}`}
                  disabled={!canWrite}
                  checked={t.approx}
                  onChange={(e) => patch(t, { approx: e.target.checked })}
                />
              </td>
              <td>
                <input
                  type="checkbox"
                  aria-label={`روجِعت: ${t.term}`}
                  disabled={!canWrite}
                  checked={t.reviewed}
                  onChange={(e) => patch(t, { reviewed: e.target.checked })}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
