import { useEffect, useState } from 'react';
import { Link, useOutletContext } from 'react-router-dom';
import { arNum, sourceColor, sourceShort, type ReviewItem, type RulingPatchBody } from '@jamei/shared';
import { CategoryBadge, StatusBadge } from '../../components/Badges';
import { RulingCard } from '../../components/RulingCard';
import { RulingEditor } from '../../components/RulingEditor';
import { api } from '../../lib/api';
import { useMeta } from '../../lib/meta';
import { useStored } from '../../lib/useStored';
import { AddRuling } from './AddRuling';
import type { AdminCtx } from './AdminLayout';

/**
 * طابورُ المراجعة. «اعتمد» يرفع الحكمَ إلى محقَّق. «ارفض» لا يحذفه: يبقى
 * مقترَحاً ويُثبَت سببُ الردّ معه. «أجِّل» يتخطّاه في هذه الجلسة وحدها.
 * «عدِّل» يفتح لفظَ المصدر والفئة والعلّة للتصحيح قبل الاعتماد. وتبويبُ
 * «من المصحف» يُدخِل وقفاً جديداً بالنقر على كلمته.
 */
export function Review() {
  const [tab, setTab] = useStored<'queue' | 'mushaf'>('review.tab', 'queue');
  return (
    <div>
      <div className="tabs" role="tablist" aria-label="المراجعة">
        <button type="button" role="tab" aria-selected={tab === 'queue'} onClick={() => setTab('queue')}>
          الطابور
        </button>
        <button type="button" role="tab" aria-selected={tab === 'mushaf'} onClick={() => setTab('mushaf')}>
          أضِف وقفاً من المصحف
        </button>
      </div>
      {tab === 'queue' ? <Queue /> : <AddRuling />}
    </div>
  );
}

