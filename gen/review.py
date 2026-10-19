import sys, json, sqlite3
sys.path.insert(0,'gen')
from tokens import *
ROOT='/tmp/claude-0/-home-claude/3d4ae7fd-b04d-5598-b44d-3e07691c2ad4/scratchpad/w/project/'
con=sqlite3.connect('out/waqf.db'); con.row_factory=sqlite3.Row
q=list(con.execute('''SELECT w.sura_name,w.sura,w.ayah,w.text,r.source,r.symbol,r.term,
  r.category,r.approx,r.confidence,r.context,r.seq
  FROM rulings r JOIN words w ON w.seq=r.seq
  WHERE r.status='proposed' AND r.context IS NOT NULL AND length(r.context)>80
  ORDER BY r.seq LIMIT 8'''))
QUEUE=[]
for x in q:
    o=[{'src':y['source'],'sym':y['symbol'],'term':y['term'],'cat':y['category'],
        'apx':bool(y['approx']),'st':y['status']}
       for y in con.execute('SELECT source,symbol,term,category,approx,status FROM rulings WHERE seq=? AND source<>?',(x['seq'],x['source']))]
    ay=[r['text'] for r in con.execute('SELECT text FROM words WHERE sura=? AND ayah=? ORDER BY seq',(x['sura'],x['ayah']))]
    QUEUE.append({'loc':f"{x['sura_name']} {x['sura']}:{x['ayah']}",'word':x['text'],'src':x['source'],
      'sym':x['symbol'],'term':x['term'],'cat':x['category'],'apx':bool(x['approx']),
      'conf':x['confidence'] or '','ctx':' '.join((x['context'] or '').split())[:300],
      'seq':x['seq'],'others':o,'ayah':ay})

DATA=('const QUEUE='+json.dumps(QUEUE,ensure_ascii=False,separators=(',',':'))+';\n'
      'const SRC='+json.dumps({k:{'n':v[0],'c':v[1],'s':v[2]} for k,v in SRC.items()},ensure_ascii=False)+';\n'
      'const CAT='+json.dumps({k:{'l':v[0],'k':v[1],'c':v[2]} for k,v in CAT.items()},ensure_ascii=False)+';')

nav=''
for name,href in [('اللوحة','Admin.dc.html'),('المراجعة','AdminReview.dc.html'),
                  ('المصادر','Admin.dc.html'),('المصطلحات','Admin.dc.html'),('السجلّ','Admin.dc.html')]:
    on=name=='المراجعة'
    style=(f'background: {LAPIS}; color: {PAPER}' if on else 'color: #D8D3C7')
    tag='div' if on else 'a'; h='' if on else f' href="{href}"'
    nav+=f'<{tag}{h} style="display: block; padding: 10px 14px; border-radius: 3px; font-size: 14px; {style}">{name}</{tag}>'

