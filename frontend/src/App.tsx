import { useEffect, useMemo, useRef, useState } from 'react';
import { fetchMeta, fetchMushaf, fetchQalun, fetchReads } from './api';
import { load, store, useHashState } from './hashState';
import { arNum, fontStyle, searchKey } from './paint';
import Sheet from './Sheet';
import type { Meta, MushafSura, QalunSura, ReadEntry, ViewState } from './types';
import {
  assignColors, buildCover, buildQ, buildR, buildX, riwOf,
  type AyahVM, type Cover, type Target, type WordVM,
} from './view';

interface Cur {
  mode: ViewState['mode']; riw: string; qd: QalunSura; reads: ReadEntry[]; rd: MushafSura | null;
  qtext: Map<number, string>; cover: Cover;
}
interface SheetState { target: Target; key: string; hl?: string }

export default function App() {
  const [meta, setMeta] = useState<Meta | null>(null);
  const [err, setErr] = useState('');
  useEffect(() => { fetchMeta().then(setMeta).catch(e => setErr('تعذَّر بدء التطبيق: ' + e.message)); }, []);
  if (err) return <div className="status">{err}</div>;
  if (!meta) return <div className="status">جارٍ التحميل…</div>;
  return <Main meta={meta} />;
}

function Main({ meta }: { meta: Meta }) {
  const { state, update, open, clearOpen, noScroll } = useHashState(meta);
  const { sura, mode, riw: riwId, sel } = state;
  const colors = useMemo(() => assignColors(meta.groups), [meta]);
  const fontCss = useMemo(() => meta.fonts.map(f =>
    `@font-face{font-family:"f-${f.id}";src:url("/fonts/${f.font}");font-display:swap}`).join(''), [meta]);

  const [cur, setCur] = useState<Cur | null>(null);
  const [status, setStatus] = useState('جارٍ التحميل…');
  const [busy, setBusy] = useState(true);
  const [sheet, setSheet] = useState<SheetState | null>(null);
  const [query, setQuery] = useState('');
  const [panelOpen, setPanelOpen] = useState(true);
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    const saved = load('iqraa-theme');
    return saved === 'dark' || saved === 'light' ? saved : matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });
  const [fs, setFs] = useState<number | null>(() => parseFloat(load('iqraa-fs') || '') || null);
  const textRef = useRef<HTMLDivElement>(null);

  useEffect(() => { document.documentElement.dataset.theme = theme; }, [theme]);
  useEffect(() => { setSheet(null); }, [state]);   // أي تغيير في الحالة يُغلق النافذة

  /* ---------- تحميل بيانات السورة ---------- */
  useEffect(() => {
    let cancelled = false;
    setBusy(true); setStatus('جارٍ التحميل…');
    (async () => {
      try {
        const r = riwOf(meta, riwId);
        if (!r) throw new Error('riwāya inconnue: ' + riwId);
        const [qd, reads, rd] = await Promise.all([
          fetchQalun(sura), fetchReads(sura),
          mode === 'r' && r.mush ? fetchMushaf(r.mush, sura) : Promise.resolve(null),
        ]);
        if (cancelled) return;
        const qtext = new Map(qd.ayat.flatMap(a => a[1]));
        setCur({ mode, riw: riwId, qd, reads, rd, qtext, cover: buildCover(reads, qtext) });
        setStatus(mode === 'q'
          ? `سورة ${qd.name} — ${arNum(qd.ayat.length)} آية، برواية قالون عن نافع`
          : `سورة ${qd.name} — ` + (r.mush ? 'مصحف ' + r.name : 'مصحف قالون معدَّلًا بحسب خلاف ' + r.name));
      } catch (e) {
        if (!cancelled) setStatus('تعذَّر التحميل: ' + (e as Error).message);
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => { cancelled = true; };
  }, [meta, sura, mode, riwId]);

  /* ---------- نموذج العرض (بحسب ما حُمِّل لا بحسب الحالة الحالية) ---------- */
  const curRiw = cur ? riwOf(meta, cur.riw)! : null;
  const ayat: AyahVM[] = useMemo(() => {
    if (!cur || !curRiw) return [];
    if (cur.mode === 'q') return buildQ(cur.qd, cur.cover, sel, colors);
    return curRiw.mush && cur.rd ? buildR(cur.rd, curRiw) : buildX(cur.qd, cur.reads, cur.riw);
  }, [cur, curRiw, sel, colors]);

  const q = searchKey(query);
  const hits = useMemo(() => {
    const s = new Set<string>();
    if (q) for (const a of ayat) for (const w of a.words) if (searchKey(w.plain).includes(q)) s.add(w.key);
    return s;
  }, [ayat, q]);

  /* فتح بيان كلمة من الرابط (o=) */
  useEffect(() => {
    if (!open || !cur) return;
    let found: WordVM | undefined;
    for (const a of ayat) for (const w of a.words) {
      if (found) break;
      if (cur.mode === 'q' ? w.seq === open : w.q === open) found = w;
    }
    clearOpen();
    if (!found) return;
    setSheet({ target: found.target, key: found.key });
    if (!noScroll) setTimeout(() => document.getElementById('w-' + found!.key)?.scrollIntoView({ block: 'center' }));
  }, [open, cur, ayat, clearOpen, noScroll]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setSheet(null); };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, []);

  const openWord = (w: WordVM, hl?: string) => setSheet({ target: w.target, key: w.key, hl });
  const bump = (d: number) => {
    const base = fs ?? (parseFloat(getComputedStyle(textRef.current!).getPropertyValue('--fs')) || 2.1);
    const v = Math.max(1.2, Math.min(4, base + d));
    setFs(v); store('iqraa-fs', String(v));
  };
  const toggleTheme = () => { const n = theme === 'dark' ? 'light' : 'dark'; setTheme(n); store('iqraa-theme', n); };
  const toggleReader = (id: string) => {
    const n = new Set(sel); n.has(id) ? n.delete(id) : n.add(id); update({ sel: n });
  };
  const allReaders = meta.groups.flatMap(g => g.readers).filter(r => r.id !== 'qalun');

  const words = cur ? cur.qd.ayat.reduce((n, [, ws]) => n + ws.length, 0) : 0;
  const bsmRiw = cur ? (cur.mode === 'q' || !curRiw?.mush ? riwOf(meta, 'qalun') : curRiw) : null;
  const bsmId = bsmRiw?.id ?? 'qalun';
  const showBsm = !!cur && sura !== 1 && sura !== 9 && !!bsmRiw?.bsm;
  const boxFont = cur ? (cur.mode === 'q' || !curRiw?.mush ? 'qalun' : curRiw.mush) : 'qalun';

  return (
    <>
      <style>{fontCss}</style>
      <header className="bar">
        <div className="brand">
          <div className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 48 48" role="img" aria-label="شعار قراءات">
              <path className="mark-page" d="M8 13.5c6.5-2.6 11.8-1.7 16 2.2v22.8c-4.2-3.5-9.5-4.3-16-1.6z" />
              <path className="mark-page" d="M40 13.5c-6.5-2.6-11.8-1.7-16 2.2v22.8c4.2-3.5 9.5-4.3 16-1.6z" />
              <path className="mark-line" d="M12.5 19.5c3.8-.8 7.1 0 10 2.2M12.5 25c3.5-.6 6.8.1 10 2.1M35.5 19.5c-3.8-.8-7.1 0-10 2.2M35.5 25c-3.5-.6-6.8.1-10 2.1" />
              <circle className="mark-dot" cx="24" cy="8.5" r="2.3" />
            </svg>
          </div>
          <h1>قراءات <small>مقابلة القراءات القرآنية</small></h1>
        </div>
        <label className="sel"><span className="sr">السورة</span>
          <select id="sura" aria-label="السورة" value={sura}
            onChange={e => { window.scrollTo(0, 0); update({ sura: +e.target.value }); }}>
            {meta.suras.map(s => <option key={s.n} value={s.n}>{arNum(s.n)} — {s.name}</option>)}
          </select>
        </label>
        <div className="seg" role="tablist" aria-label="وجه العرض">
          <button type="button" role="tab" aria-selected={mode === 'q'} onClick={() => update({ mode: 'q' })}>قالون ومقابلة القراءات</button>
          <button type="button" role="tab" aria-selected={mode === 'r'} onClick={() => update({ mode: 'r' })}>مصحف رواية</button>
        </div>
        <div className="sz" aria-label="حجم الخط">
          <button type="button" aria-label="تصغير الخط" onClick={() => bump(-.2)}>أ−</button>
          <button type="button" aria-label="تكبير الخط" onClick={() => bump(.2)}>أ+</button>
        </div>
        <label className="search"><span className="sr">البحث في السورة</span>
          <input type="search" placeholder="ابحث في السورة الحالية…" autoComplete="off"
            value={query} onChange={e => setQuery(e.target.value)} />
        </label>
        <button type="button" className="icon-btn" aria-label={theme === 'dark' ? 'تفعيل المظهر الفاتح' : 'تفعيل المظهر الداكن'}
          onClick={toggleTheme}>{theme === 'dark' ? '☀' : '☾'}</button>
        <button type="button" className="panel-btn" aria-controls="panel" aria-expanded={panelOpen}
          onClick={() => setPanelOpen(o => !o)}>القراءات</button>
      </header>

      <div className={'layout' + (panelOpen ? '' : ' nopanel')}>
        <aside id="panel" className="panel" aria-label="اختيار القراءات" hidden={!panelOpen}>
          <div className="panel-intro">
            <span className="eyebrow">لوحة المقارنة</span>
            <strong>اكتشف مواضع الاختلاف</strong>
            <span className="panel-sub">اختر قارئًا أو أكثر، ثم اضغط على أي كلمة لعرض البيان.</span>
          </div>
          <div className="stats" aria-label="ملخص السورة">
            <div><b>{cur ? arNum(cur.qd.ayat.length) : '—'}</b><span>آية</span></div>
            <div><b>{words ? arNum(words) : '—'}</b><span>كلمة</span></div>
            <div><b>{arNum(sel.size)}</b><span>رواة</span></div>
          </div>
          {mode === 'q' ? (
            <section>
              <p className="hint">اختر الرواة الذين تريد مقابلتهم بقالون؛ تُلوَّن الكلمات والحروف التي يخالفون فيها.</p>
              <div id="groups">
                {meta.groups.map(g => {
                  const rs = g.readers.filter(r => r.id !== 'qalun');
                  return (
                    <div className="grp" key={g.id}>
                      <h3>قراءة {g.name}
                        <button className="lnk" onClick={() => {
                          const n = new Set(sel);
                          const all = rs.every(r => n.has(r.id));
                          rs.forEach(r => all ? n.delete(r.id) : n.add(r.id));
                          update({ sel: n });
                        }}>الكل</button>
                      </h3>
                      {g.readers.map(r => r.id === 'qalun'
                        ? <div className="rd ref" key={r.id}>{r.name} — المرجع</div>
                        : (
                          <label className="rd" key={r.id}>
                            <input type="checkbox" checked={sel.has(r.id)} onChange={() => toggleReader(r.id)} />
                            <span className="chip" style={{ background: colors.color[r.id] }} />
                            <span>{r.name}</span>
                          </label>
                        ))}
                    </div>
                  );
                })}
              </div>
              <div className="row">
                <button type="button" className="lnk" onClick={() => update({ sel: new Set(allReaders.map(r => r.id)) })}>تحديد الكل</button>
                <button type="button" className="lnk" onClick={() => update({ sel: new Set() })}>إلغاء الكل</button>
              </div>
            </section>
          ) : (
            <section>
              <p className="hint">اختر الراوي؛ تُلوَّن في مصحفه الكلمات المخالفة لقالون. ومن لا مصحف له يُعرض مصحفُ قالون وقد استُبدلت كلمةُ كل موضعِ خلافٍ بكلمة قراءته.</p>
              <div id="riw-list">
                {meta.riwayat.filter(r => r.reader !== 'qalun').map(r => (
                  <label className="rd" key={r.id}>
                    <input type="radio" name="riw" value={r.reader} checked={r.reader === riwId}
                      onChange={() => update({ riw: r.reader })} />
                    <span>{(r.mush ? 'مصحف ' : 'قالون معدَّلًا: ') + r.name}</span>
                  </label>
                ))}
              </div>
              <ul className="legend">
                <li><i className="sw k1" /> ضبط مخالف (حركات أو همزات) — مرشَّح للمراجعة</li>
                <li><i className="sw k2" /> رسم مخالف</li>
                <li><i className="sw k3" /> كلمة لا مقابل لها في قالون</li>
              </ul>
            </section>
          )}
          <p className="note">
            النصوص والخطوط: مجمع الملك فهد لطباعة المصحف الشريف.
            بيانات الخلاف أُعدَّت بمعونة نموذج ولم تُراجَع بعدُ على كتب القراءات،
            فهي <b>غير مُتحقَّق منها</b>. العلامة ≈ تعني أن موضع الخلاف رُبط بكلمة قالون
            بتقريب (اختلاف عدّ الآي أو الضبط).
          </p>
          <p className="source-note">المصدر النصي: مجمع الملك فهد لطباعة المصحف الشريف</p>
        </aside>

        <main id="reader" className="reader" aria-live="polite" aria-busy={busy}>
          <div className="reader-head">
            <span className="eyebrow">النص القرآني</span>
            <span className="search-count" aria-live="polite">
              {q ? (hits.size ? arNum(hits.size) + ' نتيجة' : 'لا توجد نتائج') : ''}
            </span>
          </div>
          <div className="status">{status}</div>
          <div id="text" className="text" ref={textRef}
            style={{ ...fontStyle(boxFont), ...(fs ? { ['--fs' as string]: fs + 'rem' } : {}) }}>
            {showBsm && <div className="bsm" style={fontStyle(bsmId)}>{bsmRiw!.bsm}</div>}
            {ayat.map(a => (
              <span className="ay" key={a.no}>
                {a.words.map(w => (
                  <span key={w.key} id={'w-' + w.key}
                    className={w.cls + (hits.has(w.key) ? ' search-hit' : '') + (sheet?.key === w.key ? ' sel' : '')}
                    style={w.style} tabIndex={0}
                    onClick={e => openWord(w, (e.target as HTMLElement).dataset.r)}
                    onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openWord(w); } }}>
                    {w.node}{' '}
                  </span>
                ))}
                <span className="an">{arNum(a.no)}</span>{' '}
              </span>
            ))}
          </div>
        </main>
      </div>

      {sheet && cur && (
        <Sheet key={sheet.key} target={sheet.target} hl={sheet.hl} cover={cur.cover} riw={curRiw!}
          meta={meta} colors={colors} sel={sel} qtext={cur.qtext} onClose={() => setSheet(null)} />
      )}
    </>
  );
}
