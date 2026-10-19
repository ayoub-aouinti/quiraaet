import sys, json, sqlite3
sys.path.insert(0,'gen')
from tokens import *
ROOT='/tmp/claude-0/-home-claude/3d4ae7fd-b04d-5598-b44d-3e07691c2ad4/scratchpad/w/project/'
con=sqlite3.connect('out/waqf.db'); con.row_factory=sqlite3.Row
stats={r['source']:dict(r) for r in con.execute('''SELECT source, COUNT(*) n,
  SUM(CASE WHEN status='proposed' THEN 1 ELSE 0 END) prop,
  SUM(approx) apx FROM rulings GROUP BY source''')}
# مواضع مقترحة حقيقية للمراجعة
q=list(con.execute('''SELECT w.sura_name,w.sura,w.ayah,w.text,r.source,r.symbol,r.term,
  r.category,r.approx,r.confidence,r.context,r.seq
  FROM rulings r JOIN words w ON w.seq=r.seq
  WHERE r.status='proposed' AND r.context IS NOT NULL AND length(r.context)>60
  ORDER BY r.seq LIMIT 7'''))
QUEUE=[{'loc':f"{x['sura_name']} {x['sura']}:{x['ayah']}",'word':x['text'],'src':x['source'],
        'sym':x['symbol'],'term':x['term'],'cat':x['category'],'apx':bool(x['approx']),
        'conf':x['confidence'] or '','ctx':(x['context'] or '').strip()[:260],'seq':x['seq']} for x in q]
# ما يقوله غيره في الموضع نفسه
others={}
for it in QUEUE:
    o=list(con.execute('''SELECT r.source,r.symbol,r.term,r.category,r.approx,r.status
      FROM rulings r WHERE r.seq=? AND r.source<>?''',(it['seq'],it['src'])))
    others[it['seq']]=[{'src':x['source'],'sym':x['symbol'],'term':x['term'],'cat':x['category'],
                        'apx':bool(x['approx']),'st':x['status']} for x in o]

TOT=sum(v['n'] for v in stats.values()); PROP=sum(v['prop'] or 0 for v in stats.values())
DATA=('const STATS='+json.dumps(stats,ensure_ascii=False)+';\n'
      'const QUEUE='+json.dumps(QUEUE,ensure_ascii=False,separators=(',',':'))+';\n'
      'const OTHERS='+json.dumps(others,ensure_ascii=False,separators=(',',':'))+';\n'
      'const SRC='+json.dumps({k:{'n':v[0],'c':v[1],'s':v[2]} for k,v in SRC.items()},ensure_ascii=False)+';\n'
      'const CAT='+json.dumps({k:{'l':v[0],'k':v[1],'c':v[2]} for k,v in CAT.items()},ensure_ascii=False)+';\n'
      f'const TOT={TOT}; const PROP={PROP};')

def shell(active, inner):
    nav=''
    for name,href in [('اللوحة','Admin.dc.html'),('المراجعة','AdminReview.dc.html'),
                      ('المصادر','Admin.dc.html'),('المصطلحات','Admin.dc.html'),('السجلّ','Admin.dc.html')]:
        on=name==active
        style=(f'background: {LAPIS}; color: {PAPER}' if on else f'color: #D8D3C7')
        tag='div' if on else 'a'; h='' if on else f' href="{href}"'
        nav+=f'<{tag}{h} style="display: block; padding: 10px 14px; border-radius: 3px; font-size: 14px; {style}">{name}</{tag}>'
    return f'''
<div dir="rtl" style="width: 1440px; height: 980px; overflow: hidden; background: {LEAF}; color: {INK}; font-family: 'Readex Pro', sans-serif; display: grid; grid-template-columns: 222px minmax(0, 1fr)">
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
<main style="overflow-y: auto">{inner}</main>
</div>'''

