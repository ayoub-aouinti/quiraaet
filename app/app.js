'use strict';
/* قراءات — مقابلة القراءات. صفحة ثابتة؛ البيانات في data/ وخطوط المجمع في fonts/. */

const PALETTE = ['#d55e00', '#0072b2', '#009e73', '#cc79a7', '#e69f00', '#56b4e9', '#7a3e9d',
  '#b2182b', '#4d9221', '#8c6d31', '#1b7a8c', '#c51b8a', '#6a51a3', '#636363', '#1f9d8b', '#a65628',
  '#377eb8', '#984ea3', '#999999'];
const KIND = { 1: 'ضبط مخالف (حركات أو همزات) — مرشَّح للمراجعة', 2: 'رسم مخالف', 3: 'كلمة لا مقابل لها في قالون' };
const AR = '٠١٢٣٤٥٦٧٨٩';
const arNum = n => String(n).replace(/\d/g, d => AR[d]);
const $ = id => document.getElementById(id);

const S = { meta: null, sura: 1, mode: 'q', riw: 'warsh', sel: new Set(), color: {}, cache: {}, cur: null, tok: 0, returnFocus: null };

function store(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* التخزين قد يكون ممنوعاً */ } }
function load(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }

async function getJSON(path) {
  if (!S.cache[path]) {
    S.cache[path] = fetch(path, { cache: 'no-cache' }).then(r => {
      if (!r.ok) throw new Error(path + ' (' + r.status + ')');
      return r.json();
    }).catch(err => {
      // Une erreur réseau ne doit pas empêcher une nouvelle tentative.
      delete S.cache[path];
      throw err;
    });
  }
  return S.cache[path];
}
function mk(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
function setFont(el, id) { el.style.fontFamily = '"f-' + id + '", serif'; }

/* ---------- الحروف: تقسيم الكلمة إلى حرفٍ وعلاماته، وتلوين بعضها ---------- */
function clusters(text) {
  const out = [];
  for (const m of text.matchAll(/[^\p{M}]\p{M}*|\p{M}+/gu)) out.push([m.index, m[0]]);
  return out;
}
const REV = {};   // لون ← معرّف القارئ، ليُعرَف أيّ قارئٍ لُوِّن حرفُه عند الضغط
function paint(text, marks, exact) {   // marks: Map(index -> color)؛ exact: Map(index -> color) يُلوِّن الحرفَ المعيَّن وحده ولو كان علامةً في عنقود
  if ((!marks || !marks.size) && (!exact || !exact.size)) return document.createTextNode(text);
  const frag = document.createDocumentFragment();
  let run = '';
  const flush = () => { if (run) { frag.appendChild(document.createTextNode(run)); run = ''; } };
  const put = (str, col) => {
    flush();
    const el = mk('i', null, str); el.style.color = col;
    if (REV[col]) el.dataset.r = REV[col];
    frag.appendChild(el);
  };
  for (const [idx, str] of clusters(text)) {
    let col = null;
    if (marks) for (let k = 0; k < str.length; k++) if (marks.has(idx + k)) { col = marks.get(idx + k); break; }
    if (!col && exact && exact.has(idx)) col = exact.get(idx);
    if (col) { put(str, col); continue; }
    const hit = exact ? [...str].map((_, k) => k).filter(k => k > 0 && exact.has(idx + k)) : [];
    if (!hit.length) { run += str; continue; }
    for (let k = 0; k < str.length; k++) {
      if (exact.has(idx + k) && k > 0) put(str[k], exact.get(idx + k)); else run += str[k];
    }
  }
  flush();
  return frag;
}
// في مصحف الرواية الحرفُ المخالف يُبرَز بخطٍّ سفلي
function paintUnderline(text, set) {
  const frag = document.createDocumentFragment(); let run = '';
  const flush = () => { if (run) { frag.appendChild(document.createTextNode(run)); run = ''; } };
  for (const [idx, str] of clusters(text)) {
    let hit = false;
    for (let k = 0; k < str.length; k++) if (set.has(idx + k)) hit = true;
    if (hit) { flush(); const el = mk('i', null, str); el.style.textDecoration = 'underline'; el.style.textDecorationThickness = '.08em'; frag.appendChild(el); }
    else run += str;
  }
  flush();
  return frag;
}

/* ---------- أسماء الرواة ---------- */
function nameOf(id) {
  for (const g of S.meta.groups) for (const r of g.readers) if (r.id === id) {
    const w = g.name.split(' ');    // «ابن كثير» و«أبو عمرو» كلمتان؛ وسائرها كلمة
    return r.name + ' (' + (w[0] === 'ابن' || w[0] === 'أبو' ? w[0] + ' ' + w[1] : w[0]) + ')';
  }
  return id;
}
const riwOf = id => S.meta.riwayat.find(r => r.reader === id);

/* ---------- بناء اللوحة ---------- */
function buildPanel() {
  const g = $('groups'); g.textContent = '';
  let ci = 0;
  for (const grp of S.meta.groups) {
    const box = mk('div', 'grp');
    const h = mk('h3', null, 'قراءة ' + grp.name);
    const b = mk('button', 'lnk', 'الكل');
    b.onclick = () => {
      const rs = grp.readers.filter(r => r.id !== 'qalun');
      const all = rs.every(r => S.sel.has(r.id)); rs.forEach(r => all ? S.sel.delete(r.id) : S.sel.add(r.id)); syncChecks(); changed();
    };
    h.appendChild(b); box.appendChild(h);
    for (const r of grp.readers) {
      if (r.id === 'qalun') { box.appendChild(mk('div', 'rd ref', r.name + ' — المرجع')); continue; }
      S.color[r.id] = PALETTE[ci++ % PALETTE.length]; REV[S.color[r.id]] = r.id;
      const l = mk('label', 'rd');
      const cb = document.createElement('input'); cb.type = 'checkbox'; cb.dataset.id = r.id;
      cb.onchange = () => { cb.checked ? S.sel.add(r.id) : S.sel.delete(r.id); changed(); };
      const chip = mk('span', 'chip'); chip.style.background = S.color[r.id];
      l.append(cb, chip, mk('span', null, r.name)); box.appendChild(l);
    }
    g.appendChild(box);
  }
  const rl = $('riw-list'); rl.textContent = '';
  for (const r of S.meta.riwayat) {
    if (r.reader === 'qalun') continue;
    const l = mk('label', 'rd');
    const rb = document.createElement('input'); rb.type = 'radio'; rb.name = 'riw'; rb.value = r.reader; rb.checked = r.reader === S.riw;
    rb.onchange = () => { S.riw = r.reader; changed(); };
    l.append(rb, mk('span', null, (r.mush ? 'مصحف ' : 'قالون معدَّلًا: ') + r.name));
    rl.appendChild(l);
  }
  syncChecks();
}
function syncChecks() {
  document.querySelectorAll('#groups input').forEach(c => { c.checked = S.sel.has(c.dataset.id); });
  $('stat-selected').textContent = arNum(S.sel.size);
}
function updateStats(qd) {
  const words = qd?.ayat?.reduce((n, [, ws]) => n + ws.length, 0) || 0;
  $('stat-ayah').textContent = qd ? arNum(qd.ayat.length) : '—';
  $('stat-word').textContent = words ? arNum(words) : '—';
  $('stat-selected').textContent = arNum(S.sel.size);
}
function searchKey(value) {
  return value.toLocaleLowerCase().normalize('NFKD').replace(/\p{M}/gu, '').trim();
}
function applySearch() {
  const query = searchKey($('search')?.value || '');
  let count = 0;
  document.querySelectorAll('#text .w').forEach(w => {
    const hit = !!query && searchKey(w.textContent).includes(query);
    w.classList.toggle('search-hit', hit);
    if (hit) count += 1;
  });
  $('search-count').textContent = query ? (count ? arNum(count) + ' نتيجة' : 'لا توجد نتائج') : '';
}
function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  const dark = theme === 'dark';
  $('theme-toggle').textContent = dark ? '☀' : '☾';
  $('theme-toggle').setAttribute('aria-label', dark ? 'تفعيل المظهر الفاتح' : 'تفعيل المظهر الداكن');
}

