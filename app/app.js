'use strict';
/* اقرأ — قالون ومقابلة القراءات. صفحة ثابتة؛ البيانات في data/ وخطوط المجمع في fonts/. */

const PALETTE = ['#d55e00', '#0072b2', '#009e73', '#cc79a7', '#e69f00', '#56b4e9', '#7a3e9d',
  '#b2182b', '#4d9221', '#8c6d31', '#1b7a8c', '#c51b8a', '#6a51a3', '#636363'];
// مصحف الرواية ← القارئ المقابل له في ملفات الخلاف (لعرض بيانه عند الضغط)
const RIW_READER = { shuba: 'asim:شعبة', hafs: 'asim:حفص', duri: 'abu_amr:الدوري', susi: 'abu_amr:السوسي' };
const KIND = { 1: 'ضبط مخالف (حركات أو همزات) — مرشَّح للمراجعة', 2: 'رسم مخالف', 3: 'كلمة لا مقابل لها في قالون' };
const AR = '٠١٢٣٤٥٦٧٨٩';
const arNum = n => String(n).replace(/\d/g, d => AR[d]);
const $ = id => document.getElementById(id);

const S = { meta: null, sura: 1, mode: 'q', riw: 'warsh', sel: new Set(), color: {}, fs: 0, cache: {}, cur: null };

function store(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* التخزين قد يكون ممنوعاً */ } }
function load(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }

async function getJSON(path) {
  if (!S.cache[path]) {
    S.cache[path] = fetch(path).then(r => { if (!r.ok) throw new Error(path + ' ' + r.status); return r.json(); });
  }
  return S.cache[path];
}

/* ---------- الحروف: تقسيم الكلمة إلى حرفٍ وعلاماته، وتلوين بعضها ---------- */
function clusters(text) {
  const out = []; let i = 0;
  for (const m of text.matchAll(/[^\p{M}]\p{M}*|\p{M}+/gu)) { out.push([m.index, m[0]]); i++; }
  return out;
}
const REV = {};   // لون ← معرّف القارئ، ليُعرَف أيّ قارئٍ لُوِّن حرفُه عند الضغط
function paint(text, marks) {          // marks: Map(index -> color)
  if (!marks || !marks.size) return document.createTextNode(text);
  const frag = document.createDocumentFragment();
  let run = '';
  const flush = () => { if (run) { frag.appendChild(document.createTextNode(run)); run = ''; } };
  for (const [idx, str] of clusters(text)) {
    let col = null;
    for (let k = 0; k < str.length; k++) if (marks.has(idx + k)) { col = marks.get(idx + k); break; }
    if (col) {
      flush();
      const el = document.createElement('i'); el.textContent = str; el.style.color = col;
      if (REV[col]) el.dataset.r = REV[col];
      frag.appendChild(el);
    } else run += str;
  }
  flush();
  return frag;
}