# ======== لوحة المؤشرات ========
def srow(k, v):
    st = stats.get(k) or {}
    n = st.get('n', 0); pr = st.get('prop') or 0; ax = st.get('apx') or 0
    pct = min(100, int(100 * n / 9829)) if n else 0
    DASH = chr(0x2014)
    sep = chr(0x066C)
    ar = lambda x: format(x, ',').replace(',', sep)
    return f"""
<div style="display: grid; grid-template-columns: 14px 190px 1fr 90px 92px 108px; gap: 14px; align-items: center; padding: 13px 0; border-bottom: 1px solid {RULE}">
<span style="width: 10px; height: 10px; border-radius: 5px; background: {v[1]}"></span>
<span style="font-size: 14.5px">{v[0]} <span style="color: {SAGE}; font-size: 12.5px">— {v[2]}</span></span>
<span style="height: 7px; background: #E2DED3; border-radius: 1px; overflow: hidden">
<span style="display: block; height: 100%; width: {pct}%; background: {v[1]}"></span></span>
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 15px">{ar(n)}</span>
<span style="font-size: 13px; color: {CARMINE if pr else SAGE}">{ar(pr) if pr else DASH}</span>
<span style="font-size: 13px; color: {SAGE}">{ar(ax)}</span>
</div>"""

src_rows = ''.join(srow(k, v) for k, v in SRC.items())

