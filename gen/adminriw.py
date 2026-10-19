import sys, json, sqlite3
sys.path.insert(0,'gen')
from tokens import *
ROOT='/tmp/claude-0/-home-claude/3d4ae7fd-b04d-5598-b44d-3e07691c2ad4/scratchpad/w/project/'
con=sqlite3.connect('out/waqf.db'); con.row_factory=sqlite3.Row
RIW=[dict(r) for r in con.execute('SELECT id,name,line,region,script,word_count,has_text FROM riwayat')]
al={}
for r in con.execute("SELECT riwaya, align, COUNT(*) n FROM riwaya_words GROUP BY riwaya, align"):
    al.setdefault(r['riwaya'],{})[r['align']]=r['n']

nav=''
for name,href in [('اللوحة','Admin.dc.html'),('المراجعة','AdminReview.dc.html'),
                  ('الروايات','AdminRiwayat.dc.html'),('المصطلحات','Admin.dc.html'),('السجلّ','Admin.dc.html')]:
    on=name=='الروايات'
    style=(f'background: {LAPIS}; color: {PAPER}' if on else 'color: #D8D3C7')
    tag='div' if on else 'a'; h='' if on else f' href="{href}"'
    nav+=f'<{tag}{h} style="display: block; padding: 10px 14px; border-radius: 3px; font-size: 14px; {style}">{name}</{tag}>'

def ar(n): return f'{n:,}'.replace(',', chr(0x066C))

cards=''
for r in RIW:
    has=bool(r['has_text']); a=al.get(r['id'],{})
    col='#2F6B5E' if r['id']=='warsh' else ('#1E3A5F' if r['id']=='hafs' else RULE)
    ex,va,un=a.get('exact',0),a.get('variant',0),a.get('unmatched',0)
    tot=max(1,ex+va+un)
    if has:
        bar=f'''<div style="display: flex; height: 8px; border-radius: 1px; overflow: hidden; margin: 12px 0 7px">
<span style="width: {100*ex//tot}%; background: {col}"></span>
<span style="width: {100*va//tot}%; background: {OCHRE}"></span>
<span style="width: {100*un//tot}%; background: {CARMINE}"></span></div>
<div style="display: flex; gap: 15px; font-size: 12px; color: {SAGE}">
<span>مطابق {ar(ex)}</span><span>مختلف الرسم {ar(va)}</span><span>بلا مقابل {ar(un)}</span></div>'''
        act=f'<span style="font-size: 13px; color: {SAGE}">النصّ محمّل</span>'
    else:
        bar=f'''<p style="margin: 12px 0 0; font-size: 13px; line-height: 1.85; color: {SAGE}">لا نصّ بعد. ارفع مصحف الرواية (docx أو pdf)، فتُحاذى كلماته على فهرس حفص وتظهر عليه أحكام الوقف.</p>'''
        act=f'<button type="button" style="height: 38px; padding: 0 16px; border: 1px solid {LAPIS}; border-radius: 3px; background: transparent; color: {LAPIS}; font-family: inherit; font-size: 13.5px; cursor: pointer">ارفع النصّ</button>'
    cards+=f'''
<div style="background: {PAPER}; border: 1px solid {RULE}; border-top: 3px solid {col}; padding: 19px 21px">
<div style="display: flex; align-items: flex-start; justify-content: space-between; gap: 14px">
<div>
<div style="font-family: 'Reem Kufi', sans-serif; font-size: 19px; margin-bottom: 3px">{r['name']}</div>
<div style="font-size: 12.5px; color: {SAGE}">{r['line']} · {r['region']} · رسم {r['script']}</div>
</div>
<div style="text-align: start; flex-shrink: 0">
<div style="font-family: 'Reem Kufi', sans-serif; font-size: 20px">{ar(r['word_count']) if has else '—'}</div>
<div style="font-size: 11.5px; color: {SAGE}">كلمة</div>
</div>
</div>
{bar}
<div style="margin-top: 14px; padding-top: 12px; border-top: 1px solid {RULE}; display: flex; justify-content: flex-end">{act}</div>
</div>'''