/* ---------- الحالة في الرابط ---------- */
function writeHash() {
  const p = new URLSearchParams({ s: S.sura, m: S.mode, w: S.riw, r: [...S.sel].join('|') });
  history.replaceState(null, '', '#' + p.toString());
  store('iqraa', p.toString());
}
function readHash() {
  const raw = location.hash.slice(1) || load('iqraa') || '';
  const p = new URLSearchParams(raw);
  S.sel.clear();
  S.mode = 'q';
  S.riw = 'warsh';
  const s = +p.get('s'); if (s >= 1 && s <= 114) S.sura = s;
  S.open = +p.get('o') || 0;   // رقم كلمة قالون لفتح بيانها عند التحميل (للروابط)
  S.ns = p.get('ns') === '1';  // بلا تمرير إلى الكلمة (للفحص الآلي)
  if (p.get('m') === 'r') S.mode = 'r';
  const w = p.get('w');
  if (w && S.meta.riwayat.some(r => r.reader === w && w !== 'qalun')) S.riw = w;
  const known = new Set(S.meta.groups.flatMap(g => g.readers.map(r => r.id)));
  (p.get('r') || '').split('|').filter(x => known.has(x) && x !== 'qalun').forEach(x => S.sel.add(x));
}
function changed() { writeHash(); render(); }

