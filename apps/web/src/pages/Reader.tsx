import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  CATEGORY_NOTE,
  arNum,
  categoryBadge,
  riwayaColor,
  sourceColor,
  sourceShort,
  type AyatPage,
  type ReaderWord,
  type RiwayaText,
} from '@jamei/shared';
import { SourceStateBadge } from '../components/Badges';
import { WordPanel } from '../components/WordPanel';
import { api } from '../lib/api';
import { useMeta } from '../lib/meta';
import { useAsync } from '../lib/useAsync';
import { useStored } from '../lib/useStored';

const NEUTRAL_RULE = '#B9A77E';

export function Reader() {
  const meta = useMeta();
  const nav = useNavigate();
  const { sura: suraParam } = useParams();
  const [sp, setSp] = useSearchParams();
  const sura = Math.min(Math.max(Number(suraParam) || 1, 1), 114);
  const from = Number(sp.get('from')) || 1;
  const focusSeq = Number(sp.get('seq')) || null;

  const [hiddenList, setHiddenList] = useStored<string[]>('reader.hidden', []);
  const [riwaya, setRiwaya] = useStored<string>('reader.riwaya', 'hafs');
  const [colorBy, setColorBy] = useStored<string>('reader.colorBy', '');
  const [selected, setSelected] = useState<number | null>(focusSeq);
  const hidden = useMemo(() => new Set(hiddenList), [hiddenList]);

  useEffect(() => setSelected(focusSeq), [focusSeq]);

  const page = useAsync(() => api.ayat(sura, from), [sura, from]);
  // ‎?riwaya=‎ في الرابط يُقدَّم على المحفوظ، فيُشارَك الموضعُ بروايته
  const wanted = sp.get('riwaya') || riwaya;
  const riwOk = meta.riwayat.some((r) => r.id === wanted && r.has_text);
  const activeRiwaya = riwOk ? wanted : 'hafs';
  const pickRiwaya = (id: string) => {
    setRiwaya(id);
    if (sp.has('riwaya')) {
      const next = new URLSearchParams(sp);
      next.delete('riwaya');
      setSp(next, { replace: true });
    }
  };
  const riwText = useAsync<RiwayaText | null>(
    () =>
      page.data && activeRiwaya !== 'hafs'
        ? api.riwayaText(activeRiwaya, sura, page.data.from, page.data.to)
        : Promise.resolve(null),
    [page.data, activeRiwaya],
  );

  const suraMeta = meta.suras.find((s) => s.sura === sura);
  const riwMeta = meta.riwayat.find((r) => r.id === activeRiwaya);
  const toggle = (id: string) =>
    setHiddenList(hidden.has(id) ? hiddenList.filter((x) => x !== id) : [...hiddenList, id]);
  const anyHidden = hiddenList.length > 0;

  const go = (s: number, f = 1) => nav(`/read/${s}${f > 1 ? `?from=${f}` : ''}`);

  return (
    <div className={`reader ${selected ? 'with-panel' : ''}`}>
      <aside className="side">
        <label className="field">
          <span>السورة</span>
          <select value={sura} onChange={(e) => go(Number(e.target.value))}>
            {meta.suras.map((s) => (
              <option key={s.sura} value={s.sura}>
                {arNum(s.sura)}. {s.name}
              </option>
            ))}
          </select>
        </label>

        <h2 className="side-title">الرواية</h2>
        <div className="riw-picker" role="radiogroup" aria-label="الرواية">
          {meta.riwayat.map((r) => (
            <button
              key={r.id}
              type="button"
              role="radio"
              aria-checked={activeRiwaya === r.id}
              disabled={!r.has_text}
              onClick={() => pickRiwaya(r.id)}
              style={{ borderInlineStartColor: riwayaColor[r.id] ?? '#5A6B5D' }}
            >
              <span>{r.name}</span>
              <span className="muted small">{r.has_text ? `${r.region ?? ''} — ${r.script ?? ''}` : 'ينتظر استيرادَ النصّ'}</span>
            </button>
          ))}
        </div>

        <div className="side-row">
          <h2 className="side-title">المصادر</h2>
          <button type="button" className="link-btn" onClick={() => setHiddenList(anyHidden ? [] : meta.sources.map((s) => s.id))}>
            {anyHidden ? 'أظهر الكلّ' : 'أخفِ الكلّ'}
          </button>
        </div>
        <ul className="src-toggles">
          {meta.sources.map((s) => {
            const on = !hidden.has(s.id);
            return (
              <li key={s.id}>
                <button type="button" aria-pressed={on} onClick={() => toggle(s.id)}>
                  <span
                    className="swatch"
                    style={{ borderColor: sourceColor(s.id), background: on ? sourceColor(s.id) : 'transparent' }}
                  />
                  <span className="src-text">
                    <span className={on ? '' : 'muted'}>{sourceShort(s.id, s.name)}</span>
                    <span className="muted small">{s.name}</span>
                  </span>
                  <span className="src-end">
                    <span className="muted small">{arNum(s.counts.total)}</span>
                    <SourceStateBadge state={s.state} />
                  </span>
                </button>
              </li>
            );
          })}
        </ul>

        <label className="field">
          <span>لوِّن الخطَّ بفئة</span>
          <select value={colorBy} onChange={(e) => setColorBy(e.target.value)}>
            <option value="">لا مصدر (لونٌ محايد)</option>
            {meta.sources.map((s) => (
              <option key={s.id} value={s.id}>
                {sourceShort(s.id, s.name)}
              </option>
            ))}
          </select>
        </label>

        <h2 className="side-title">الفئات</h2>
        <ul className="legend">
          {meta.categoryList.map((c) => (
            <li key={c.id}>
              <span className="cat-chip" style={{ background: c.color }}>
                {c.symbol}
              </span>
              {c.label}
            </li>
          ))}
          <li>
            <span className="cat-chip" style={{ background: '#5A6B5D' }}>
              ≈
            </span>
            مقابلةٌ تقريبية لمصطلح المصدر
          </li>
        </ul>
        <p className="muted small note">{CATEGORY_NOTE}</p>
      </aside>

      <main className="page-col">
        <div className="page-head">
          <h1>سورة {suraMeta?.name}</h1>
          <p className="muted small">
            {arNum(suraMeta?.ayat)} آية
            {page.data && (
              <>
                {' '}
                · الآيات {arNum(page.data.from)}–{arNum(page.data.to)}
              </>
            )}
          </p>
        </div>

        <div className="mushaf-frame">
          <div className="mushaf-inner">
            <div className="mushaf-title">
              <span />
              <b>{riwMeta?.name ?? 'حفص عن عاصم'}</b>
              <span />
            </div>
            {page.loading && !page.data && <p className="muted">يُحمَّل…</p>}
            {page.error && <p className="error">{page.error.message}</p>}
            {page.data && (
              <p className={`mushaf-text riw-${activeRiwaya}`} style={{ ['--riw' as string]: riwayaColor[activeRiwaya] }}>
                {activeRiwaya === 'hafs' ? (
                  <HafsText
                    page={page.data}
                    hidden={hidden}
                    colorBy={colorBy}
                    selected={selected}
                    onPick={(s) => setSelected(selected === s ? null : s)}
                  />
                ) : riwText.data ? (
                  <RiwayaWords
                    page={page.data}
                    text={riwText.data}
                    hidden={hidden}
                    colorBy={colorBy}
                    selected={selected}
                    onPick={(s) => setSelected(selected === s ? null : s)}
                  />
                ) : (
                  <span className="muted">يُحمَّل نصُّ الرواية…</span>
                )}
              </p>
            )}
            {activeRiwaya !== 'hafs' && (
              <p className="muted small mushaf-foot">
                أرقامُ الآي هنا على عدِّ حفص، لأنّه فهرسُ المحاذاة. وأحكامُ المصادر محاذاةٌ على حفص إلا علاماتِ مصحف الرواية نفسِه.
              </p>
            )}
          </div>
        </div>

        <PageNav page={page.data} sura={sura} go={go} />
      </main>

      {selected != null && <WordPanel seq={selected} hidden={hidden} onClose={() => setSelected(null)} />}
    </div>
  );

  function PageNav({ page: p, sura: s, go: g }: { page?: AyatPage; sura: number; go: (s: number, f?: number) => void }) {
    if (!p) return null;
    return (
      <nav className="page-nav" aria-label="التنقّل">
        {p.prev ? (
          <button type="button" onClick={() => g(s, p.prev!.from)}>
            السابقة
          </button>
        ) : s > 1 ? (
          <button type="button" onClick={() => g(s - 1)}>
            السورة السابقة
          </button>
        ) : (
          <span />
        )}
        <Link to="/suras" className="muted small">
          فهرس السور
        </Link>
        {p.next ? (
          <button type="button" onClick={() => g(s, p.next!.from)}>
            التالية
          </button>
        ) : s < 114 ? (
          <button type="button" onClick={() => g(s + 1)}>
            السورة التالية
          </button>
        ) : (
          <span />
        )}
      </nav>
    );
  }
}

