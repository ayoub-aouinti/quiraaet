import sys, json, sqlite3
sys.path.insert(0,'gen')
from tokens import *
# صفُّ كلِّ مصدرٍ ينتظر نصَّه، يُبنى من القائمة مهما طالت أو قصرت
PENDROWS = ''.join(
  '<div style="display: flex; align-items: center; gap: 10px; min-height: 40px;'
  ' padding: 7px 2px; border-bottom: 1px solid {R}">'
  '<span style="flex-shrink: 0; width: 15px; height: 15px; border-radius: 2px;'
  ' border: 1.5px dashed {R}"></span>'
  '<span style="flex: 1"><span style="display: block; font-size: 13.5px;'
  ' color: #A49E92">{N}</span>'
  '<span style="display: block; font-size: 11px; color: #A49E92">{A}</span></span>'
  '</div>'.replace('{R}', RULE).replace('{N}', n).replace('{A}', a)
  for n, a in PENDING)
import json as _j
ROOT='/tmp/claude-0/-home-claude/3d4ae7fd-b04d-5598-b44d-3e07691c2ad4/scratchpad/w/project/'
RW=json.load(open('out/page_riwayat.json',encoding='utf-8'))
PW=json.load(open('out/page_words.json',encoding='utf-8'))
con=sqlite3.connect('out/waqf.db'); con.row_factory=sqlite3.Row
rows=con.execute('''SELECT w.seq,w.sura,w.ayah,w.text,r.source,r.symbol,r.term,r.category,r.approx,r.status
  FROM words w JOIN rulings r ON r.seq=w.seq WHERE w.sura=2 AND w.ayah BETWEEN 15 AND 20 ORDER BY w.seq''').fetchall()
by={}
for r in rows:
    by.setdefault(r['seq'],{'text':r['text'],'sura':r['sura'],'ayah':r['ayah'],'m':{}})
    by[r['seq']]['m'][r['source']]={'s':r['symbol'],'t':r['term'],'c':r['category'],'a':bool(r['approx']),'st':r['status']}
POS=[{'seq':k,**v} for k,v in sorted(by.items())][:9]
RIW=[dict(r) for r in con.execute('SELECT id,name,line,region,script,word_count,has_text FROM riwayat')]

DATA=('const PAGEW='+json.dumps(PW['pagew'],ensure_ascii=False,separators=(',',':'))+';\n'
 'const RUL='+json.dumps(PW['rul'],ensure_ascii=False,separators=(',',':'))+';\n'
 'const RIW='+json.dumps(RIW,ensure_ascii=False)+';\n'
 'const POS='+json.dumps(POS,ensure_ascii=False,separators=(',',':'))+';\n'
 'const SRC='+json.dumps({k:{'n':v[0],'c':v[1],'s':v[2]} for k,v in SRC.items()},ensure_ascii=False)+';\n'
 'const CAT='+json.dumps({k:{'l':v[0],'k':v[1],'c':v[2]} for k,v in CAT.items()},ensure_ascii=False)+';\n'
 'const RFONT='+_j.dumps(RIW_FONT,ensure_ascii=False)+';\n'
 'const RCOL='+_j.dumps(RIW_COLOR,ensure_ascii=False)+';\n'
 'const COUNTS='+json.dumps({k:f'{v[3]:,}'.replace(',',chr(0x066C)) for k,v in SRC.items()},ensure_ascii=False)+';')

