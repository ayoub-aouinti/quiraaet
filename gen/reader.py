import sys, json
sys.path.insert(0,'gen')
from tokens import *
ROOT='/tmp/claude-0/-home-claude/3d4ae7fd-b04d-5598-b44d-3e07691c2ad4/scratchpad/w/project/'
PAGE=json.load(open('out/page_sample.json',encoding='utf-8'))['text']

# أحكام حقيقية من القاعدة على مواضع من هذه الصفحة
import sqlite3
con=sqlite3.connect('out/waqf.db'); con.row_factory=sqlite3.Row
rows=con.execute('''SELECT w.seq,w.sura,w.ayah,w.text,r.source,r.symbol,r.term,r.category,r.approx,r.status
  FROM words w JOIN rulings r ON r.seq=w.seq WHERE w.sura=2 AND w.ayah BETWEEN 15 AND 20
  ORDER BY w.seq''').fetchall()
by={}
for r in rows:
    by.setdefault(r['seq'],{'text':r['text'],'sura':r['sura'],'ayah':r['ayah'],'m':{}})
    by[r['seq']]['m'][r['source']]={'s':r['symbol'],'t':r['term'],'c':r['category'],
                                    'a':bool(r['approx']),'st':r['status']}
POS=[{'seq':k,**v} for k,v in sorted(by.items())][:9]

DATA = ('const PAGE_TEXT = '+json.dumps(PAGE,ensure_ascii=False)+';\n'
        'const POS = '+json.dumps(POS,ensure_ascii=False,separators=(',',':'))+';\n'
        'const SRC = '+json.dumps({k:{'n':v[0],'c':v[1],'s':v[2]} for k,v in SRC.items()},ensure_ascii=False)+';\n'
        'const CAT = '+json.dumps({k:{'l':v[0],'k':v[1],'c':v[2]} for k,v in CAT.items()},ensure_ascii=False)+';')

