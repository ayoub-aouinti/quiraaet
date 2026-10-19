import sys, json, sqlite3
sys.path.insert(0,'gen')
from tokens import *
exec(open('gen/mobile.py').read().split('# ============')[0].split("ROOT=")[0])
ROOT='/tmp/claude-0/-home-claude/3d4ae7fd-b04d-5598-b44d-3e07691c2ad4/scratchpad/w/project/'
con=sqlite3.connect('out/waqf.db'); con.row_factory=sqlite3.Row
rows=con.execute('''SELECT w.seq,w.sura,w.ayah,w.text,r.source,r.symbol,r.term,r.category,r.approx,r.status,r.context
 FROM words w JOIN rulings r ON r.seq=w.seq WHERE w.sura=2 AND w.ayah BETWEEN 15 AND 22 ORDER BY w.seq''').fetchall()
by={}
for r in rows:
    by.setdefault(r['seq'],{'text':r['text'],'sura':r['sura'],'ayah':r['ayah'],'m':{}})
    by[r['seq']]['m'][r['source']]={'s':r['symbol'],'t':r['term'],'c':r['category'],
        'a':bool(r['approx']),'st':r['status'],'x':(r['context'] or '')[:150]}
POS=[{'seq':k,**v} for k,v in sorted(by.items())][:12]
SEL=max(POS, key=lambda p: len(p['m']))

DATA=('const POS='+json.dumps(POS,ensure_ascii=False,separators=(',',':'))+';\n'
      'const SEL='+json.dumps(SEL,ensure_ascii=False,separators=(',',':'))+';\n'
      'const SRC='+json.dumps({k:{'n':v[0],'c':v[1],'s':v[2],'a':v[2]} for k,v in SRC.items()},ensure_ascii=False)+';\n'
      'const CAT='+json.dumps({k:{'l':v[0],'k':v[1],'c':v[2]} for k,v in CAT.items()},ensure_ascii=False)+';\n'
      'const ORDER='+json.dumps(list(SRC.keys()))+';')

def tabbar(active):
    items=[('المصحف','Main.dc.html','M4 5.5C4 4.7 4.7 4 5.5 4H11v15H5.5C4.7 19 4 18.3 4 17.5zM20 5.5c0-.8-.7-1.5-1.5-1.5H13v15h5.5c.8 0 1.5-.7 1.5-1.5z'),
           ('المقارنة','Compare.dc.html','M4 4h16v16H4zM4 10h16M10 4v16'),
           ('الموضع','Position.dc.html','M12 3v18M7 8l5-5 5 5')]
    out=''
    for name,href,path in items:
        on=name==active; col=LAPIS if on else '#8A857B'
        bd=f'border-top: 2px solid {LAPIS}' if on else 'border-top: 2px solid transparent'
        tag='div' if on else 'a'; h='' if on else f' href="{href}"'
        out+=f'''<{tag}{h} style="flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 4px; color: {col}; font-size: 11.5px; {bd}">
<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="{path}"/></svg><span>{name}</span></{tag}>'''
    return f'<nav style="flex-shrink: 0; display: flex; height: 58px; background: {PAPER}; border-top: 1px solid {RULE}">{out}</nav>'

