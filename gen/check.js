// يشغّل منطق كل شاشة فعلياً: يستخرج كتلة السكربت ويستدعي renderVals
const fs = require('fs'), path = require('path');
const DIR = '/tmp/claude-0/-home-claude/3d4ae7fd-b04d-5598-b44d-3e07691c2ad4/scratchpad/w/project';
let fail = 0;

// يجمع كل {{holes}} المستعملة في القالب
function holes(html) {
  const body = html.slice(0, html.indexOf('<script type="text/x-dc"'));
  const out = new Set();
  for (const m of body.matchAll(/\{\{\s*([A-Za-z_$][\w$]*)/g)) out.add(m[1]);
  for (const m of body.matchAll(/as="([A-Za-z_$][\w$]*)"/g)) out.delete(m[1]);
  for (const lit of ['true','false','null','undefined','$index']) out.delete(lit);
  return out;
}

for (const f of fs.readdirSync(DIR).filter((x) => x.endsWith('.dc.html'))) {
  const html = fs.readFileSync(path.join(DIR, f), 'utf8');
  const m = html.match(/<script type="text\/x-dc"[^>]*>([\s\S]*?)<\/script>/);
  if (!m) { console.log(`${f.padEnd(24)} لا سكربت`); continue; }
  try {
    const src = m[1] + '\n;return Component;';
    const DCLogic = class { constructor(p){ this.props = p || {}; this.state = {}; }
                            setState(o){ Object.assign(this.state, o); } };
    const C = new Function('DCLogic', src)(DCLogic);
    const inst = new C({});
    const v = inst.renderVals();

    // كل hole في القالب له قيمة
    const missing = [...holes(html)].filter((h) => !(h in v));

    // جرّب كل زرّ/مبدّل: الروايات والمصادر والاختيار
    let acted = 0;
    const fire = (x) => { if (typeof x === 'function') { x(); inst.renderVals(); acted++; } };
    for (const key of ['riwayat', 'sources', 'words', 'rows', 'queue', 'apparatus', 'filters']) {
      for (const it of (Array.isArray(v[key]) ? v[key] : [])) {
        if (it && typeof it === 'object') for (const k of ['pick', 'toggle']) fire(it[k]);
      }
    }
    for (const k of ['toggleAll', 'toggle', 'openSheet', 'closeSheet', 'approve', 'reject', 'skip', 'close', 'closeCard', 'closeCell'])
      fire(v[k]);

    const bad = missing.length;
    if (bad) fail++;
    console.log(`${f.padEnd(24)} ${bad ? '✗ holes بلا قيمة: ' + missing.join(', ') : '✓'}  (تفاعلات: ${acted})`);
  } catch (e) {
    fail++;
    console.log(`${f.padEnd(24)} ✗ ${e.message}`);
  }
}
console.log('\nشاشات معطوبة:', fail);
process.exit(fail ? 1 : 0);