body=f'''
<div dir="rtl" style="width: 1440px; height: 980px; overflow: hidden; background: {LEAF}; color: {INK}; font-family: 'Readex Pro', sans-serif; display: grid; grid-template-columns: 222px minmax(0, 1fr)">
<aside style="background: #211D19; padding: 20px 14px; display: flex; flex-direction: column; gap: 5px">
<div style="display: flex; align-items: center; gap: 9px; padding: 0 6px 18px">
{logo_mark(22, PAPER, '#E0B266', '#E8A0A0', PAPER)}
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 16px; font-weight: 600; color: {PAPER}">جامع الوقوف</span></div>
<div style="font-size: 11px; color: #8A857B; padding: 0 8px 7px">الإدارة</div>
{nav}
<div style="margin-top: auto; padding: 13px 8px 0; border-top: 1px solid #38322B">
<div style="font-size: 13px; color: {PAPER}">د. المراجع</div>
<div style="font-size: 11.5px; color: #8A857B">محقّق — صلاحية الاعتماد</div></div>
</aside>

<main style="overflow-y: auto; padding: 26px 32px 40px">
<h1 style="margin: 0 0 4px; font-family: 'Reem Kufi', sans-serif; font-size: 27px; font-weight: 500">الروايات</h1>
<p style="margin: 0 0 22px; font-size: 14px; line-height: 1.9; color: {SAGE}; max-width: 76ch">الرواية نصٌّ مستقلّ لا طبقة عرض: يختلف رسمها وعدّ آيها وعدد كلماتها. ولذلك لكل رواية جدول كلماتها، ويُربط بفهرس حفص المرجعي بمحاذاة، فتُعرض أحكام الوقف على أي رواية. والكلمة التي لا مقابل لها تبقى بلا علامة، ولا يُخمَّن لها موضع.</p>

<div style="display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin-bottom: 26px">{cards}</div>

<section style="background: {PAPER}; border: 1px solid {RULE}; padding: 20px 24px">
<h2 style="margin: 0 0 11px; font-family: 'Reem Kufi', sans-serif; font-size: 18px; font-weight: 500">كيف يُستورَد مصحف رواية</h2>
<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 1px; background: {RULE}; border: 1px solid {RULE}">
<div style="background: {PAPER}; padding: 16px 18px">
<div style="font-size: 14.5px; margin-bottom: 5px">١ — رفع الملف</div>
<div style="font-size: 12.5px; line-height: 1.85; color: {SAGE}">docx أو pdf. المصاحف المطبوعة كثيراً ما تستعمل ترميز خطّ خاصّاً.</div></div>
<div style="background: {PAPER}; padding: 16px 18px">
<div style="font-size: 14.5px; margin-bottom: 5px">٢ — ردّ الترميز</div>
<div style="font-size: 12.5px; line-height: 1.85; color: {SAGE}">تُستنبط خريطة الحروف المُزاحة من الملف نفسه بمقابلته على نصّ معلوم.</div></div>
<div style="background: {PAPER}; padding: 16px 18px">
<div style="font-size: 14.5px; margin-bottom: 5px">٣ — المحاذاة</div>
<div style="font-size: 12.5px; line-height: 1.85; color: {SAGE}">تُربط كل كلمة بمقابلها في فهرس حفص، وتُصنَّف: مطابق، مختلف الرسم، بلا مقابل.</div></div>
<div style="background: {PAPER}; padding: 16px 18px">
<div style="font-size: 14.5px; margin-bottom: 5px">٤ — المراجعة</div>
<div style="font-size: 12.5px; line-height: 1.85; color: {SAGE}">يُعرض ما لم يُطابَق على متخصص قبل نشر الرواية للقرّاء.</div></div>
</div>
</section>
</main>
</div>'''

open(ROOT+'AdminRiwayat.dc.html','w',encoding='utf-8').write(
    doc('الروايات — جامع الوقوف', body, 'class Component extends DCLogic { renderVals(){ return {}; } }', 1440, 980))
print('AdminRiwayat written')