/* ---------- بناء اللوحة ---------- */
function buildPanel() {
  const g = $('groups'); g.textContent = '';
  let ci = 0;
  for (const grp of S.meta.groups) {
    const box = document.createElement('div'); box.className = 'grp';
    const h = document.createElement('h3'); h.textContent = 'قراءة ' + grp.name;
    const b = document.createElement('button'); b.className = 'lnk'; b.textContent = 'الكل';
    b.onclick = () => { const all = grp.readers.every(r => S.sel.has(r.id)); grp.readers.forEach(r => all ? S.sel.delete(r.id) : S.sel.add(r.id)); syncChecks(); changed(); };
    h.appendChild(b); box.appendChild(h);
    for (const r of grp.readers) {
      S.color[r.id] = PALETTE[ci++ % PALETTE.length]; REV[S.color[r.id]] = r.id;
      const l = document.createElement('label'); l.className = 'rd';
      const cb = document.createElement('input'); cb.type = 'checkbox'; cb.dataset.id = r.id;
      cb.onchange = () => { cb.checked ? S.sel.add(r.id) : S.sel.delete(r.id); changed(); };
      const chip = document.createElement('span'); chip.className = 'chip'; chip.style.background = S.color[r.id];
      const t = document.createElement('span'); t.textContent = r.name;
      l.append(cb, chip, t); box.appendChild(l);
    }
    g.appendChild(box);
  }
  const rl = $('riw-list'); rl.textContent = '';
  for (const r of S.meta.riwayat) {
    if (r.ref) continue;
    const l = document.createElement('label'); l.className = 'rd';
    const rb = document.createElement('input'); rb.type = 'radio'; rb.name = 'riw'; rb.value = r.id; rb.checked = r.id === S.riw;
    rb.onchange = () => { S.riw = r.id; changed(); };
    const t = document.createElement('span'); t.textContent = 'مصحف ' + r.name;
    l.append(rb, t); rl.appendChild(l);
  }
  syncChecks();
}
function syncChecks() { document.querySelectorAll('#groups input').forEach(c => { c.checked = S.sel.has(c.dataset.id); }); }

/* ---------- الحالة في الرابط ---------- */
function writeHash() {
  const p = new URLSearchParams({ s: S.sura, m: S.mode, w: S.riw, r: [...S.sel].join('|') });
  history.replaceState(null, '', '#' + p.toString());
  store('iqraa', p.toString());
}
function readHash() {
  const raw = location.hash.slice(1) || load('iqraa') || '';
  const p = new URLSearchParams(raw);
  const s = +p.get('s'); if (s >= 1 && s <= 114) S.sura = s;
  S.open = +p.get('o') || 0;   // رقم كلمة قالون لفتح بيانها عند التحميل (للروابط)
  if (p.get('m') === 'r') S.mode = 'r';
  if (p.get('w') && S.meta.riwayat.some(r => r.id === p.get('w') && !r.ref)) S.riw = p.get('w');
  const known = new Set(S.meta.groups.flatMap(g => g.readers.map(r => r.id)));
  (p.get('r') || '').split('|').filter(x => known.has(x)).forEach(x => S.sel.add(x));
}

function changed() { writeHash(); render(); }

/* ---------- العرض ---------- */
async function render() {
  const token = ++S.tok;
  closeSheet();
  document.querySelectorAll('.seg button').forEach(b => b.setAttribute('aria-selected', String((b.id === 'mode-q') === (S.mode === 'q'))));
  $('panel-q').hidden = S.mode !== 'q'; $('panel-r').hidden = S.mode !== 'r';
  $('sura').value = S.sura;
  $('status').textContent = 'جارٍ التحميل…';
  try {
    const n = S.sura;
    const [qd, kh] = await Promise.all([getJSON('data/qalun/' + n + '.json'), getJSON('data/khilaf/' + n + '.json')]);
    let rd = null;
    if (S.mode === 'r') rd = await getJSON('data/riw/' + S.riw + '/' + n + '.json');
    if (token !== S.tok) return;
    S.cur = { qd, kh, rd, qtext: new Map(qd.ayat.flatMap(a => a[1])) };
    if (S.mode === 'q') renderQ(); else renderR();
    if (S.open) {
      const w = S.mode === 'q' ? document.querySelector('.w[data-seq="' + S.open + '"]') : document.querySelector('.w[data-q="' + S.open + '"]');
      S.open = 0;
      if (w) { S.mode === 'q' ? onWordQ(w, { target: w }) : onWordR(w); w.scrollIntoView({ block: 'center' }); }
    }
    $('status').textContent = S.mode === 'q'
      ? 'سورة ' + qd.name + ' — ' + arNum(qd.ayat.length) + ' آية، برواية قالون عن نافع'
      : 'سورة ' + qd.name + ' — مصحف ' + S.meta.riwayat.find(r => r.id === S.riw).name;
  } catch (e) {
    $('status').textContent = 'تعذَّر التحميل: ' + e.message;
  }
}