/* ---------- العرض ---------- */
async function render() {
  const token = ++S.tok;
  closeSheet();
  $('reader').setAttribute('aria-busy', 'true');
  document.querySelectorAll('.seg button').forEach(b => b.setAttribute('aria-selected', String((b.id === 'mode-q') === (S.mode === 'q'))));
  $('panel-q').hidden = S.mode !== 'q'; $('panel-r').hidden = S.mode !== 'r';
  $('sura').value = S.sura;
  $('status').textContent = 'جارٍ التحميل…';
  try {
    const n = S.sura;
    const [qd, reads] = await Promise.all([getJSON('data/qalun/' + n + '.json'), getJSON('data/reads/' + n + '.json')]);
    const riw = riwOf(S.riw);
    if (!riw) throw new Error('riwāya inconnue: ' + S.riw);
    let rd = null;
    if (S.mode === 'r' && riw.mush) rd = await getJSON('data/riw/' + riw.mush + '/' + n + '.json');
    if (token !== S.tok) return;
    S.cur = { qd, reads, rd, qtext: new Map(qd.ayat.flatMap(a => a[1])) };
    updateStats(qd);
    // لكل كلمة: العناصر التي تغطّيها والإزاحة داخل العبارة
    const cover = new Map();
    for (const e of reads) {
      let off = 0;
      for (let s = e.s; s <= e.e; s++) {
        if (!cover.has(s)) cover.set(s, []);
        cover.get(s).push({ e, off });
        off += (S.cur.qtext.get(s) || '').length + 1;
      }
    }
    S.cur.cover = cover;
    if (S.mode === 'q') renderQ(); else if (riw.mush) renderR(); else renderX();
    applySearch();
    if (S.open) {
      const w = document.querySelector(S.mode === 'q' ? '.w[data-seq="' + S.open + '"]' : '.w[data-q="' + S.open + '"]');
      S.open = 0;
      if (w) { S.mode === 'q' ? onWordQ(w, { target: w }) : onWordR(w); if (!S.ns) w.scrollIntoView({ block: 'center' }); }
    }
    $('status').textContent = S.mode === 'q'
      ? 'سورة ' + qd.name + ' — ' + arNum(qd.ayat.length) + ' آية، برواية قالون عن نافع'
      : 'سورة ' + qd.name + ' — ' + (riw.mush ? 'مصحف ' + riw.name : 'مصحف قالون معدَّلًا بحسب خلاف ' + riw.name);
  } catch (e) {
    $('status').textContent = 'تعذَّر التحميل: ' + e.message;
  } finally {
    if (token === S.tok) $('reader').setAttribute('aria-busy', 'false');
  }
}

function basmala(id) {
  const r = S.meta.riwayat.find(x => x.id === id);
  if (S.sura === 1 || S.sura === 9 || !r || !r.bsm) return null;
  const d = mk('div', 'bsm', r.bsm); setFont(d, id);
  return d;
}
function ayahMark(ay, n) { ay.appendChild(mk('span', 'an', arNum(n))); ay.appendChild(document.createTextNode(' ')); }

function renderQ() {
  const { qd, cover } = S.cur;
  const box = $('text'); box.textContent = ''; setFont(box, 'qalun');
  const b = basmala('qalun'); if (b) box.appendChild(b);
  for (const [ayNo, words] of qd.ayat) {
    const ay = mk('span', 'ay');
    for (const [seq, text] of words) {
      const w = mk('span', 'w'); w.tabIndex = 0; w.dataset.seq = seq;
      const marks = new Map(), exact = new Map(); const cols = [];
      for (const { e, off } of cover.get(seq) || []) {
        for (const r of e.r) {
          if (!S.sel.has(r.id) || r.same) continue;
          const c = S.color[r.id];
          if (!cols.includes(c)) cols.push(c);
          for (const i of r.dq || []) { const k = i - off; if (k >= 0 && k < text.length && !marks.has(k)) marks.set(k, c); }
          for (const i of r.dqa || []) { const k = i - off; if (k >= 0 && k < text.length) exact.set(k, c); }
        }
      }
      if (cols.length) {
        w.classList.add('diff');
        const stops = cols.map((c, i) => c + ' ' + (i * 100 / cols.length) + '% ' + ((i + 1) * 100 / cols.length) + '%');
        w.style.backgroundImage = 'linear-gradient(to left,' + stops.join(',') + ')';
      }
      w.appendChild(paint(text, marks, exact));
      ay.appendChild(w); ay.appendChild(document.createTextNode(' '));
    }
    ayahMark(ay, ayNo);
    box.appendChild(ay);
  }
}

