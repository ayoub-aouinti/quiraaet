import sys, json, sqlite3
sys.path.insert(0,'gen')
from tokens import *
import json as _j
ROOT='/tmp/claude-0/-home-claude/3d4ae7fd-b04d-5598-b44d-3e07691c2ad4/scratchpad/w/project/'
RW=json.load(open('out/page_riwayat.json',encoding='utf-8'))
con=sqlite3.connect('out/waqf.db'); con.row_factory=sqlite3.Row
rows=con.execute('''SELECT w.seq,w.ayah,w.text,r.source,r.symbol,r.category,r.approx
 FROM words w JOIN rulings r ON r.seq=w.seq WHERE w.sura=2 AND w.ayah BETWEEN 15 AND 20 ORDER BY w.seq''').fetchall()
by={}
for r in rows:
    by.setdefault(r['seq'],{'text':r['text'],'ayah':r['ayah'],'m':{}})
    by[r['seq']]['m'][r['source']]={'c':r['category'],'a':bool(r['approx'])}
POS=[{'seq':k,**v} for k,v in sorted(by.items())][:10]
RIW=[dict(r) for r in con.execute('SELECT id,name,region,script,word_count,has_text FROM riwayat')]

DATA=('const TEXTS='+json.dumps({'warsh':RW['warsh'],'hafs':RW['hafs']},ensure_ascii=False)+';\n'
 'const RIW='+json.dumps(RIW,ensure_ascii=False)+';\n'
 'const POS='+json.dumps(POS,ensure_ascii=False,separators=(',',':'))+';\n'
 'const SRC='+json.dumps({k:{'n':v[0],'c':v[1],'s':v[2]} for k,v in SRC.items()},ensure_ascii=False)+';\n'
 'const CAT='+json.dumps({k:{'l':v[0],'k':v[1],'c':v[2]} for k,v in CAT.items()},ensure_ascii=False)+';\n'
 'const RFONT='+_j.dumps(RIW_FONT,ensure_ascii=False)+';\n'
 'const RCOL='+_j.dumps(RIW_COLOR,ensure_ascii=False)+';\n'
 'const COUNTS='+json.dumps({k:f'{v[3]:,}'.replace(',',chr(0x066C)) for k,v in SRC.items()},ensure_ascii=False)+';')

tab=f'''<nav style="flex-shrink: 0; display: flex; height: 58px; background: {PAPER}; border-top: 1px solid {RULE}">
<div style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; color: {LAPIS}; font-size: 11.5px; border-top: 2px solid {LAPIS}">
<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v15H5.5C4.7 19 4 18.3 4 17.5zM20 5.5c0-.8-.7-1.5-1.5-1.5H13v15h5.5c.8 0 1.5-.7 1.5-1.5z"/></svg><span>المصحف</span></div>
<a href="Compare.dc.html" style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; color: #8A857B; font-size: 11.5px; border-top: 2px solid transparent">
<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 4h16v16H4zM4 10h16M10 4v16"/></svg><span>المقارنة</span></a>
<a href="Position.dc.html" style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; color: #8A857B; font-size: 11.5px; border-top: 2px solid transparent">
<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v18M7 8l5-5 5 5"/></svg><span>الموضع</span></a>
</nav>'''