function setFont(el, id) { el.style.fontFamily = '"f-' + id + '", serif'; }

function basmala(rid) {
  const r = S.meta.riwayat.find(x => x.id === rid);
  if (S.sura === 1 || S.sura === 9 || !r || !r.bsm) return null;
  const d = document.createElement('div'); d.className = 'bsm'; d.textContent = r.bsm; setFont(d, rid);
  return d;
}

function renderQ() {
  const { qd, kh } = S.cur;
  const box = $('text'); box.textContent = ''; setFont(box, 'qalun');
  const b = basmala('qalun'); if (b) box.appendChild(b);
  // لكل كلمة: الإدخالات التي تغطّيها والإزاحة داخل العبارة
  const cover = new Map();
  for (const e of kh) {
    let off = 0;
    for (let s = e.s; s <= e.e; s++) {
      const t = S.cur.qtext.get(s) || '';
      if (!cover.has(s)) cover.set(s, []);
      cover.get(s).push({ e, off });
      off += t.length + 1;
    }
  }
  S.cur.cover = cover;
  for (const [ayNo, words] of qd.ayat) {
    const ay = document.createElement('span'); ay.className = 'ay';
    for (const [seq, text] of words) {
      const w = document.createElement('span'); w.className = 'w'; w.dataset.seq = seq;
      const marks = new Map(); const cols = [];
      for (const { e, off } of cover.get(seq) || []) {
        for (const r of e.r) {
          if (!S.sel.has(r.id) || r.same) continue;
          const c = S.color[r.id];
          if (!cols.includes(c)) cols.push(c);
          for (const i of r.dq) { const k = i - off; if (k >= 0 && k < text.length && !marks.has(k)) marks.set(k, c); }
        }
      }
      if (cols.length) {
        w.classList.add('diff');
        const stops = cols.map((c, i) => c + ' ' + (i * 100 / cols.length) + '% ' + ((i + 1) * 100 / cols.length) + '%');
        w.style.backgroundImage = 'linear-gradient(to left,' + stops.join(',') + ')';
      }
      w.appendChild(paint(text, marks));
      ay.appendChild(w); ay.appendChild(document.createTextNode(' '));
    }
    const an = document.createElement('span'); an.className = 'an'; an.textContent = arNum(ayNo);
    ay.appendChild(an); ay.appendChild(document.createTextNode(' '));
    box.appendChild(ay);
  }
}

function renderR() {
  const { rd } = S.cur;
  const box = $('text'); box.textContent = ''; setFont(box, S.riw);
  const b = basmala(S.riw); if (b) box.appendChild(b);
  for (const [ayNo, words] of rd.ayat) {
    const ay = document.createElement('span'); ay.className = 'ay';
    for (const wd of words) {
      const [text, q, k, d] = wd;
      const w = document.createElement('span'); w.className = 'w' + (k ? ' k' + k : '');
      w.dataset.q = q; w.dataset.k = k; w.dataset.t = text;
      const marks = new Map();
      if (d) d.forEach(i => marks.set(i, 'currentColor'));
      w.appendChild(d ? paintUnderline(text, new Set(d)) : document.createTextNode(text));
      ay.appendChild(w); ay.appendChild(document.createTextNode(' '));
    }
    const an = document.createElement('span'); an.className = 'an'; an.textContent = arNum(ayNo);
    ay.appendChild(an); ay.appendChild(document.createTextNode(' '));
    box.appendChild(ay);
  }
}
// في مصحف الرواية الكلمةُ كلُّها ملوَّنة بلون فرقها، والحرف المخالف يُبرَز بتغميقٍ وخط سفلي
function paintUnderline(text, set) {
  const frag = document.createDocumentFragment(); let run = '';
  const flush = () => { if (run) { frag.appendChild(document.createTextNode(run)); run = ''; } };
  for (const [idx, str] of clusters(text)) {
    let hit = false;
    for (let k = 0; k < str.length; k++) if (set.has(idx + k)) hit = true;
    if (hit) { flush(); const el = document.createElement('i'); el.textContent = str; el.style.textDecoration = 'underline'; el.style.textDecorationThickness = '.08em'; frag.appendChild(el); }
    else run += str;
  }
  flush();
  return frag;
}