function Queue() {
  const meta = useMeta();
  const { canWrite } = useOutletContext<AdminCtx>();
  const [source, setSource] = useStored<string>('review.source', '');
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [remaining, setRemaining] = useState(0);
  const [i, setI] = useState(0);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [reason, setReason] = useState('');
  const [rejecting, setRejecting] = useState(false);
  const [editing, setEditing] = useState(false);

  const load = async (after?: string) => {
    setBusy(true);
    setErr(null);
    try {
      const q = await api.reviewQueue(source || undefined, 20, after);
      setItems(q.items);
      setRemaining(q.remaining);
      setI(0);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [source]);

  const cur = items[i];
  const advance = () => {
    setReason('');
    setRejecting(false);
    setEditing(false);
    if (i + 1 < items.length) setI(i + 1);
    else if (cur) void load(`${cur.word.seq}:${cur.ruling.source}`);
  };

  const decide = async (decision: 'verify' | 'reject') => {
    if (!cur) return;
    setBusy(true);
    setErr(null);
    try {
      await api.decide(cur.word.seq, cur.ruling.source, { decision, reason: decision === 'reject' ? reason : undefined });
      setRemaining((n) => Math.max(0, n - 1));
      advance();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  /** يحفظ تعديلَ المراجِع في الحكم الحاليّ، ويعتمده بعدها إن طُلب. */
  const saveEdit = async (body: RulingPatchBody, thenVerify = false) => {
    if (!cur) return;
    setBusy(true);
    setErr(null);
    try {
      if (Object.keys(body).some((k) => k !== 'reason')) {
        const next = await api.patchRuling(cur.word.seq, cur.ruling.source, body);
        setItems((all) => all.map((x, n) => (n === i ? { ...x, ruling: next } : x)));
      }
      if (thenVerify) {
        await api.decide(cur.word.seq, cur.ruling.source, { decision: 'verify' });
        setRemaining((n) => Math.max(0, n - 1));
        advance();
      } else {
        setEditing(false);
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="review">
      <div className="review-top">
        <div>
          <h1>طابورُ المراجعة</h1>
          <p className="muted">{arNum(remaining)} حكماً مقترَحاً لم يُقضَ فيه{source ? ` عند ${sourceShort(source)}` : ''}.</p>
        </div>
        <label className="field inline">
          <span>المصدر</span>
          <select value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="">كلُّ المصادر</option>
            {meta.sources
              .filter((s) => s.counts.proposed > 0)
              .map((s) => (
                <option key={s.id} value={s.id}>
                  {sourceShort(s.id, s.name)} ({arNum(s.counts.proposed)})
                </option>
              ))}
          </select>
        </label>
      </div>

      {!canWrite && <p className="notice">أنت تطّلع على الطابور دون رمز مراجِع، فأزرارُ القرار معطَّلة.</p>}
      {err && <p className="error">{err}</p>}
      {busy && !cur && <p className="muted">يُحمَّل…</p>}
      {!busy && !cur && !err && <p className="muted">لا شيءَ في الطابور.</p>}

      {cur && (
        <div className="review-grid">
          <section className="review-main">
            <div className="review-word">
              <span className="muted small">الوقف بعد</span>
              <h2 className="quran">{cur.word.text}</h2>
              <Link className="small" to={`/read/${cur.word.sura}?from=${cur.word.ayah}&seq=${cur.word.seq}`}>
                {cur.word.sura_name} {arNum(cur.word.sura)}:{arNum(cur.word.ayah)} — افتحه في المصحف
              </Link>
            </div>

            {editing ? (
              <RulingEditor
                source={cur.ruling.source}
                initial={cur.ruling}
                busy={busy || !canWrite}
                onSave={(b) => void saveEdit(b)}
                onCancel={() => setEditing(false)}
                extra={({ body }) => (
                  <button type="button" className="btn" disabled={busy || !canWrite} onClick={() => void saveEdit(body, true)}>
                    احفظ واعتمد
                  </button>
                )}
              />
            ) : (
              <RulingCard ruling={cur.ruling} source={meta.sourceById[cur.ruling.source]} categories={meta.categories} />
            )}

            <div className="decide">
              <button type="button" className="btn primary" disabled={!canWrite || busy || editing} onClick={() => decide('verify')}>
                اعتمد
              </button>
              <button type="button" className="btn" disabled={!canWrite || busy} onClick={() => setEditing((v) => !v)} aria-expanded={editing}>
                عدِّل
              </button>
              <button type="button" className="btn danger" disabled={!canWrite || busy} onClick={() => setRejecting((v) => !v)} aria-expanded={rejecting}>
                ارفض
              </button>
              <button type="button" className="btn" disabled={busy} onClick={advance}>
                أجِّل
              </button>
              <span className="muted small">
                {arNum(i + 1)} من {arNum(items.length)} في هذه الدفعة
              </span>
            </div>
            {rejecting && (
              <form
                className="reject"
                onSubmit={(e) => {
                  e.preventDefault();
                  void decide('reject');
                }}
              >
                <label htmlFor="reason">سببُ الردّ — يُثبَت مع الحكم ولا يُحذَف الحكم</label>
                <textarea id="reason" rows={3} value={reason} onChange={(e) => setReason(e.target.value)} required />
                <button type="submit" className="btn danger" disabled={!reason.trim() || busy}>
                  أثبِت الردّ
                </button>
              </form>
            )}
          </section>

          <aside className="review-others">
            <h3>ماذا يقول غيرُه هنا</h3>
            <p className="muted small">للاستئناس، ولا يُحتجّ به على الكتاب.</p>
            {cur.others.length === 0 && <p className="muted">لا مصدرَ آخرَ عنده حكمٌ في هذا الموضع.</p>}
            <ul className="others">
              {cur.others.map((o) => (
                <li key={o.source} style={{ borderInlineStartColor: sourceColor(o.source) }}>
                  <span>{sourceShort(o.source)}</span>
                  <span className="other-raw">{o.raw}</span>
                  <StatusBadge status={o.status} />
                  <CategoryBadge category={o.category} approx={o.approx} categories={meta.categories} />
                </li>
              ))}
            </ul>
          </aside>
        </div>
      )}
    </div>
  );
}