body=f'''
<div dir="rtl" style="position: relative; width: 390px; height: 844px; overflow: hidden; background: {LEAF}; color: {INK}; font-family: 'Readex Pro', sans-serif; display: flex; flex-direction: column">

<header style="flex-shrink: 0; padding: 12px 15px 0; background: {PAPER}; border-bottom: 1px solid {RULE}">
<div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 9px">
<div>
<div style="font-family: 'Reem Kufi', sans-serif; font-size: 15.5px; font-weight: 600">سورة البقرة</div>
<div style="font-size: 11px; color: {SAGE}">الجزء الأول — صفحة ٥</div>
</div>
<button type="button" onClick="{{{{openSheet}}}}" style="height: 44px; padding: 0 12px; border: 1px solid {RULE}; border-radius: 3px; background: {LEAF}; font-family: inherit; font-size: 12.5px; color: {INK}; cursor: pointer">{{{{nOn}}}} مصادر</button>
</div>
<div style="display: flex; gap: 0; overflow-x: auto">
<sc-for list="{{{{riwayat}}}}" as="r" hint-placeholder-count="4">
<button type="button" onClick="{{{{r.pick}}}}" aria-pressed="{{{{r.on}}}}" disabled="{{{{r.off}}}}" style="flex-shrink: 0; min-height: 44px; padding: 0 13px; border: 0; border-bottom: 2px solid {{{{r.bar}}}}; background: transparent; font-family: inherit; font-size: 13px; color: {{{{r.fg}}}}; cursor: {{{{r.cursor}}}}; white-space: nowrap">{{{{r.name}}}}</button>
</sc-for>
</div>
</header>

<div style="flex: 1; min-height: 0; overflow-y: auto; padding: 12px 12px 18px">
<div style="padding: 9px 12px; margin-bottom: 11px; background: {PAPER}; border-inline-start: 3px solid {{{{riwColor}}}}; font-size: 11.5px; line-height: 1.75; color: {SAGE}">{{{{riwMeta}}}}</div>

<div style="border: 1.4px solid {LAPIS}; padding: 5px; background: {PAPER}">
<div style="border: 0.8px solid {OCHRE}; padding: 16px 14px 14px">
<p style="margin: 0; font-family: {{{{fontStack}}}}; font-size: {{{{fontSize}}}}; line-height: 2.5; text-align: justify; color: {INK}">{{{{pageText}}}}</p>
</div>
</div>
<div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 2px 0; font-size: 12px; color: {SAGE}">
<span>السابقة</span><span style="font-family: 'Reem Kufi', sans-serif; font-size: 13.5px; color: {INK}">٥</span><span>التالية</span>
</div>

<h2 style="margin: 20px 0 3px; font-family: 'Reem Kufi', sans-serif; font-size: 15px; font-weight: 500">حاشية الصفحة</h2>
<p style="margin: 0 0 9px; font-size: 11.5px; color: {SAGE}">{{{{note}}}}</p>
<div style="border-top: 1px solid {RULE}">
<sc-for list="{{{{apparatus}}}}" as="p" hint-placeholder-count="6">
<a href="Position.dc.html" style="display: block; padding: 10px 2px; border-bottom: 1px solid {RULE}">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 10px; margin-bottom: 5px">
<span style="font-family: 'Amiri Quran', serif; font-size: 17px">{{{{p.word}}}}</span>
<span style="font-size: 10.5px; color: {SAGE}">{{{{p.loc}}}}</span></span>
<span style="display: flex; flex-wrap: wrap; gap: 5px">
<sc-for list="{{{{p.marks}}}}" as="m" hint-placeholder-count="3">
<span style="display: inline-flex; align-items: center; gap: 5px; padding: 2px 8px 2px 3px; border: 1px solid {{{{m.color}}}}; border-radius: 2px; font-size: 11px; background: {PAPER}">
<span style="display: inline-block; min-width: 19px; height: 16px; line-height: 16px; text-align: center; border-radius: 2px; color: {PAPER}; font-size: 10px; background: {{{{m.color}}}}">{{{{m.approx}}}}{{{{m.code}}}}</span>
<span style="color: {SAGE}">{{{{m.src}}}}</span></span>
</sc-for>
</span></a>
</sc-for>
</div>
</div>
{tab}

<sc-if value="{{{{sheet}}}}" hint-placeholder-val="{{{{ false }}}}">
<button type="button" onClick="{{{{closeSheet}}}}" aria-label="إغلاق" style="position: absolute; inset: 0; border: 0; padding: 0; background: rgba(28, 24, 21, 0.42); cursor: pointer"></button>
<div style="position: absolute; left: 0; right: 0; bottom: 0; background: {PAPER}; border-top: 2px solid {LAPIS}; padding: 10px 17px 20px; max-height: 600px; overflow-y: auto">
<span style="display: block; width: 38px; height: 4px; border-radius: 2px; background: {RULE}; margin: 0 auto 9px"></span>
<h2 style="margin: 0 0 2px; font-family: 'Reem Kufi', sans-serif; font-size: 16.5px; font-weight: 500">المصادر المعروضة</h2>
<p style="margin: 0 0 9px; font-size: 11.5px; color: {SAGE}">{{{{srcNote}}}}</p>
<sc-for list="{{{{sources}}}}" as="s" hint-placeholder-count="6">
<button type="button" onClick="{{{{s.toggle}}}}" aria-pressed="{{{{s.on}}}}" style="width: 100%; display: flex; align-items: center; gap: 10px; min-height: 46px; padding: 6px 0; border: 0; border-bottom: 1px solid {RULE}; background: transparent; font-family: inherit; text-align: start; cursor: pointer">
<span style="flex-shrink: 0; width: 16px; height: 16px; border-radius: 2px; border: 1.5px solid {{{{s.color}}}}; background: {{{{s.fill}}}}"></span>
<span style="flex: 1"><span style="display: block; font-size: 14px; color: {{{{s.textColor}}}}">{{{{s.name}}}}</span>
<span style="display: block; font-size: 11px; color: {SAGE}">{{{{s.sub}}}}</span></span>
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 12.5px; color: {SAGE}">{{{{s.count}}}}</span>
</button>
</sc-for>
</div>
</sc-if>
</div>'''

