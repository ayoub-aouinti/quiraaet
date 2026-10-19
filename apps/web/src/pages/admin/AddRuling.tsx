import { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { arNum, sourceColor, sourceShort, type RulingPatchBody, type WordDetail } from '@jamei/shared';
import { CategoryBadge, StatusBadge } from '../../components/Badges';
import { RulingEditor } from '../../components/RulingEditor';
import { api } from '../../lib/api';
import { useMeta } from '../../lib/meta';
import { useAsync } from '../../lib/useAsync';
import { useStored } from '../../lib/useStored';
import type { AdminCtx } from './AdminLayout';

const NEUTRAL_RULE = '#B9A77E';

/**
 * مصحفٌ للمراجِع: ينقر كلمةً فيُفتَح له نموذجُ حكمٍ يملؤه من الكتاب. فإن كان
 * للمصدر المختار حكمٌ على الكلمة فُتح للتعديل، وإلا فللإنشاء. والنصُّ بحفص
 * لأنّه فهرسُ المحاذاة. وإدخالُ حكمٍ لا يُنشئ شيئاً عن سائر المصادر: خلوُّ
 * الموضع عندها ليس نفياً.
 */
export function AddRuling() {
  const meta = useMeta();
  const { canWrite } = useOutletContext<AdminCtx>();
  const [sura, setSura] = useStored<number>('addruling.sura', 1);
  const [from, setFrom] = useState(1);
  const [seq, setSeq] = useState<number | null>(null);

  const page = useAsync(() => api.ayat(sura, from), [sura, from]);
  const goSura = (s: number) => {
    setSura(s);
    setFrom(1);
    setSeq(null);
  };

  return (
    <div className="add-ruling">
      <div className="review-top">
        <div>
          <h1>أضِف وقفاً من المصحف</h1>
          <p className="muted">انقر كلمةً لتُدخِل حكماً من كتابٍ عليها، أو لتعدِّل حكماً قائماً. النصُّ برواية حفص، وهو فهرسُ المحاذاة.</p>
        </div>
        <label className="field inline">
          <span>السورة</span>
          <select value={sura} onChange={(e) => goSura(Number(e.target.value))}>
            {meta.suras.map((s) => (
              <option key={s.sura} value={s.sura}>
                {arNum(s.sura)}. {s.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {!canWrite && <p className="notice">أنت تطّلع دون رمز مراجِع، فلا يُحفَظ ما تُدخِله.</p>}

      <div className="review-grid">
        <section>
          <div className="mushaf-frame">
            <div className="mushaf-inner">
              {page.loading && !page.data && <p className="muted">يُحمَّل…</p>}
              {page.error && <p className="error">{page.error.message}</p>}
              {page.data && (
                <p className="mushaf-text">
                  {page.data.ayat.map((a) => (
                    <span key={a.ayah}>
                      {a.words.map((w) => {
                        const has = w.rulings.length > 0;
                        return (
                          <span key={w.seq}>
                            <button
                              type="button"
                              className={`w pick ${has ? 'marked' : ''} ${seq === w.seq ? 'sel' : ''}`}
                              style={has ? { borderBottomColor: NEUTRAL_RULE } : undefined}
                              aria-pressed={seq === w.seq}
                              aria-label={`${w.text}${has ? ` — ${arNum(w.rulings.length)} أحكام` : ''}`}
                              onClick={() => setSeq(seq === w.seq ? null : w.seq)}
                            >
                              {w.text}
                            </button>{' '}
                          </span>
                        );
                      })}
                      <span className="ayah-no">﴿{arNum(a.ayah)}﴾ </span>
                    </span>
                  ))}
                </p>
              )}
            </div>
          </div>
          {page.data && (
            <nav className="page-nav" aria-label="التنقّل">
              {page.data.prev ? (
                <button type="button" onClick={() => setFrom(page.data!.prev!.from)}>
                  السابقة
                </button>
              ) : sura > 1 ? (
                <button type="button" onClick={() => goSura(sura - 1)}>
                  السورة السابقة
                </button>
              ) : (
                <span />
              )}
              <span className="muted small">
                الآيات {arNum(page.data.from)}–{arNum(page.data.to)}
              </span>
              {page.data.next ? (
                <button type="button" onClick={() => setFrom(page.data!.next!.from)}>
                  التالية
                </button>
              ) : sura < 114 ? (
                <button type="button" onClick={() => goSura(sura + 1)}>
                  السورة التالية
                </button>
              ) : (
                <span />
              )}
            </nav>
          )}
        </section>

        <aside className="review-others">
          {seq == null ? (
            <p className="muted">اختر كلمةً من المصحف.</p>
          ) : (
            <WordForm key={seq} seq={seq} canWrite={canWrite} onChanged={page.reload} />
          )}
        </aside>
      </div>
    </div>
  );
}

function WordForm({ seq, canWrite, onChanged }: { seq: number; canWrite: boolean; onChanged: () => void }) {
  const meta = useMeta();
  const detail = useAsync<WordDetail>(() => api.word(seq), [seq]);
  const [source, setSource] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  useEffect(() => {
    setErr(null);
    setDone(null);
  }, [source]);

  if (detail.loading && !detail.data) return <p className="muted">يُحمَّل…</p>;
  if (detail.error) return <p className="error">{detail.error.message}</p>;
  if (!detail.data) return null;

  const { word, rulings } = detail.data;
  const existing = rulings.find((r) => r.source === source);

  const save = async (body: RulingPatchBody) => {
    setBusy(true);
    setErr(null);
    setDone(null);
    try {
      if (existing) await api.patchRuling(seq, source, body);
      else await api.createRuling(seq, { ...body, source, raw: body.raw ?? '' });
      setDone(existing ? 'عُدِّل الحكمُ وقُيِّد في السجلّ.' : 'أُدخِل الحكمُ وقُيِّد في السجلّ.');
      detail.reload();
      onChanged();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div>
      <h2 className="quran add-word">{word.text}</h2>
      <p className="muted small">
        {word.sura_name} {arNum(word.sura)}:{arNum(word.ayah)}
      </p>

      <h3>الأحكامُ الموجودة</h3>
      {rulings.length === 0 && <p className="muted small">لا حكمَ لأيِّ مصدرٍ هنا بعد. وليس ذلك نفياً للوقف.</p>}
      <ul className="others">
        {rulings.map((r) => (
          <li key={r.source} style={{ borderInlineStartColor: sourceColor(r.source) }}>
            <span>{sourceShort(r.source)}</span>
            <span className="other-raw">{r.raw}</span>
            <StatusBadge status={r.status} />
            <CategoryBadge category={r.category} approx={r.approx} categories={meta.categories} />
          </li>
        ))}
      </ul>

      <label className="field">
        <span>المصدر الذي تُدخِل منه</span>
        <select value={source} onChange={(e) => setSource(e.target.value)}>
          <option value="">— اختر —</option>
          {meta.sources.map((s) => (
            <option key={s.id} value={s.id}>
              {sourceShort(s.id, s.name)}
              {rulings.some((r) => r.source === s.id) ? ' (له حكمٌ هنا — تعديل)' : ''}
            </option>
          ))}
        </select>
      </label>

      {done && <p className="notice small">{done}</p>}
      {err && <p className="error">{err}</p>}
      {source && (
        <RulingEditor
          key={`${seq}|${source}|${existing ? 'e' : 'n'}`}
          source={source}
          initial={existing ?? EMPTY}
          create={!existing}
          busy={busy || !canWrite}
          onSave={(b) => void save(b)}
        />
      )}
    </div>
  );
}

const EMPTY = {};