inner_dash=f'''
<div style="padding: 26px 32px 40px">
<div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; margin-bottom: 24px">
<div>
<h1 style="margin: 0 0 4px; font-family: 'Reem Kufi', sans-serif; font-size: 27px; font-weight: 500">اللوحة</h1>
<p style="margin: 0; font-size: 14px; color: {SAGE}">حالة الجامع اليوم</p>
</div>
<a href="AdminReview.dc.html" style="display: inline-flex; align-items: center; height: 44px; padding: 0 20px; border-radius: 3px; background: {LAPIS}; color: {PAPER}; font-size: 14.5px; font-weight: 500">ابدأ المراجعة</a>
</div>

<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1px; background: {RULE}; border: 1px solid {RULE}; margin-bottom: 30px">
<div style="background: {PAPER}; padding: 18px 20px">
<div style="font-size: 13px; color: {SAGE}; margin-bottom: 6px">أحكام في الجامع</div>
<div style="font-family: 'Reem Kufi', sans-serif; font-size: 30px">٣١٬١٢٩</div>
<div style="font-size: 12px; color: {SAGE}; margin-top: 4px">على ٧٧٬٤٣٦ كلمة</div>
</div>
<div style="background: {PAPER}; padding: 18px 20px">
<div style="font-size: 13px; color: {SAGE}; margin-bottom: 6px">معتمد</div>
<div style="font-family: 'Reem Kufi', sans-serif; font-size: 30px; color: {LAPIS}">٢٥٬٤٣٢</div>
<div style="font-size: 12px; color: {SAGE}; margin-top: 4px">منقول من مصدره مباشرة</div>
</div>
<div style="background: {PAPER}; padding: 18px 20px">
<div style="font-size: 13px; color: {SAGE}; margin-bottom: 6px">مقترح ينتظر المراجعة</div>
<div style="font-family: 'Reem Kufi', sans-serif; font-size: 30px; color: {CARMINE}">٥٬٦٩٧</div>
<div style="font-size: 12px; color: {SAGE}; margin-top: 4px">مستخرج آلياً من الكتب</div>
</div>
<div style="background: {PAPER}; padding: 18px 20px">
<div style="font-size: 13px; color: {SAGE}; margin-bottom: 6px">مطابقات مصطلحات مراجَعة</div>
<div style="font-family: 'Reem Kufi', sans-serif; font-size: 30px; color: {OCHRE}">٠ / ٤٠</div>
<div style="font-size: 12px; color: {SAGE}; margin-top: 4px">لم يبدأ ضبط المعجم بعد</div>
</div>
</div>

<section style="background: {PAPER}; border: 1px solid {RULE}; padding: 20px 24px 8px; margin-bottom: 26px">
<h2 style="margin: 0 0 3px; font-family: 'Reem Kufi', sans-serif; font-size: 18px; font-weight: 500">المصادر</h2>
<p style="margin: 0 0 12px; font-size: 13px; color: {SAGE}">العمود الأحمر: ما ينتظر المراجعة. والأخير: مطابقات تقريبية للفئة العامة.</p>
<div style="display: grid; grid-template-columns: 14px 190px 1fr 90px 92px 108px; gap: 14px; padding-bottom: 8px; border-bottom: 1px solid {RULE}; font-size: 12px; color: {SAGE}">
<span></span><span>المصدر</span><span></span><span>المواضع</span><span>مقترح</span><span>تقريبية</span>
</div>
{src_rows}
</section>

<div style="display: grid; grid-template-columns: minmax(0, 1fr) 380px; gap: 22px">
<section style="background: {PAPER}; border: 1px solid {RULE}; padding: 20px 24px">
<h2 style="margin: 0 0 12px; font-family: 'Reem Kufi', sans-serif; font-size: 18px; font-weight: 500">ما يحتاج قراراً</h2>
<div style="display: flex; flex-direction: column; gap: 11px">
<a href="AdminReview.dc.html" style="display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 13px 15px; border-inline-start: 3px solid {CARMINE}; background: {LEAF}">
<span><span style="display: block; font-size: 14.5px; margin-bottom: 2px">٥٬٦٩٧ موضعاً مقترحاً من كتابين</span>
<span style="display: block; font-size: 12.5px; color: {SAGE}">المقصد ومنار الهدى — استُخرجت آلياً ولم تُعتمد</span></span>
<span style="font-size: 13px; color: {LAPIS}">راجِع</span></a>
<a href="Admin.dc.html" style="display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 13px 15px; border-inline-start: 3px solid {OCHRE}; background: {LEAF}">
<span><span style="display: block; font-size: 14.5px; margin-bottom: 2px">٤٠ مصطلحاً بلا مطابقة مراجَعة</span>
<span style="display: block; font-size: 12.5px; color: {SAGE}">ضبطُ واحدٍ منها يسري على كل مواضعه</span></span>
<span style="font-size: 13px; color: {LAPIS}">اضبط</span></a>
<a href="Admin.dc.html" style="display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 13px 15px; border-inline-start: 3px solid {SAGE}; background: {LEAF}">
<span><span style="display: block; font-size: 14.5px; margin-bottom: 2px">١٨ قيمة غير مفهومة في ملف الترقيم</span>
<span style="display: block; font-size: 12.5px; color: {SAGE}">تحتاج الرجوع إلى المطبوع</span></span>
<span style="font-size: 13px; color: {LAPIS}">افتح</span></a>
</div>
</section>
<section style="background: {PAPER}; border: 1px solid {RULE}; padding: 20px 22px">
<h2 style="margin: 0 0 12px; font-family: 'Reem Kufi', sans-serif; font-size: 18px; font-weight: 500">ثغرات معلومة</h2>
<ul style="margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 12px; font-size: 13px; line-height: 1.8; color: #44423D">
<li style="padding-inline-start: 13px; border-inline-start: 2px solid {RULE}">علامة «لا» غائبة من مصدر رموز المصحف — النصّ المستعمل فيه ست علامات فقط.</li>
<li style="padding-inline-start: 13px; border-inline-start: 2px solid {RULE}">١٢ وقفة هبطية من ٩٬٨٤١ لم تُسنَد، وقعت في مواضع اختلاف ورش عن حفص.</li>
<li style="padding-inline-start: 13px; border-inline-start: 2px solid {RULE}">نحو ١٢ ألف موضع ملتبس في الكتابين لم يُحسم بعد.</li>
<li style="padding-inline-start: 13px; border-inline-start: 2px solid {RULE}">٩ مواضع بلا ترتيب داخل الآية — مواضع الفصل والوصل المعروفة.</li>
</ul>
</section>
</div>
</div>'''

open(ROOT+'Admin.dc.html','w',encoding='utf-8').write(
    doc('لوحة الإدارة — جامع الوقوف', shell('اللوحة', inner_dash),
        'class Component extends DCLogic { renderVals(){ return {}; } }', 1440, 980))
print('Admin written · أحكام', TOT, '· مقترح', PROP)
json.dump({'DATA':DATA}, open('out/_admin_data.json','w',encoding='utf-8'))