// مصحف الرواية: نصُّه كما في ملف المجمع، وما يخالف قالون ملوَّن
function renderR() {
  const { rd } = S.cur; const riw = riwOf(S.riw);
  const box = $('text'); box.textContent = ''; setFont(box, riw.mush);
  const b = basmala(riw.id); if (b) box.appendChild(b);
  for (const [ayNo, words] of rd.ayat) {
    const ay = mk('span', 'ay');
    for (const [text, q, k, d] of words) {
      const w = mk('span', 'w' + (k ? ' k' + k : '')); w.tabIndex = 0;
      w.dataset.q = q; w.dataset.k = k; w.dataset.t = text; w.dataset.f = riw.mush;
      w.appendChild(d ? paintUnderline(text, new Set(d)) : document.createTextNode(text));
      ay.appendChild(w); ay.appendChild(document.createTextNode(' '));
    }
    ayahMark(ay, ayNo);
    box.appendChild(ay);
  }
}

// لمن لا مصحف له: مصحف قالون وقد استُبدلت كلمةُ كل موضعِ خلافٍ بكلمة قراءته (≈ حيث قُرِّبت)
function renderX() {
  const { qd, reads } = S.cur; const rid = S.riw; const riw = riwOf(rid);
  const rep = new Map(), skip = new Set(), mark = new Set();
  for (const e of reads) {
    const r = e.r.find(x => x.id === rid);
    if (!r || r.same) continue;
    if (e.s !== e.e && [...Array(e.e - e.s + 1).keys()].some(i => rep.has(e.s + i) || skip.has(e.s + i))) continue;
    if (rep.has(e.s) || mark.has(e.s)) continue;
    if (r.x) {
      rep.set(e.s, { r, e });
      for (let s = e.s + 1; s <= e.e; s++) skip.add(s);
    } else for (let s = e.s; s <= e.e; s++) mark.add(s);
  }
  const box = $('text'); box.textContent = ''; setFont(box, 'qalun');
  const b = basmala('qalun'); if (b) box.appendChild(b);
  for (const [ayNo, words] of qd.ayat) {
    const ay = mk('span', 'ay');
    for (const [seq, text] of words) {
      if (skip.has(seq)) continue;
      const w = mk('span', 'w'); w.tabIndex = 0; w.dataset.q = seq; w.dataset.f = 'qalun';
      const p = rep.get(seq);
      if (p) {
        w.classList.add('k1');
        w.dataset.k = 1; w.dataset.t = p.r.x; w.dataset.f = p.r.f || 'hafs';
        setFont(w, w.dataset.f);
        w.appendChild(p.r.dx ? paintUnderline(p.r.x, new Set(p.r.dx)) : document.createTextNode(p.r.x));
      } else {
        w.dataset.k = mark.has(seq) ? 1 : 0; w.dataset.t = text;
        if (mark.has(seq)) w.classList.add('k1', 'nt');
        w.appendChild(document.createTextNode(text));
      }
      ay.appendChild(w); ay.appendChild(document.createTextNode(' '));
    }
    ayahMark(ay, ayNo);
    box.appendChild(ay);
  }
}

/* ---------- نافذة بيان الخلاف ---------- */
function closeSheet() {
  $('sheet').hidden = true;
  document.querySelectorAll('.w.sel').forEach(x => x.classList.remove('sel'));
  if (S.returnFocus?.isConnected) S.returnFocus.focus();
  S.returnFocus = null;
}
function openSheet(titleText, titleFont, bodyNodes) {
  const t = $('sheet-title'); t.textContent = titleText; setFont(t, titleFont);
  const b = $('sheet-body'); b.textContent = ''; bodyNodes.forEach(n => b.appendChild(n));
  $('sheet').hidden = false;
  S.returnFocus = document.activeElement;
  $('sheet-close').focus();
}