interface WordProps {
  hidden: Set<string>;
  colorBy: string;
  selected: number | null;
  onPick: (seq: number) => void;
}

function MarkedWord({ text, word, hidden, colorBy, selected, onPick }: WordProps & { text: string; word?: ReaderWord }) {
  const meta = useMeta();
  const active = word ? word.rulings.filter((r) => !hidden.has(r.source)) : [];
  if (!word || active.length === 0) return <span className="w">{text} </span>;
  const pick = active.find((r) => r.source === colorBy);
  const rule = pick ? categoryBadge(pick, meta.categories).color : NEUTRAL_RULE;
  const isSel = selected === word.seq;
  const aria = active.map((r) => `${sourceShort(r.source)}: ${r.raw}`).join('، ');
  return (
    <>
      <button
        type="button"
        className={`w marked ${isSel ? 'sel' : ''}`}
        style={{ borderBottomColor: rule }}
        onClick={() => onPick(word.seq)}
        aria-label={`${text} — ${aria}`}
        aria-pressed={isSel}
      >
        {text}
        <span className="dots" aria-hidden="true">
          {active.map((r) => (
            <span key={r.source} style={{ background: sourceColor(r.source) }} />
          ))}
        </span>
      </button>{' '}
    </>
  );
}

function AyahNo({ n }: { n: number }) {
  return <span className="ayah-no">﴿{arNum(n)}﴾ </span>;
}