body=f'''
<div dir="rtl" style="width: 1440px; height: 980px; overflow: hidden; background: {LEAF}; color: {INK}; font-family: 'Readex Pro', sans-serif; display: grid; grid-template-columns: 222px 300px minmax(0, 1fr)">

<aside style="background: #211D19; padding: 20px 14px; display: flex; flex-direction: column; gap: 5px">
<div style="display: flex; align-items: center; gap: 9px; padding: 0 6px 18px">
{logo_mark(22, PAPER, '#E0B266', '#E8A0A0', PAPER)}
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 16px; font-weight: 600; color: {PAPER}">جامع الوقوف</span>
</div>
<div style="font-size: 11px; color: #8A857B; padding: 0 8px 7px">الإدارة</div>
{nav}
<div style="margin-top: auto; padding: 13px 8px 0; border-top: 1px solid #38322B">
<div style="font-size: 13px; color: {PAPER}">د. المراجع</div>
<div style="font-size: 11.5px; color: #8A857B">محقّق — صلاحية الاعتماد</div>
</div>
</aside>

<section style="background: {PAPER}; border-inline-end: 1px solid {RULE}; overflow-y: auto">
<div style="padding: 18px 18px 12px; border-bottom: 1px solid {RULE}">
<h1 style="margin: 0 0 3px; font-family: 'Reem Kufi', sans-serif; font-size: 18px; font-weight: 500">طابور المراجعة</h1>
<p style="margin: 0 0 11px; font-size: 12.5px; color: {SAGE}">{{{{queueNote}}}}</p>
<div style="display: flex; gap: 6px; flex-wrap: wrap">
<sc-for list="{{{{filters}}}}" as="f" hint-placeholder-count="3">
<button type="button" onClick="{{{{f.pick}}}}" aria-pressed="{{{{f.on}}}}" style="height: 32px; padding: 0 11px; border: 1px solid {{{{f.bd}}}}; border-radius: 2px; background: {{{{f.bg}}}}; color: {{{{f.fg}}}}; font-family: inherit; font-size: 12.5px; cursor: pointer">{{{{f.label}}}}</button>
</sc-for>
</div>
</div>
<sc-for list="{{{{queue}}}}" as="q" hint-placeholder-count="8">
<button type="button" onClick="{{{{q.pick}}}}" style="width: 100%; display: block; padding: 13px 18px; border: 0; border-bottom: 1px solid {RULE}; border-inline-start: 3px solid {{{{q.side}}}}; background: {{{{q.bg}}}}; font-family: inherit; text-align: start; cursor: pointer">
<span style="display: flex; align-items: baseline; justify-content: space-between; gap: 10px; margin-bottom: 4px">
<span style="font-family: 'Maghribi', serif; font-size: 19px">{{{{q.word}}}}</span>
<span style="font-size: 11px; color: {SAGE}">{{{{q.loc}}}}</span>
</span>
<span style="display: flex; align-items: center; gap: 7px">
<span style="font-size: 12.5px; color: {{{{q.srcColor}}}}">{{{{q.src}}}}</span>
<span style="font-size: 12.5px; color: {INK}">{{{{q.term}}}}</span>
<sc-if value="{{{{q.done}}}}" hint-placeholder-val="{{{{ false }}}}">
<span style="margin-inline-start: auto; font-size: 11px; color: {{{{q.doneColor}}}}">{{{{q.doneLabel}}}}</span>
</sc-if>
</span>
</button>
</sc-for>
</section>

<main style="overflow-y: auto; padding: 24px 30px 34px">
<div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 22px; margin-bottom: 18px">
<div>
<div style="font-size: 12.5px; color: {SAGE}; margin-bottom: 3px">{{{{cur.loc}}}}</div>
<h2 style="margin: 0; font-family: 'Reem Kufi', sans-serif; font-size: 23px; font-weight: 500">الوقف بعد «{{{{cur.word}}}}»</h2>
</div>
<div style="display: flex; gap: 8px; flex-shrink: 0">
<button type="button" onClick="{{{{approve}}}}" style="height: 44px; padding: 0 20px; border: 0; border-radius: 3px; background: {LAPIS}; color: {PAPER}; font-family: inherit; font-size: 14.5px; font-weight: 500; cursor: pointer">اعتمد</button>
<button type="button" onClick="{{{{reject}}}}" style="height: 44px; padding: 0 20px; border: 1px solid {CARMINE}; border-radius: 3px; background: transparent; color: {CARMINE}; font-family: inherit; font-size: 14.5px; cursor: pointer">ارفض</button>
<button type="button" onClick="{{{{skip}}}}" style="height: 44px; padding: 0 18px; border: 1px solid {RULE}; border-radius: 3px; background: transparent; color: {INK}; font-family: inherit; font-size: 14.5px; cursor: pointer">أجِّل</button>
</div>
</div>

<div style="border: 1.4px solid {LAPIS}; padding: 5px; background: {PAPER}; margin-bottom: 20px">
<div style="border: 0.8px solid {OCHRE}; padding: 20px 22px">
<div style="font-size: 12px; color: {SAGE}; margin-bottom: 9px">الآية كاملة — الكلمة الموقوف بعدها مظلّلة</div>
<p style="margin: 0; font-family: 'Maghribi', serif; font-size: 23px; line-height: 2.5; text-align: justify">
<sc-for list="{{{{cur.ayah}}}}" as="w" hint-placeholder-count="10">
<span style="background: {{{{w.bg}}}}; padding: 0 3px; border-radius: 2px">{{{{w.t}}}} </span>
</sc-for>
</p>
</div>
</div>

<div style="display: grid; grid-template-columns: minmax(0, 1fr) 330px; gap: 22px">
<section>
<h3 style="margin: 0 0 3px; font-family: 'Reem Kufi', sans-serif; font-size: 16px; font-weight: 500">نصّ الكتاب في الموضع</h3>
<p style="margin: 0 0 10px; font-size: 12px; color: {SAGE}">هذا هو ما يُحكم به — اقرأه قبل الاعتماد</p>
<p style="margin: 0 0 18px; padding: 16px 18px; background: {PAPER}; border: 1px solid {RULE}; font-size: 14.5px; line-height: 2.05; color: #353330">{{{{cur.ctx}}}}</p>

<h3 style="margin: 0 0 10px; font-family: 'Reem Kufi', sans-serif; font-size: 16px; font-weight: 500">الحكم المقترح</h3>
<div style="display: flex; align-items: center; gap: 16px; flex-wrap: wrap; padding: 15px 18px; background: {PAPER}; border: 1px solid {RULE}; border-inline-start: 3px solid {{{{cur.srcColor}}}}">
<span>
<span style="display: block; font-size: 12px; color: {SAGE}; margin-bottom: 3px">المصدر</span>
<span style="font-size: 15px">{{{{cur.srcFull}}}}</span>
</span>
<span style="width: 1px; height: 34px; background: {RULE}"></span>
<span>
<span style="display: block; font-size: 12px; color: {SAGE}; margin-bottom: 3px">المصطلح كما في الكتاب</span>
<span style="font-size: 15px">{{{{cur.term}}}}</span>
</span>
<span style="width: 1px; height: 34px; background: {RULE}"></span>
<span>
<span style="display: block; font-size: 12px; color: {SAGE}; margin-bottom: 3px">الفئة العامة</span>
<span style="display: inline-flex; align-items: center; gap: 7px">
<span style="display: inline-block; min-width: 26px; height: 20px; line-height: 20px; text-align: center; border-radius: 2px; color: {PAPER}; font-size: 11.5px; background: {{{{cur.catColor}}}}">{{{{cur.approx}}}}{{{{cur.catCode}}}}</span>
<span style="font-size: 14px">{{{{cur.catLabel}}}}</span>
</span>
</span>
<span style="margin-inline-start: auto; font-size: 12.5px; color: {SAGE}">ثقة الاستخراج: {{{{cur.conf}}}}</span>
</div>
<sc-if value="{{{{cur.isApprox}}}}" hint-placeholder-val="{{{{ true }}}}">
<p style="margin: 10px 0 0; font-size: 12.5px; line-height: 1.85; color: {CARMINE}">ردّ هذا المصطلح إلى الفئة العامة تقريبيّ. اعتمادُك هنا يخصّ الموضع وحده؛ وضبطُ المطابقة نفسها من شاشة المصطلحات يسري على كل مواضعها.</p>
</sc-if>
</section>

<aside>
<h3 style="margin: 0 0 3px; font-family: 'Reem Kufi', sans-serif; font-size: 16px; font-weight: 500">ماذا يقول غيره هنا</h3>
<p style="margin: 0 0 10px; font-size: 12px; color: {SAGE}">للاستئناس، ولا يُحتجّ به على الكتاب</p>
<div style="border-top: 1px solid {RULE}">
<sc-for list="{{{{cur.others}}}}" as="o" hint-placeholder-count="4">
<div style="display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 11px 2px; border-bottom: 1px solid {RULE}">
<span style="font-size: 13.5px; color: {{{{o.color}}}}">{{{{o.src}}}}</span>
<span style="display: inline-flex; align-items: center; gap: 7px">
<span style="font-size: 13px; color: #44423D">{{{{o.term}}}}</span>
<span style="display: inline-block; min-width: 24px; height: 19px; line-height: 19px; text-align: center; border-radius: 2px; color: {PAPER}; font-size: 11px; background: {{{{o.catColor}}}}">{{{{o.code}}}}</span>
</span>
</div>
</sc-for>
<sc-if value="{{{{cur.noOthers}}}}" hint-placeholder-val="{{{{ false }}}}">
<p style="margin: 0; padding: 13px 2px; font-size: 13px; color: {SAGE}">لا مصدر آخر عنده حكم في هذا الموضع.</p>
</sc-if>
</div>
<p style="margin: 16px 0 0; padding: 12px 14px; background: {PAPER}; border: 1px solid {RULE}; font-size: 12px; line-height: 1.85; color: {SAGE}">لا يُحسب اتفاق ولا خلاف من الفئات العامة. تسميتان لمعنى واحد تُظهران خلافاً وهمياً.</p>
</aside>
</div>
</main>
</div>'''