/* ---------- نافذة بيان الخلاف ---------- */
function closeSheet() { $('sheet').hidden = true; document.querySelectorAll('.w.sel').forEach(x => x.classList.remove('sel')); }
function openSheet(titleText, titleFont, bodyNodes) {
  const t = $('sheet-title'); t.textContent = titleText; setFont(t, titleFont);
  const b = $('sheet-body'); b.textContent = ''; bodyNodes.forEach(n => b.appendChild(n));
  $('sheet').hidden = false;
}
function mk(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }

function entryNode(e, off, text, hl) {
  const box = mk('div', 'ent' + (e.r.some(r => S.sel.has(r.id)) ? '' : ' off'));
  const h = mk('h4'); h.append(mk('span', null, 'قراءة ' + (S.meta.groups.find(g => g.id === e.g) || {}).name));
  if (e.t === 'shifted') h.append(mk('span', 'tag warn', '≈ رُبط بآية مجاورة (اختلاف العدّ)'));
  else if (e.t === 'rasm') h.append(mk('span', 'tag warn', '≈ مطابقة بالرسم'));
  h.append(mk('span', 'tag', 'غير مُتحقَّق'));
  box.appendChild(h);
  if (e.e > e.s) {
    const ph = mk('div', 'same', 'العبارة: ' + [...Array(e.e - e.s + 1).keys()].map(i => S.cur.qtext.get(e.s + i)).join(' '));
    setFont(ph, 'qalun'); ph.style.fontSize = '1.4rem'; box.appendChild(ph);
  }
  for (const r of e.r) {
    const row = mk('div', 'rr' + (hl === r.id ? ' hl' : ''));
    const nm = mk('span', 'nm'); const chip = mk('span', 'chip'); chip.style.background = S.color[r.id];
    nm.append(chip, mk('span', null, r.n)); row.appendChild(nm);
    if (r.same) row.appendChild(mk('span', 'same', 'كقالون'));
    else {
      const tx = mk('span', 'tx'); setFont(tx, 'hafs');
      const marks = new Map(); r.dx.forEach(i => marks.set(i, S.color[r.id]));
      tx.appendChild(paint(r.x, marks)); row.appendChild(tx);
    }
    box.appendChild(row);
  }
  const bay = mk('div', 'bayan'); bay.append(mk('b', null, 'بيان القراءة (بلفظ الملف)'), document.createTextNode(e.b));
  box.appendChild(bay);
  return box;
}

function onWordQ(span, ev) {
  const seq = +span.dataset.seq;
  const hl = ev.target.dataset && ev.target.dataset.r;
  document.querySelectorAll('.w.sel').forEach(x => x.classList.remove('sel')); span.classList.add('sel');
  const ents = (S.cur.cover.get(seq) || []);
  const text = S.cur.qtext.get(seq);
  const sorted = ents.slice().sort((a, b) => b.e.r.filter(r => S.sel.has(r.id)).length - a.e.r.filter(r => S.sel.has(r.id)).length);
  const nodes = sorted.map(({ e, off }) => entryNode(e, off, text, hl));
  if (!nodes.length) nodes.push(mk('p', 'empty', 'لا خلاف مسجَّل لهذه الكلمة في ملفات الخلاف المتوفرة. وخلوّ الموضع من خلافٍ ليس نفياً له؛ قد يكون نقصاً في المصدر.'));
  openSheet(text, 'qalun', nodes);
}