function HafsText({ page, ...rest }: WordProps & { page: AyatPage }) {
  return (
    <>
      {page.ayat.map((a) => (
        <span key={a.ayah}>
          {a.words.map((w) => (
            <MarkedWord key={w.seq} text={w.text} word={w} {...rest} />
          ))}
          <AyahNo n={a.ayah} />
        </span>
      ))}
    </>
  );
}

/**
 * نصُّ الرواية بكلماته هو، وأحكامُ كلِّ كلمةٍ من مقابِلها في حفص. والكلمةُ
 * التي لم تُحاذَ تُعرَض بلا حكم — وليس ذلك نفياً للحكم.
 */
function RiwayaWords({ page, text, ...rest }: WordProps & { page: AyatPage; text: RiwayaText }) {
  const bySeq = useMemo(() => {
    const m = new Map<number, ReaderWord>();
    for (const a of page.ayat) for (const w of a.words) m.set(w.seq, w);
    return m;
  }, [page]);
  let ayah = page.from;
  const ayahOf = text.words.map((w) => {
    const h = w.hafs_seq != null ? bySeq.get(w.hafs_seq) : undefined;
    if (h) ayah = h.ayah;
    return ayah;
  });
  return (
    <>
      {text.words.map((w, i) => {
        const h = w.hafs_seq != null ? bySeq.get(w.hafs_seq) : undefined;
        const end = i === text.words.length - 1 || ayahOf[i + 1] !== ayahOf[i];
        return (
          <span key={w.pos}>
            <MarkedWord text={w.text} word={h} {...rest} />
            {end && <AyahNo n={ayahOf[i]} />}
          </span>
        );
      })}
    </>
  );
}