body = f'''
<div dir="rtl" style="width: 1440px; height: 980px; overflow: hidden; background: {LEAF}; color: {INK}; font-family: 'Readex Pro', sans-serif; display: flex; flex-direction: column">

<header style="flex-shrink: 0; display: flex; align-items: center; justify-content: space-between; gap: 28px; padding: 0 28px; height: 62px; background: {PAPER}; border-bottom: 1px solid {RULE}">
<div style="display: flex; align-items: center; gap: 26px">
<a href="Landing.dc.html" style="display: flex; align-items: center; gap: 10px">
{logo_mark(24)}
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 18px; font-weight: 600">جامع الوقوف</span>
</a>
<div style="display: flex; align-items: center; gap: 14px; font-size: 14px; color: {SAGE}">
<span style="color: {INK}; font-weight: 500">سورة البقرة</span>
<span style="width: 1px; height: 14px; background: {RULE}"></span>
<span>الجزء الأول</span>
<span style="width: 1px; height: 14px; background: {RULE}"></span>
<span>صفحة ٥</span>
</div>
</div>
<div style="display: flex; align-items: center; gap: 10px">
<label for="q" style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0)">ابحث في المصحف</label>
<input id="q" type="search" placeholder="ابحث في المصحف" style="width: 230px; height: 38px; padding: 0 13px; border: 1px solid {RULE}; border-radius: 3px; background: {LEAF}; font-family: inherit; font-size: 14px; color: {INK}">
<button type="button" onClick="{{{{toggleAll}}}}" style="height: 38px; padding: 0 15px; border: 1px solid {RULE}; border-radius: 3px; background: {LEAF}; font-family: inherit; font-size: 14px; color: {INK}; cursor: pointer">{{{{allLabel}}}}</button>
</div>
</header>

<div style="flex: 1; min-height: 0; display: grid; grid-template-columns: 330px minmax(0, 1fr)">

<aside style="border-inline-end: 1px solid {RULE}; background: {PAPER}; overflow-y: auto; padding: 20px 22px">
<h2 style="margin: 0 0 4px; font-family: 'Reem Kufi', sans-serif; font-size: 17px; font-weight: 500">المصادر</h2>
<p style="margin: 0 0 16px; font-size: 12.5px; line-height: 1.75; color: {SAGE}">اختر ما يظهر على الصفحة</p>
<sc-for list="{{{{sources}}}}" as="s" hint-placeholder-count="6">
<button type="button" onClick="{{{{s.toggle}}}}" aria-pressed="{{{{s.on}}}}" style="width: 100%; display: flex; align-items: center; gap: 11px; padding: 10px 2px; border: 0; border-bottom: 1px solid {RULE}; background: transparent; font-family: inherit; text-align: start; cursor: pointer">
<span style="flex-shrink: 0; width: 15px; height: 15px; border-radius: 2px; border: 1.5px solid {{{{s.color}}}}; background: {{{{s.fill}}}}; display: flex; align-items: center; justify-content: center">
<sc-if value="{{{{s.on}}}}" hint-placeholder-val="{{{{ true }}}}">
<svg width="9" height="9" viewBox="0 0 12 12" fill="none" aria-hidden="true"><path d="M2 6.5L4.8 9 10 3.4" stroke="{PAPER}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
</sc-if>
</span>
<span style="flex: 1; min-width: 0">
<span style="display: block; font-size: 14.5px; color: {{{{s.textColor}}}}">{{{{s.name}}}}</span>
<span style="display: block; font-size: 11.5px; color: {SAGE}">{{{{s.sub}}}}</span>
</span>
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 13px; color: {SAGE}">{{{{s.count}}}}</span>
</button>
</sc-for>

<h2 style="margin: 24px 0 10px; font-family: 'Reem Kufi', sans-serif; font-size: 17px; font-weight: 500">الفئات</h2>
<div style="display: flex; flex-direction: column; gap: 7px">
<sc-for list="{{{{cats}}}}" as="c" hint-placeholder-count="6">
<div style="display: flex; align-items: center; gap: 9px; font-size: 13px; color: #44423D">
<span style="width: 26px; height: 20px; line-height: 20px; text-align: center; border-radius: 2px; color: {PAPER}; font-size: 11.5px; background: {{{{c.color}}}}">{{{{c.code}}}}</span>
<span>{{{{c.label}}}}</span>
</div>
</sc-for>
</div>

<p style="margin: 22px 0 0; padding-top: 14px; border-top: 1px solid {RULE}; font-size: 12px; line-height: 1.85; color: {SAGE}">علامة ≈ تعني أن ردّ مصطلح المصدر إلى الفئة العامة تقريبيّ، ولم يراجعه متخصص بعد.</p>
</aside>

<main style="overflow-y: auto; display: flex; flex-direction: column; align-items: center; padding: 26px 0 34px">

<div style="width: 672px; border: 1.5px solid {LAPIS}; padding: 7px; background: {PAPER}">
<div style="border: 0.8px solid {OCHRE}; padding: 26px 26px 22px">
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 18px">
<span style="height: 1px; flex: 1; background: {OCHRE}; opacity: 0.5"></span>
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 14px; color: {OCHRE}">الجزء الأول</span>
<span style="height: 1px; flex: 1; background: {OCHRE}; opacity: 0.5"></span>
</div>
<p style="margin: 0; font-family: 'Maghribi', serif; font-size: 25px; line-height: 2.55; text-align: justify; color: {INK}">{{{{pageText}}}}</p>
</div>
</div>
<div style="width: 672px; display: flex; align-items: center; justify-content: space-between; padding: 11px 2px 0; font-size: 13px; color: {SAGE}">
<button type="button" style="height: 36px; padding: 0 13px; border: 1px solid {RULE}; border-radius: 3px; background: transparent; font-family: inherit; font-size: 13px; color: {INK}; cursor: pointer">الصفحة السابقة</button>
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 15px; color: {INK}">٥</span>
<button type="button" style="height: 36px; padding: 0 13px; border: 1px solid {RULE}; border-radius: 3px; background: transparent; font-family: inherit; font-size: 13px; color: {INK}; cursor: pointer">الصفحة التالية</button>
</div>

<section style="width: 672px; margin-top: 30px">
<h2 style="margin: 0 0 3px; font-family: 'Reem Kufi', sans-serif; font-size: 18px; font-weight: 500">حاشية الصفحة</h2>
<p style="margin: 0 0 14px; font-size: 13px; color: {SAGE}">{{{{apparatusNote}}}}</p>
<div style="border-top: 1px solid {RULE}">
<sc-for list="{{{{apparatus}}}}" as="p" hint-placeholder-count="6">
<button type="button" onClick="{{{{p.pick}}}}" style="width: 100%; display: grid; grid-template-columns: 152px minmax(0, 1fr); gap: 18px; align-items: start; padding: 13px 4px; border: 0; border-bottom: 1px solid {RULE}; background: {{{{p.bg}}}}; font-family: inherit; text-align: start; cursor: pointer">
<span style="display: block">
<span style="display: block; font-family: 'Maghribi', serif; font-size: 20px; line-height: 1.7; color: {INK}">{{{{p.word}}}}</span>
<span style="display: block; font-size: 11.5px; color: {SAGE}">{{{{p.loc}}}}</span>
</span>
<span style="display: flex; flex-wrap: wrap; gap: 7px; padding-top: 3px">
<sc-for list="{{{{p.marks}}}}" as="m" hint-placeholder-count="3">
<span style="display: inline-flex; align-items: center; gap: 6px; padding: 3px 9px 3px 4px; border: 1px solid {{{{m.color}}}}; border-radius: 2px; font-size: 12.5px; color: {INK}; background: {PAPER}">
<span style="display: inline-block; min-width: 22px; height: 18px; line-height: 18px; text-align: center; border-radius: 2px; color: {PAPER}; font-size: 11px; background: {{{{m.color}}}}">{{{{m.approx}}}}{{{{m.code}}}}</span>
<span style="color: {SAGE}">{{{{m.src}}}}</span>
<span>{{{{m.term}}}}</span>
<sc-if value="{{{{m.proposed}}}}" hint-placeholder-val="{{{{ false }}}}">
<span style="font-size: 10.5px; color: {CARMINE}">مقترح</span>
</sc-if>
</span>
</sc-for>
</span>
</button>
</sc-for>
</div>
</section>
</main>
</div>
</div>'''