script=DATA+'''
class Component extends DCLogic {
  constructor(p){ super(p); this.state={i:0, acted:{}, filter:'all'}; }
  renderVals(){
    const st=this.state, cur=QUEUE[st.i]||QUEUE[0];
    const fdefs=[['all','الكلّ'],['ansari','المقصد'],['ashmuni','منار الهدى']];
    const filters=fdefs.map(([id,label])=>{
      const on=st.filter===id;
      return {label, on, bg:on?'#1E3A5F':'transparent', fg:on?'#F6F4EE':'#1C1815',
        bd:on?'#1E3A5F':'#CFC9BA', pick:()=>this.setState({filter:id})};
    });
    const queue=QUEUE.map((q,idx)=>{
      const a=st.acted[idx];
      return { word:q.word, loc:q.loc, src:SRC[q.src].n, srcColor:SRC[q.src].c, term:q.term,
        side: idx===st.i ? '#1E3A5F' : (a==='ok' ? '#2F6B5E' : a==='no' ? '#8C2F39' : 'transparent'),
        bg: idx===st.i ? '#EFECE2' : 'transparent',
        done: !!a, doneLabel: a==='ok'?'اعتُمد':a==='no'?'رُفض':'أُجّل',
        doneColor: a==='ok'?'#2F6B5E':a==='no'?'#8C2F39':'#8A857B',
        pick:()=>this.setState({i:idx}) };
    }).filter((q,idx)=> st.filter==='all' || QUEUE[idx].src===st.filter);

    const c=CAT[cur.cat];
    const act=(v)=>()=>this.setState({acted:{...st.acted,[st.i]:v},
      i: Math.min(st.i+1, QUEUE.length-1)});
    const left=QUEUE.length-Object.keys(st.acted).length;

    return {
      queue, filters,
      queueNote: '٥٬٦٩٧ موضعاً مقترحاً · ' + left + ' من هذه الدفعة بلا قرار',
      cur: {
        loc:cur.loc, word:cur.word, ctx:cur.ctx, term:cur.term+' ('+cur.sym+')',
        srcFull:SRC[cur.src].n+' — '+SRC[cur.src].s, srcColor:SRC[cur.src].c,
        catCode:c.k, catLabel:c.l, catColor:c.c,
        approx: cur.apx ? '\\u2248 ' : '', isApprox: cur.apx,
        conf: cur.conf || 'غير مسجّلة',
        ayah: cur.ayah.map((t)=>({t, bg: t===cur.word ? '#F2E3C4' : 'transparent'})),
        others: cur.others.map((o)=>({src:SRC[o.src].n, color:SRC[o.src].c,
          term:o.term, code:(o.apx?'\\u2248':'')+CAT[o.cat].k, catColor:CAT[o.cat].c})),
        noOthers: cur.others.length===0
      },
      approve: act('ok'), reject: act('no'), skip: act('later')
    };
  }
}'''
open(ROOT+'AdminReview.dc.html','w',encoding='utf-8').write(
    doc('مراجعة المواضع — جامع الوقوف', body, script, 1440, 980))
print('AdminReview written ·', len(QUEUE), 'مواضع في الطابور')