body=f'''
<div dir="rtl" style="width: 1440px; height: 980px; overflow: hidden; background: {LEAF}; color: {INK}; font-family: 'Readex Pro', sans-serif; display: flex; flex-direction: column">

<header style="flex-shrink: 0; display: flex; align-items: center; justify-content: space-between; gap: 24px; padding: 0 26px; height: 60px; background: {PAPER}; border-bottom: 1px solid {RULE}">
<div style="display: flex; align-items: center; gap: 22px">
<a href="Landing.dc.html" style="display: flex; align-items: center; gap: 9px">
{logo_mark(23)}
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 17px; font-weight: 600">جامع الوقوف</span></a>
<div style="display: flex; align-items: center; gap: 12px; font-size: 13.5px; color: {SAGE}">
<span style="color: {INK}; font-weight: 500">سورة البقرة</span>
<span style="width: 1px; height: 13px; background: {RULE}"></span><span>الجزء الأول</span>
<span style="width: 1px; height: 13px; background: {RULE}"></span><span>صفحة ٥</span>
</div>
</div>
<div style="display: flex; align-items: center; gap: 9px">
<label for="q" style="position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0)">ابحث</label>
<input id="q" type="search" placeholder="ابحث في المصحف" style="width: 200px; height: 37px; padding: 0 12px; border: 1px solid {RULE}; border-radius: 3px; background: {LEAF}; font-family: inherit; font-size: 13.5px; color: {INK}">
<button type="button" onClick="{{{{toggleAll}}}}" style="height: 37px; padding: 0 14px; border: 1px solid {RULE}; border-radius: 3px; background: {LEAF}; font-family: inherit; font-size: 13.5px; color: {INK}; cursor: pointer">{{{{allLabel}}}}</button>
</div>
</header>

<div style="flex-shrink: 0; display: flex; align-items: stretch; gap: 0; background: {PAPER}; border-bottom: 1px solid {RULE}; padding: 0 26px">
<span style="display: flex; align-items: center; font-size: 12.5px; color: {SAGE}; padding-inline-end: 16px">الرواية</span>
<sc-for list="{{{{riwayat}}}}" as="r" hint-placeholder-count="4">
<button type="button" onClick="{{{{r.pick}}}}" aria-pressed="{{{{r.on}}}}" disabled="{{{{r.off}}}}" style="display: flex; flex-direction: column; align-items: flex-start; gap: 1px; min-height: 52px; justify-content: center; padding: 0 18px; border: 0; border-bottom: 2px solid {{{{r.bar}}}}; background: transparent; font-family: inherit; text-align: start; cursor: {{{{r.cursor}}}}">
<span style="font-size: 14px; color: {{{{r.fg}}}}">{{{{r.name}}}}</span>
<span style="font-size: 11px; color: {{{{r.subFg}}}}">{{{{r.sub}}}}</span>
</button>
</sc-for>
</div>

<div style="flex: 1; min-height: 0; display: grid; grid-template-columns: 320px minmax(0, 1fr)">

<aside style="border-inline-end: 1px solid {RULE}; background: {PAPER}; overflow-y: auto; padding: 18px 20px">
<div style="padding: 11px 13px; background: {LEAF}; border-inline-start: 3px solid {{{{riwColor}}}}; margin-bottom: 18px">
<div style="font-size: 14.5px; margin-bottom: 2px">{{{{riwName}}}}</div>
<div style="font-size: 11.5px; line-height: 1.75; color: {SAGE}">{{{{riwMeta}}}}</div>
</div>

<h2 style="margin: 0 0 3px; font-family: 'Reem Kufi', sans-serif; font-size: 16.5px; font-weight: 500">المصادر</h2>
<p style="margin: 0 0 12px; font-size: 12px; line-height: 1.7; color: {SAGE}">{{{{srcNote}}}}</p>
<sc-for list="{{{{sources}}}}" as="s" hint-placeholder-count="6">
<button type="button" onClick="{{{{s.toggle}}}}" aria-pressed="{{{{s.on}}}}" style="width: 100%; display: flex; align-items: center; gap: 10px; min-height: 46px; padding: 8px 2px; border: 0; border-bottom: 1px solid {RULE}; background: transparent; font-family: inherit; text-align: start; cursor: pointer">
<span style="flex-shrink: 0; width: 15px; height: 15px; border-radius: 2px; border: 1.5px solid {{{{s.color}}}}; background: {{{{s.fill}}}}"></span>
<span style="flex: 1; min-width: 0">
<span style="display: block; font-size: 14px; color: {{{{s.textColor}}}}">{{{{s.name}}}}</span>
<span style="display: block; font-size: 11px; color: {SAGE}">{{{{s.sub}}}}</span></span>
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 12.5px; color: {SAGE}">{{{{s.count}}}}</span>
</button>
</sc-for>

<h2 style="margin: 20px 0 3px; font-family: 'Reem Kufi', sans-serif; font-size: 16.5px; font-weight: 500">ينتظر النصّ</h2>
<p style="margin: 0 0 9px; font-size: 12px; line-height: 1.7; color: {SAGE}">مصادر مسجَّلة في الجامع، ومصنَّفاتها لم تُرقمن بعد</p>
{PENDROWS}

<h2 style="margin: 22px 0 9px; font-family: 'Reem Kufi', sans-serif; font-size: 16.5px; font-weight: 500">الفئات</h2>
<div style="display: flex; flex-direction: column; gap: 6px">
<sc-for list="{{{{cats}}}}" as="c" hint-placeholder-count="6">
<div style="display: flex; align-items: center; gap: 9px; font-size: 12.5px; color: #44423D">
<span style="width: 25px; height: 19px; line-height: 19px; text-align: center; border-radius: 2px; color: {PAPER}; font-size: 11px; background: {{{{c.color}}}}">{{{{c.code}}}}</span>
<span>{{{{c.label}}}}</span></div>
</sc-for>
</div>
<p style="margin: 20px 0 0; padding-top: 13px; border-top: 1px solid {RULE}; font-size: 11.5px; line-height: 1.85; color: {SAGE}">أحكام الوقف من المصادر المختلفة تُعرض على أي رواية بمحاذاة الكلمات، بشكل تفاعلي: اضغط أي كلمة مظلَّلة لترى من قال فيها وماذا قال.</p>
</aside>

<main style="overflow-y: auto; display: flex; flex-direction: column; align-items: center; padding: 24px 0 32px">
<div style="width: 668px; border: 1.5px solid {LAPIS}; padding: 7px; background: {PAPER}">
<div style="border: 0.8px solid {OCHRE}; padding: 24px 26px 20px">
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px">
<span style="height: 1px; flex: 1; background: {OCHRE}; opacity: 0.5"></span>
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 13.5px; color: {OCHRE}">{{{{riwName}}}}</span>
<span style="height: 1px; flex: 1; background: {OCHRE}; opacity: 0.5"></span>
</div>
<p style="margin: 0; font-family: {{{{fontStack}}}}; font-size: {{{{fontSize}}}}; line-height: 3.1; text-align: justify; color: {INK}">
<sc-for list="{{{{words}}}}" as="w" hint-placeholder-count="40">
<sc-if value="{{{{w.plain}}}}" hint-placeholder-val="{{{{ true }}}}">
<span>{{{{w.t}}}} </span>
</sc-if>
<sc-if value="{{{{w.marked}}}}" hint-placeholder-val="{{{{ false }}}}">
<button type="button" onClick="{{{{w.pick}}}}" aria-label="{{{{w.aria}}}}" style="position: relative; display: inline-block; padding: 1px 4px; margin: 0 1px; border: 0; border-radius: 2px; font: inherit; color: inherit; cursor: pointer; background: {{{{w.bg}}}}; box-shadow: {{{{w.ring}}}}; border-bottom: 2px solid {{{{w.rule}}}}">{{{{w.t}}}}<span style="position: absolute; top: -17px; right: 0; left: 0; display: flex; justify-content: center; gap: 2px; pointer-events: none">
<sc-for list="{{{{w.dots}}}}" as="d" hint-placeholder-count="3">
<span style="width: 7px; height: 7px; border-radius: 4px; background: {{{{d}}}}"></span>
</sc-for>
</span></button><span> </span>
</sc-if>
</sc-for>
</p>
</div>
</div>
<div style="width: 668px; display: flex; align-items: center; justify-content: space-between; padding: 10px 2px 0; font-size: 12.5px; color: {SAGE}">
<button type="button" style="height: 36px; padding: 0 13px; border: 1px solid {RULE}; border-radius: 3px; background: transparent; font-family: inherit; font-size: 12.5px; color: {INK}; cursor: pointer">السابقة</button>
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 14px; color: {INK}">٥</span>
<button type="button" style="height: 36px; padding: 0 13px; border: 1px solid {RULE}; border-radius: 3px; background: transparent; font-family: inherit; font-size: 12.5px; color: {INK}; cursor: pointer">التالية</button>
</div>

<sc-if value="{{{{card.show}}}}" hint-placeholder-val="{{{{ false }}}}">
<div style="width: 668px; margin-top: 16px; background: {PAPER}; border: 1px solid {LAPIS}; border-top: 3px solid {LAPIS}; padding: 15px 18px">
<div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; margin-bottom: 11px">
<div style="display: flex; align-items: baseline; gap: 10px">
<span style="font-size: 12.5px; color: {SAGE}">الوقف بعد</span>
<span style="font-family: 'Amiri Quran', serif; font-size: 24px">{{{{card.word}}}}</span>
</div>
<button type="button" onClick="{{{{closeCard}}}}" aria-label="إغلاق البطاقة" style="flex-shrink: 0; width: 44px; height: 44px; margin: -12px -12px -12px 0; border: 0; background: transparent; color: {INK}; cursor: pointer; display: flex; align-items: center; justify-content: center">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>
</button>
</div>
<div style="display: flex; flex-direction: column; gap: 1px">
<sc-for list="{{{{card.rows}}}}" as="r" hint-placeholder-count="4">
<div style="display: flex; align-items: center; gap: 12px; padding: 9px 11px; background: {LEAF}; border-inline-start: 3px solid {{{{r.color}}}}">
<span style="flex: 0 0 128px; font-size: 13.5px">{{{{r.src}}}}</span>
<span style="flex: 1; font-size: 14px">{{{{r.term}}}}</span>
<sc-if value="{{{{r.proposed}}}}" hint-placeholder-val="{{{{ false }}}}">
<span style="flex-shrink: 0; padding: 2px 8px; border: 1px dashed {CARMINE}; border-radius: 2px; font-size: 10.5px; color: {CARMINE}">مقترح</span>
</sc-if>
<span style="flex-shrink: 0; display: inline-flex; align-items: center; gap: 6px">
<span style="font-size: 11.5px; color: {SAGE}">{{{{r.cat}}}}</span>
<span style="display: inline-block; min-width: 26px; height: 20px; line-height: 20px; text-align: center; border-radius: 2px; color: {PAPER}; font-size: 11.5px; background: {{{{r.catColor}}}}">{{{{r.code}}}}</span>
</span>
</div>
</sc-for>
</div>
</div>
</sc-if>

<section style="width: 668px; margin-top: 26px">
<h2 style="margin: 0 0 3px; font-family: 'Reem Kufi', sans-serif; font-size: 17.5px; font-weight: 500">حاشية الصفحة</h2>
<p style="margin: 0 0 12px; font-size: 12.5px; color: {SAGE}">{{{{apparatusNote}}}}</p>
<div style="border-top: 1px solid {RULE}">
<sc-for list="{{{{apparatus}}}}" as="p" hint-placeholder-count="6">
<div style="display: grid; grid-template-columns: 148px minmax(0, 1fr); gap: 16px; align-items: start; padding: 12px 4px; border-bottom: 1px solid {RULE}">
<span style="display: block">
<span style="display: block; font-family: 'Amiri Quran', serif; font-size: 19px; line-height: 1.7">{{{{p.word}}}}</span>
<span style="display: block; font-size: 11px; color: {SAGE}">{{{{p.loc}}}}</span></span>
<span style="display: flex; flex-wrap: wrap; gap: 6px; padding-top: 3px">
<sc-for list="{{{{p.marks}}}}" as="m" hint-placeholder-count="3">
<span style="display: inline-flex; align-items: center; gap: 6px; padding: 3px 9px 3px 4px; border: 1px solid {{{{m.color}}}}; border-radius: 2px; font-size: 12px; background: {PAPER}">
<span style="display: inline-block; min-width: 22px; height: 18px; line-height: 18px; text-align: center; border-radius: 2px; color: {PAPER}; font-size: 10.5px; background: {{{{m.color}}}}">{{{{m.approx}}}}{{{{m.code}}}}</span>
<span style="color: {SAGE}">{{{{m.src}}}}</span><span>{{{{m.term}}}}</span>
<sc-if value="{{{{m.proposed}}}}" hint-placeholder-val="{{{{ false }}}}">
<span style="font-size: 10px; color: {CARMINE}">مقترح</span></sc-if>
</span>
</sc-for>
</span>
</div>
</sc-for>
</div>
</section>
</main>
</div>
</div>'''