script = DATA + '''

class Component extends DCLogic {
  constructor(props) {
    super(props);
    this.state = { off: {}, sel: null };
  }

  renderVals() {
    const off = this.state.off;
    const ids = Object.keys(SRC);
    const anyOff = ids.some((k) => off[k]);

    const sources = ids.map((k) => {
      const on = !off[k];
      return {
        name: SRC[k].n, sub: SRC[k].s, color: SRC[k].c, on,
        fill: on ? SRC[k].c : 'transparent',
        textColor: on ? '#1C1815' : '#8A857B',
        count: COUNTS[k],
        toggle: () => this.setState({ off: { ...off, [k]: !off[k] } })
      };
    });

    const shown = POS.map((p) => {
      const marks = Object.keys(p.m).filter((k) => !off[k]).map((k) => {
        const m = p.m[k], c = CAT[m.c];
        return {
          code: c.k, color: c.c, src: SRC[k].n, term: m.t,
          approx: m.a ? '\\u2248' : '',
          proposed: m.st === 'proposed'
        };
      });
      return {
        word: p.text, loc: 'البقرة ' + p.sura + ':' + p.ayah,
        marks,
        bg: this.state.sel === p.seq ? '#EFECE2' : 'transparent',
        pick: () => this.setState({ sel: p.seq })
      };
    }).filter((p) => p.marks.length);

    const total = shown.reduce((n, p) => n + p.marks.length, 0);

    return {
      pageText: PAGE_TEXT,
      sources,
      cats: Object.keys(CAT).map((k) => ({ label: CAT[k].l, code: CAT[k].k, color: CAT[k].c })),
      apparatus: shown,
      apparatusNote: shown.length + ' مواضع في هذه الصفحة · ' + total + ' حكماً من المصادر المختارة',
      allLabel: anyOff ? 'أظهر كل المصادر' : 'أخفِ كل المصادر',
      toggleAll: () => this.setState({
        off: anyOff ? {} : Object.fromEntries(ids.map((k) => [k, true]))
      })
    };
  }
}'''

script = ('const COUNTS = '+json.dumps({k:f'{v[3]:,}'.replace(',','٬') for k,v in SRC.items()},ensure_ascii=False)+';\n') + script
open(ROOT+'Reader.dc.html','w',encoding='utf-8').write(doc('قارئ المصحف — جامع الوقوف', body, script, 1440, 980))
print('Reader written ·', len(POS), 'مواضع')