# ============ المقارنة ============
heads=''.join(f'<div style="flex: 0 0 74px; padding: 9px 2px; text-align: center; font-size: 11px; color: {v[1]}">{v[0]}</div>' for v in SRC.values())
body_cmp=f'''
<div dir="rtl" style="width: 390px; height: 844px; overflow: hidden; background: {LEAF}; color: {INK}; font-family: 'Readex Pro', sans-serif; display: flex; flex-direction: column">
<header style="flex-shrink: 0; padding: 13px 16px 11px; background: {PAPER}; border-bottom: 1px solid {RULE}">
<div style="font-family: 'Reem Kufi', sans-serif; font-size: 16px; font-weight: 600">المقارنة</div>
<div style="font-size: 11.5px; color: {SAGE}">{{{{summary}}}}</div>
</header>
<div style="flex-shrink: 0; padding: 10px 14px 6px; display: flex; gap: 8px">
<button type="button" onClick="{{{{toggle}}}}" aria-pressed="{{{{only}}}}" style="height: 44px; padding: 0 14px; border: 1px solid {{{{btnBd}}}}; border-radius: 3px; background: {{{{btnBg}}}}; color: {{{{btnFg}}}}; font-family: inherit; font-size: 13px; cursor: pointer">المواضع المتعدّدة فقط</button>
</div>
<div style="flex: 1; min-height: 0; overflow: auto; margin: 4px 12px 0; background: {PAPER}; border: 1px solid {RULE}">
<div style="width: 612px">
<div style="display: flex; align-items: center; position: sticky; top: 0; z-index: 3; background: #EFECE2; border-bottom: 1px solid {RULE}">
<div style="position: sticky; right: 0; z-index: 4; flex: 0 0 168px; padding: 9px 11px; background: #EFECE2; border-inline-end: 1px solid {RULE}; font-size: 11.5px; color: {SAGE}">الموضع</div>
{heads}
</div>
<sc-for list="{{{{rows}}}}" as="r" hint-placeholder-count="10">
<div style="display: flex; align-items: stretch; border-bottom: 1px solid {RULE}">
<div style="position: sticky; right: 0; z-index: 2; flex: 0 0 168px; box-sizing: border-box; padding: 9px 11px; background: {PAPER}; border-inline-end: 1px solid {RULE}">
<div style="font-family: 'Maghribi', serif; font-size: 17px; line-height: 1.7">{{{{r.word}}}}</div>
<div style="font-size: 10.5px; color: {SAGE}">{{{{r.loc}}}}</div>
</div>
<sc-for list="{{{{r.cells}}}}" as="c" hint-placeholder-count="6">
<div style="flex: 0 0 74px; display: flex; align-items: center; justify-content: center">
<a href="Position.dc.html" aria-label="{{{{c.aria}}}}" style="display: flex; align-items: center; justify-content: center; width: 70px; height: 44px">
<span style="display: inline-block; min-width: 30px; height: 21px; line-height: 21px; padding: 0 5px; text-align: center; border-radius: 2px; font-size: 11.5px; color: {{{{c.fg}}}}; background: {{{{c.bg}}}}; border: {{{{c.bd}}}}">{{{{c.code}}}}</span>
</a>
</div>
</sc-for>
</div>
</sc-for>
<div style="position: sticky; right: 0; width: 366px; padding: 13px; font-size: 11.5px; line-height: 1.85; color: {SAGE}">— لا علامة عند هذا المصدر · ≈ ردّ المصطلح إلى الفئة تقريبيّ · الإطار المنقّط يعني حكماً مقترحاً لم يُراجع.</div>
</div>
</div>
{tabbar('المقارنة')}
</div>'''

script_cmp=DATA+'''
class Component extends DCLogic {
  constructor(p){ super(p); this.state={only:false}; }
  renderVals(){
    const only=this.state.only;
    const all=POS.map((p)=>({
      word:p.text, loc:'البقرة ٢:'+p.ayah, n:Object.keys(p.m).length,
      cells:ORDER.map((k)=>{
        const m=p.m[k];
        if(!m) return {code:'—', bg:'#EFECE2', fg:'#8A857B', bd:'0', aria:SRC[k].n+' لا علامة'};
        const c=CAT[m.c];
        return {code:(m.a?'\\u2248':'')+c.k, bg:c.c, fg:'#F6F4EE',
                bd: m.st==='proposed' ? '1.5px dashed #8C2F39' : '0',
                aria:SRC[k].n+' '+m.t};
      })
    }));
    const rows= only ? all.filter((r)=>r.n>1) : all;
    const multi= all.filter((r)=>r.n>1).length;
    return { rows, only,
      summary: all.length+' موضعاً · '+multi+' فيها أكثر من مصدر',
      btnBg: only?'#1E3A5F':'transparent', btnFg: only?'#F6F4EE':'#1C1815',
      btnBd: only?'#1E3A5F':'#CFC9BA',
      toggle:()=>this.setState({only:!this.state.only}) };
  }
}'''
open(ROOT+'Compare.dc.html','w',encoding='utf-8').write(doc('المقارنة — جامع الوقوف', body_cmp, script_cmp, 390, 844))