// نصُّ التقييد بحسب الحالة المذكورة في الملاحظة
function condText(r) {
  const n = r.n || '', w = /وقف/.test(n), v = /وصل/.test(n);
  return w && !v ? 'مقيَّد وقفًا' : v && !w ? 'مقيَّد وصلًا' : 'مقيَّد (في بعض الأحوال)';
}

// عنصرُ خلافٍ: رواةٌ بكلماتهم وحروفهم المخالفة، ثم البيان بلفظ المصدر
function entryNode(e, only, hl) {
  const rs = only ? e.r.filter(r => r.id === only) : e.r;
  const box = mk('div', 'ent' + (rs.some(r => S.sel.has(r.id)) ? '' : ' off'));
  const h = mk('h4'); h.append(mk('span', null, e.e > e.s ? 'خلاف في عبارة' : 'خلاف'));
  if (e.t === 'rasm') h.append(mk('span', 'tag warn', '≈ مطابقة بالرسم'));
  else if (e.t === 'm') h.append(mk('span', 'tag', 'فرق في المصحف'));
  else if (e.t === 'u' || e.t === 'w') h.append(mk('span', 'tag', 'أصلٌ عامّ معمَّم على مواضعه'));
  if (e.u) h.append(mk('span', 'tag warn', 'مشكوك فيه'));
  h.append(mk('span', 'tag', 'غير مُتحقَّق'));
  box.appendChild(h);
  if (e.e > e.s) {
    const ph = mk('div', 'same', [...Array(e.e - e.s + 1).keys()].map(i => S.cur.qtext.get(e.s + i)).join(' '));
    setFont(ph, 'qalun'); ph.style.fontSize = '1.4rem'; box.appendChild(ph);
  }
  const rank = r => (r.id === 'qalun' ? 2 : S.sel.has(r.id) ? 1 : 0);
  const order = rs.slice().sort((a, b) => rank(b) - rank(a));
  for (const r of order) {
    const row = mk('div', 'rr' + (hl === r.id ? ' hl' : '') + (S.sel.has(r.id) || r.id === 'qalun' ? '' : ' dim'));
    const nm = mk('span', 'nm'); const chip = mk('span', 'chip'); chip.style.background = S.color[r.id] || 'var(--muted)';
    nm.append(chip, mk('span', null, nameOf(r.id))); row.appendChild(nm);
    if (r.same) row.appendChild(mk('span', 'same', 'كقالون'));
    else if (r.x) {
      const tx = mk('span', 'tx'); setFont(tx, r.f || 'hafs');
      const marks = new Map(); (r.dx || []).forEach(i => marks.set(i, S.color[r.id]));
      const exact = new Map(); (r.dxa || []).forEach(i => exact.set(i, S.color[r.id]));
      tx.appendChild(paint(r.x, marks, exact)); row.appendChild(tx);
      const tags = mk('span', 'tags');
      if (r.n) tags.append(mk('span', 'tag', r.n));
      if (r.cond) tags.append(mk('span', 'tag', condText(r)));
      if (r.khulf) tags.append(mk('span', 'tag', 'بخلافٍ عنه'));
      if (tags.childNodes.length) row.appendChild(tags);
    } else {
      row.appendChild(mk('span', 'same', r.n ? 'يخالف قالون: ' + r.n : 'يخالف قالون (لم يُبيَّن وجهه في المصادر المتاحة)'));
      const tags = mk('span', 'tags');
      if (r.cond) tags.append(mk('span', 'tag', condText(r)));
      if (r.khulf) tags.append(mk('span', 'tag', 'بخلافٍ عنه'));
      if (tags.childNodes.length) row.appendChild(tags);
    }
    box.appendChild(row);
  }
  return box;
}

function onWordQ(span, ev) {
  const seq = +span.dataset.seq;
  const hl = ev.target.dataset && ev.target.dataset.r;
  document.querySelectorAll('.w.sel').forEach(x => x.classList.remove('sel')); span.classList.add('sel');
  const ents = (S.cur.cover.get(seq) || []).map(c => c.e);
  const score = e => e.r.filter(r => S.sel.has(r.id)).length;
  const nodes = ents.slice().sort((a, b) => score(b) - score(a)).map(e => entryNode(e, null, hl));
  if (!nodes.length) nodes.push(mk('p', 'empty', 'لا خلاف مسجَّل لهذه الكلمة في المصادر المتوفرة. وخلوّ الموضع من خلافٍ ليس نفياً له؛ قد يكون نقصاً في المصدر.'));
  openSheet(S.cur.qtext.get(seq), 'qalun', nodes);
}