function onWordR(span) {
  const k = +span.dataset.k, q = +span.dataset.q, text = span.dataset.t;
  document.querySelectorAll('.w.sel').forEach(x => x.classList.remove('sel')); span.classList.add('sel');
  const nodes = [];
  const info = mk('div', 'ent');
  info.append(mk('h4', null, k ? KIND[k] : 'مطابقة لقالون'));
  if (q && S.cur.qtext.has(q)) {
    const row = mk('div', 'rr'); row.append(mk('span', 'nm', 'قالون'));
    const tx = mk('span', 'tx', S.cur.qtext.get(q)); setFont(tx, 'qalun'); row.appendChild(tx); info.appendChild(row);
  } else if (q) info.appendChild(mk('p', 'same', 'مقابل قالون في سورةٍ أخرى (رقم الكلمة ' + q + ').'));
  info.appendChild(mk('p', 'same', 'هذا فرقُ نصّين بين مصحفين، لا حكمُ قراءة؛ ولا يُنسَب إلى قارئ إلا من بيان الخلاف أدناه إن وُجد.'));
  nodes.push(info);
  const rid = RIW_READER[S.riw];
  if (rid && q) {
    for (const { e, off } of (S.cur.cover || coverFor()).get(q) || []) {
      if (e.r.some(r => r.id === rid)) nodes.push(entryNode({ ...e, r: e.r.filter(r => r.id === rid) }, off, text, rid));
    }
  }
  openSheet(text, S.riw, nodes);
}
function coverFor() {
  const cover = new Map();
  for (const e of S.cur.kh) for (let s = e.s, off = 0; s <= e.e; s++) {
    if (!cover.has(s)) cover.set(s, []);
    cover.get(s).push({ e, off }); off += (S.cur.qtext.get(s) || '').length + 1;
  }
  S.cur.cover = cover; return cover;
}

/* ---------- التهيئة ---------- */
async function init() {
  S.tok = 0;
  S.meta = await getJSON('data/meta.json');
  const css = S.meta.riwayat.map(r => '@font-face{font-family:"f-' + r.id + '";src:url("fonts/' + r.font + '");font-display:swap}').join('');
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  const sel = $('sura');
  S.meta.suras.forEach(s => { const o = document.createElement('option'); o.value = s.n; o.textContent = arNum(s.n) + ' — ' + s.name; sel.appendChild(o); });
  readHash(); buildPanel();
  const fs = parseFloat(load('iqraa-fs')); if (fs) $('text').style.setProperty('--fs', fs + 'rem');
  sel.onchange = () => { S.sura = +sel.value; window.scrollTo(0, 0); changed(); };
  $('mode-q').onclick = () => { S.mode = 'q'; changed(); };
  $('mode-r').onclick = () => { S.mode = 'r'; changed(); };
  $('all-on').onclick = () => { S.meta.groups.forEach(g => g.readers.forEach(r => S.sel.add(r.id))); syncChecks(); changed(); };
  $('all-off').onclick = () => { S.sel.clear(); syncChecks(); changed(); };
  $('sheet-close').onclick = closeSheet;
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSheet(); });
  $('text').addEventListener('click', ev => {
    const w = ev.target.closest('.w'); if (!w) return;
    S.mode === 'q' ? onWordQ(w, ev) : onWordR(w);
  });
  const bump = d => { const cur = parseFloat(getComputedStyle($('text')).getPropertyValue('--fs')) || 2.1; const v = Math.max(1.2, Math.min(4, cur + d)); $('text').style.setProperty('--fs', v + 'rem'); store('iqraa-fs', v); };
  $('fs+').onclick = () => bump(.2); $('fs-').onclick = () => bump(-.2);
  const L = document.querySelector('.layout');
  $('toggle-panel').onclick = () => { const h = $('panel').hidden = !$('panel').hidden; L.classList.toggle('nopanel', h); $('toggle-panel').setAttribute('aria-expanded', String(!h)); };
  render();
}
init().catch(e => { $('status').textContent = 'تعذَّر بدء التطبيق: ' + e.message; });