# ============ بطاقة الموضع ============
body_pos=f'''
<div dir="rtl" style="width: 390px; height: 844px; overflow: hidden; background: {LEAF}; color: {INK}; font-family: 'Readex Pro', sans-serif; display: flex; flex-direction: column">
<header style="flex-shrink: 0; display: flex; align-items: center; gap: 12px; padding: 12px 14px; background: {PAPER}; border-bottom: 1px solid {RULE}">
<a href="Main.dc.html" aria-label="رجوع إلى المصحف" style="flex-shrink: 0; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; color: {INK}">
<svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>
</a>
<div>
<div style="font-family: 'Reem Kufi', sans-serif; font-size: 15.5px; font-weight: 600">الموضع</div>
<div style="font-size: 11.5px; color: {SAGE}">{{{{loc}}}}</div>
</div>
</header>

<div style="flex: 1; min-height: 0; overflow-y: auto; padding: 14px 14px 22px">

<div style="border: 1.4px solid {LAPIS}; padding: 5px; background: {PAPER}; margin-bottom: 16px">
<div style="border: 0.8px solid {OCHRE}; padding: 16px 15px">
<div style="font-size: 11.5px; color: {SAGE}; margin-bottom: 7px">الوقف بعد</div>
<div style="font-family: 'Maghribi', serif; font-size: 31px; line-height: 1.8">{{{{word}}}}</div>
</div>
</div>

<h2 style="margin: 0 0 3px; font-family: 'Reem Kufi', sans-serif; font-size: 15.5px; font-weight: 500">ما قاله كل مصدر</h2>
<p style="margin: 0 0 10px; font-size: 11.5px; line-height: 1.8; color: {SAGE}">اللفظ أولاً كما استعمله صاحبه، ثم الفئة العامة للّون.</p>

<div style="border-top: 1px solid {RULE}">
<sc-for list="{{{{rows}}}}" as="r" hint-placeholder-count="6">
<div style="padding: 12px 2px; border-bottom: 1px solid {RULE}; border-inline-start: 3px solid {{{{r.sideColor}}}}; padding-inline-start: 11px">
<div style="display: flex; align-items: baseline; justify-content: space-between; gap: 10px; margin-bottom: 5px">
<span style="font-size: 14px; font-weight: 500; color: {{{{r.nameColor}}}}">{{{{r.name}}}}</span>
<sc-if value="{{{{r.proposed}}}}" hint-placeholder-val="{{{{ false }}}}">
<span style="flex-shrink: 0; padding: 2px 8px; border: 1px dashed {CARMINE}; border-radius: 2px; font-size: 10.5px; color: {CARMINE}">مقترح — لم يُراجع</span>
</sc-if>
</div>
<div style="display: flex; align-items: center; gap: 9px; flex-wrap: wrap">
<span style="font-size: 15px">{{{{r.term}}}}</span>
<sc-if value="{{{{r.has}}}}" hint-placeholder-val="{{{{ true }}}}">
<span style="display: inline-flex; align-items: center; gap: 6px; font-size: 11.5px; color: {SAGE}">
<span style="display: inline-block; min-width: 26px; height: 19px; line-height: 19px; text-align: center; border-radius: 2px; color: {PAPER}; font-size: 11px; background: {{{{r.catColor}}}}">{{{{r.approx}}}}{{{{r.code}}}}</span>
<span>{{{{r.catLabel}}}}</span>
</span>
</sc-if>
</div>
<sc-if value="{{{{r.hasCtx}}}}" hint-placeholder-val="{{{{ false }}}}">
<p style="margin: 8px 0 0; padding: 9px 11px; background: {PAPER}; font-size: 12px; line-height: 1.85; color: #44423D">{{{{r.ctx}}}}</p>
</sc-if>
</div>
</sc-for>
</div>

<a href="Compare.dc.html" style="display: flex; align-items: center; justify-content: center; height: 48px; margin-top: 18px; border-radius: 3px; background: {LAPIS}; color: {PAPER}; font-size: 15px; font-weight: 500">قارن هذا الموضع بغيره</a>
</div>
{tabbar('الموضع')}
</div>'''

script_pos=DATA+'''
class Component extends DCLogic {
  renderVals(){
    const rows=ORDER.map((k)=>{
      const m=SEL.m[k];
      if(!m) return {name:SRC[k].n, nameColor:'#8A857B', sideColor:'#CFC9BA',
        term:'لا علامة عند هذا المصدر في هذا الموضع', has:false, hasCtx:false,
        proposed:false, approx:'', code:'', catLabel:'', catColor:'#EFECE2', ctx:''};
      const c=CAT[m.c];
      return {name:SRC[k].n, nameColor:'#1C1815', sideColor:SRC[k].c,
        term:m.t+' ('+m.s+')', has:true, approx:m.a?'\\u2248 ':'', code:c.k,
        catLabel:c.l, catColor:c.c, proposed:m.st==='proposed',
        hasCtx:!!m.x, ctx:m.x};
    });
    return { word:SEL.text, loc:'سورة البقرة ٢:'+SEL.ayah, rows };
  }
}'''
open(ROOT+'Position.dc.html','w',encoding='utf-8').write(doc('بطاقة الموضع — جامع الوقوف', body_pos, script_pos, 390, 844))
print('Compare + Position written · الموضع المختار:', SEL['text'], len(SEL['m']),'مصادر')