script=DATA+'''
class Component extends DCLogic {
  constructor(p){ super(p); this.state={off:{}, sheet:false, riw:'warsh'}; }
  renderVals(){
    const st=this.state, off=st.off, riw=st.riw, ids=Object.keys(SRC);
    const meta=RIW.find((r)=>r.id===riw), warsh=riw==='warsh';
    const riwayat=RIW.map((r)=>{ const on=r.id===riw, has=!!r.has_text;
      return { name:r.name, on, off:!has, bar:on?'#1E3A5F':'transparent',
        fg:on?'#1C1815':(has?'#5A6B5D':'#A49E92'), cursor:has?'pointer':'not-allowed',
        pick:()=>{ if(has) this.setState({riw:r.id}); } }; });
    const sources=ids.map((k)=>{ const on=!off[k];
      return { name:SRC[k].n, sub:SRC[k].s, color:SRC[k].c, on, count:COUNTS[k],
        fill:on?SRC[k].c:'transparent', textColor:on?'#1C1815':'#8A857B',
        toggle:()=>this.setState({off:{...off,[k]:!off[k]}}) }; });
    const ap=POS.map((p)=>({ word:p.text, loc:'٢:'+p.ayah,
      marks:Object.keys(p.m).filter((k)=>!off[k]).map((k)=>{
        const m=p.m[k], c=CAT[m.c];
        return {code:c.k, color:c.c, src:SRC[k].n, approx:m.a?'\\u2248':''}; })
    })).filter((p)=>p.marks.length);
    return { riwayat, sources, apparatus:ap,
      pageText:TEXTS[riw],
      fontStack: RFONT[riw][0],
      fontSize: RFONT[riw][2],
      riwColor: RCOL[riw],
      riwMeta: meta.name+' — '+meta.region+' · رسم '+meta.script,
      nOn: ids.filter((k)=>!off[k]).length,
      note: ap.length+' مواضع في هذه الصفحة',
      srcNote: (riw==='warsh'||riw==='qalun') ? 'علامات الرواية في نصّها، وغيرها محاذاةً على حفص' : 'كلها على فهرس حفص',
      sheet: st.sheet,
      openSheet:()=>this.setState({sheet:true}),
      closeSheet:()=>this.setState({sheet:false}) };
  }
}'''
open(ROOT+'Main.dc.html','w',encoding='utf-8').write(doc('صفحة المصحف — جامع الوقوف', body, script, 390, 844))
print('Main محدّث بالروايات')