script=DATA+'''
class Component extends DCLogic {
  constructor(p){ super(p); this.state={off:{}, riw:'warsh', word:null}; }
  renderVals(){
    const off=this.state.off, riw=this.state.riw, ids=Object.keys(SRC);
    const anyOff=ids.some((k)=>off[k]);
    const meta=RIW.find((r)=>r.id===riw);

    const riwayat=RIW.map((r)=>{
      const on=r.id===riw, has=!!r.has_text;
      return { name:r.name, on, off:!has,
        sub: has ? (r.region+' — '+r.script) : 'ينتظر استيراد النصّ',
        bar: on ? '#1E3A5F' : 'transparent',
        fg: on ? '#1C1815' : (has ? '#44423D' : '#A49E92'),
        subFg: has ? '#5A6B5D' : '#A49E92',
        cursor: has ? 'pointer' : 'not-allowed',
        pick: ()=>{ if(has) this.setState({riw:r.id, word:null}); } };
    });

    const sources=ids.map((k)=>{ const on=!off[k];
      return { name:SRC[k].n, sub:SRC[k].s, color:SRC[k].c, on, count:COUNTS[k],
        fill:on?SRC[k].c:'transparent', textColor:on?'#1C1815':'#8A857B',
        toggle:()=>this.setState({off:{...off,[k]:!off[k]}}) }; });

    const ap=POS.map((p)=>({
      word:p.text, loc:'البقرة '+p.sura+':'+p.ayah,
      marks:Object.keys(p.m).filter((k)=>!off[k]).map((k)=>{
        const m=p.m[k], c=CAT[m.c];
        return {code:c.k, color:c.c, src:SRC[k].n, term:m.t,
                approx:m.a?'\\u2248':'', proposed:m.st==='proposed'};
      })
    })).filter((p)=>p.marks.length);

    const warsh = riw==='warsh';
    const sel = this.state.word;
    const on = (k)=>!off[k];

    const words = (PAGEW[riw]||[]).map((w, wi)=>{
      const r = w.s!=null ? RUL[String(w.s)] : null;
      const act = r ? Object.keys(r).filter(on) : [];
      if (!act.length) return { t:w.t, plain:true, marked:false, dots:[], bg:'transparent',
                                ring:'none', rule:'transparent', aria:'', pick:()=>{} };
      const isSel = sel===w.s;
      return {
        t: w.t, plain:false, marked:true,
        dots: act.map((k)=>SRC[k].c),
        bg: isSel ? '#EADFC2' : '#F2E8D2',
        ring: isSel ? '0 0 0 2px #1C1815' : 'none',
        rule: CAT[r[act[0]].c].c,
        aria: act.map((k)=>SRC[k].n+' '+r[k].t).join('، '),
        pick: ()=>this.setState({ word: isSel ? null : w.s })
      };
    });

    let card = { show:false, word:'', rows:[] };
    if (sel!=null && RUL[String(sel)]) {
      const r = RUL[String(sel)];
      const hit = (PAGEW[riw]||[]).find((x)=>x.s===sel);
      card = {
        show:true, word: hit ? hit.t : '',
        rows: Object.keys(r).filter(on).map((k)=>{
          const m=r[k], c=CAT[m.c];
          return { src:SRC[k].n, color:SRC[k].c, term:m.t+' ('+m.s+')',
                   code:(m.a?'\u2248':'')+c.k, catColor:c.c, cat:c.l,
                   proposed:m.st==='proposed' };
        })
      };
    }

    return {
      words, card,
      closeCard: ()=>this.setState({ word:null }),
      riwayat,
      riwName: meta.name,
      riwColor: RCOL[riw],
      riwMeta: meta.line + ' · ' + meta.region + ' · رسم ' + meta.script
               + ' · ' + meta.word_count.toLocaleString('ar-EG') + ' كلمة',
      fontStack: RFONT[riw][0],
      fontSize: RFONT[riw][1],
      sources, apparatus: ap,
      cats: Object.keys(CAT).map((k)=>({label:CAT[k].l, code:CAT[k].k, color:CAT[k].c})),
      srcNote: (riw==='warsh' || riw==='qalun')
        ? 'علامات هذه الرواية في نصّها نفسه، وبقيّة المصادر محاذاةً على حفص'
        : 'المصادر محفوظة على فهرس حفص وتُعرض مباشرة',
      apparatusNote: ap.length + ' مواضع في هذه الصفحة · '
        + ap.reduce((n,p)=>n+p.marks.length,0) + ' حكماً من المصادر المختارة',
      allLabel: anyOff ? 'أظهر الكل' : 'أخفِ الكل',
      toggleAll: ()=>this.setState({off: anyOff ? {} : Object.fromEntries(ids.map((k)=>[k,true]))})
    };
  }
}'''
open(ROOT+'Reader.dc.html','w',encoding='utf-8').write(doc('قارئ المصحف — جامع الوقوف', body, script, 1440, 980))
print('Reader محدّث · روايات:', [r['name'] for r in RIW])