function onWordR(span) {
  const k = +span.dataset.k, q = +span.dataset.q, text = span.dataset.t, f = span.dataset.f;
  document.querySelectorAll('.w.sel').forEach(x => x.classList.remove('sel')); span.classList.add('sel');
  const riw = riwOf(S.riw);
  const nodes = [];
  const info = mk('div', 'ent');
  info.append(mk('h4', null, k ? KIND[k] || 'يخالف قالون' : 'مطابقة لقالون'));
  if (q && S.cur.qtext.has(q)) {
    const row = mk('div', 'rr'); row.append(mk('span', 'nm', 'قالون'));
    const tx = mk('span', 'tx', S.cur.qtext.get(q)); setFont(tx, 'qalun'); row.appendChild(tx); info.appendChild(row);
  } else if (q) info.appendChild(mk('p', 'same', 'مقابل قالون في سورةٍ أخرى (رقم الكلمة ' + q + ').'));
  info.appendChild(mk('p', 'same', riw.mush
    ? 'هذا فرقُ نصّين بين مصحفين، لا حكمُ قراءة؛ ولا يُنسَب إلى قارئ إلا من البيان أدناه إن وُجد.'
    : 'مصحفُ قالون وقد استُبدلت الكلمةُ بكلمة قراءته من المصدر.'));
  nodes.push(info);
  if (q) for (const { e } of S.cur.cover.get(q) || []) {
    if (e.r.some(r => r.id === S.riw)) nodes.push(entryNode(e, S.riw, S.riw));
  }
  openSheet(text, f || riw.mush || 'qalun', nodes);
}

/* ---------- التهيئة ---------- */
async function init() {
  S.meta = await getJSON('data/meta.json');
  const css = S.meta.fonts.map(r => '@font-face{font-family:"f-' + r.id + '";src:url("fonts/' + r.font + '");font-display:swap}').join('');
  const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  const sel = $('sura');
  S.meta.suras.forEach(s => { const o = document.createElement('option'); o.value = s.n; o.textContent = arNum(s.n) + ' — ' + s.name; sel.appendChild(o); });
  readHash(); buildPanel();
  const fs = parseFloat(load('iqraa-fs')); if (fs) $('text').style.setProperty('--fs', fs + 'rem');
  sel.onchange = () => { S.sura = +sel.value; window.scrollTo(0, 0); changed(); };
  $('mode-q').onclick = () => { S.mode = 'q'; changed(); };
  $('mode-r').onclick = () => { S.mode = 'r'; changed(); };
  $('all-on').onclick = () => { S.meta.groups.forEach(g => g.readers.forEach(r => r.id !== 'qalun' && S.sel.add(r.id))); syncChecks(); changed(); };
  $('all-off').onclick = () => { S.sel.clear(); syncChecks(); changed(); };
  $('sheet-close').onclick = closeSheet;
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeSheet(); });
  $('search').oninput = applySearch;
  const savedTheme = load('iqraa-theme');
  setTheme(savedTheme === 'dark' || savedTheme === 'light' ? savedTheme : (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  $('theme-toggle').onclick = () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    setTheme(next); store('iqraa-theme', next);
  };
  $('text').addEventListener('click', ev => {
    const w = ev.target.closest('.w'); if (!w) return;
    S.mode === 'q' ? onWordQ(w, ev) : onWordR(w);
  });
  $('text').addEventListener('keydown', ev => {
    if (ev.key !== 'Enter' && ev.key !== ' ') return;
    const w = ev.target.closest('.w'); if (!w) return;
    ev.preventDefault();
    S.mode === 'q' ? onWordQ(w, { target: w }) : onWordR(w);
  });
  const bump = d => { const cur = parseFloat(getComputedStyle($('text')).getPropertyValue('--fs')) || 2.1; const v = Math.max(1.2, Math.min(4, cur + d)); $('text').style.setProperty('--fs', v + 'rem'); store('iqraa-fs', v); };
  $('fs+').onclick = () => bump(.2); $('fs-').onclick = () => bump(-.2);
  const L = document.querySelector('.layout');
  $('toggle-panel').onclick = () => { const h = $('panel').hidden = !$('panel').hidden; L.classList.toggle('nopanel', h); $('toggle-panel').setAttribute('aria-expanded', String(!h)); };
  window.addEventListener('hashchange', () => { readHash(); syncChecks(); render(); });
  render();
}
init().catch(e => { $('status').textContent = 'تعذَّر بدء التطبيق: ' + e.message; });
