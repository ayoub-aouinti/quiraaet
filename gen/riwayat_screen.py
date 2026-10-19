import sys, json, sqlite3
sys.path.insert(0,'gen')
from tokens import *
ROOT='/tmp/claude-0/-home-claude/3d4ae7fd-b04d-5598-b44d-3e07691c2ad4/scratchpad/w/project/'
G=json.load(open('out/page_riwayat.json',encoding='utf-8'))
con=sqlite3.connect('out/waqf.db'); con.row_factory=sqlite3.Row
RIW=[dict(r) for r in con.execute('SELECT id,name,line,region,script,word_count,has_text FROM riwayat')]
al={}
for r in con.execute('SELECT riwaya, align, COUNT(*) n FROM riwaya_words GROUP BY riwaya, align'):
    al.setdefault(r['riwaya'],{})[r['align']]=r['n']

def ar(n): return f'{n:,}'.replace(',', chr(0x066C))

def phone(rid, name, sub, col, text, font, size, has, note):
    inner = (f'''<p style="margin: 0; font-family: {font}; font-size: {size}; line-height: 2.45; text-align: justify; color: {INK}">{text}</p>'''
      if has else f'''<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 11px; height: 100%; text-align: center">
<svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="{RULE}" stroke-width="1.3" aria-hidden="true">
<rect x="4" y="3" width="16" height="18" rx="1"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>
<span style="font-family: 'Readex Pro', sans-serif; font-size: 13px; line-height: 1.85; color: #A49E92; max-width: 22ch">{note}</span></div>''')
    border = col if has else RULE
    style = 'solid' if has else 'dashed'
    tabbg = col if has else '#C9C3B6'
    return f'''
<div style="display: flex; flex-direction: column; gap: 11px">
<div style="width: 300px; height: 630px; border-radius: 26px; border: 8px solid #211D19; background: {LEAF}; overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 1px 0 {RULE}">
<div style="flex-shrink: 0; padding: 11px 13px 0; background: {PAPER}; border-bottom: 1px solid {RULE}">
<div style="display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 8px">
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 13.5px; font-weight: 600">سورة البقرة</span>
<span style="font-size: 10.5px; color: {SAGE}">الجزء الأول</span>
</div>
<div style="display: flex; gap: 2px; overflow: hidden">
<span style="flex-shrink: 0; padding: 0 9px 7px; font-size: 11px; color: {PAPER}; background: {tabbg}; border-radius: 2px 2px 0 0; padding-top: 5px">{name}</span>
<span style="flex-shrink: 0; padding: 5px 9px 7px; font-size: 11px; color: #A49E92">غيرها</span>
</div>
</div>
<div style="flex: 1; min-height: 0; padding: 11px 10px; overflow: hidden">
<div style="height: 100%; border: 1.2px {style} {border}; padding: 4px; background: {PAPER if has else LEAF}">
<div style="height: 100%; box-sizing: border-box; border: 0.7px {style} {OCHRE if has else RULE}; padding: 13px 11px; overflow: hidden">{inner}</div>
</div>
</div>
<div style="flex-shrink: 0; display: flex; height: 46px; background: {PAPER}; border-top: 1px solid {RULE}">
<span style="flex: 1; display: flex; align-items: center; justify-content: center; font-size: 10.5px; color: {col if has else '#A49E92'}; border-top: 2px solid {col if has else 'transparent'}">المصحف</span>
<span style="flex: 1; display: flex; align-items: center; justify-content: center; font-size: 10.5px; color: #A49E92">المقارنة</span>
<span style="flex: 1; display: flex; align-items: center; justify-content: center; font-size: 10.5px; color: #A49E92">الموضع</span>
</div>
</div>
<div style="width: 300px">
<div style="font-size: 14.5px; margin-bottom: 2px; color: {INK if has else '#A49E92'}">{name}</div>
<div style="font-size: 11.5px; line-height: 1.8; color: {SAGE if has else '#A49E92'}">{sub}</div>
</div>
</div>'''

cards=''
for r in RIW:
    has=bool(r['has_text']); a=al.get(r['id'],{})
    col=RIW_COLOR.get(r['id'], RULE)
    font, size = RIW_FONT[r['id']][0], '16px'
    txt = G.get(r['id'],'')[:430]
    marks = {'warsh':'وقف الهبطي في النصّ','qalun':'علامة الوقف المغربية في النصّ',
             'hafs':'رموز الوقف في النصّ','duri':'رموز الوقف في النصّ'}.get(r['id'],'')
    scr = 'خطّ مغربي' if r['id']=='warsh' else 'خطّ المجمع'
    sub=f"{r['region']} — {scr} · {ar(r['word_count'])} كلمة · {marks}"
    note=''
    cards+=phone(r['id'], r['name'], sub, col, txt, font, size, has, note)

rowsHtml=''
for r in RIW:
    has=bool(r['has_text']); a=al.get(r['id'],{})
    col=RIW_COLOR.get(r['id'], RULE)
    ex,va,un=a.get('exact',0),a.get('variant',0),a.get('unmatched',0); tot=max(1,ex+va+un)
    bar=(f'''<span style="display: flex; height: 7px; border-radius: 1px; overflow: hidden">
<span style="width: {100*ex//tot}%; background: {col}"></span>
<span style="width: {100*va//tot}%; background: {OCHRE}"></span>
<span style="width: {100*un//tot}%; background: {CARMINE}"></span></span>'''
      if has else f'<span style="display: block; height: 7px; background: #E2DED3; border-radius: 1px"></span>')
    detail=(f'مطابق {ar(ex)} · مختلف الرسم {ar(va)} · بلا مقابل {ar(un)}' if has else 'لا نصّ بعد')
    rowsHtml+=f'''
<div style="display: grid; grid-template-columns: 180px 1fr 230px; gap: 16px; align-items: center; padding: 11px 0; border-bottom: 1px solid {RULE}">
<span style="font-size: 14px; color: {INK if has else '#A49E92'}">{r['name']}</span>
{bar}
<span style="font-size: 12px; color: {SAGE}">{detail}</span>
</div>'''

body=f'''
<div dir="rtl" style="width: 1440px; height: 1060px; overflow: hidden; background: {LEAF}; color: {INK}; font-family: 'Readex Pro', sans-serif; display: flex; flex-direction: column">
<header style="flex-shrink: 0; display: flex; align-items: center; justify-content: space-between; gap: 24px; padding: 0 30px; height: 60px; background: {PAPER}; border-bottom: 1px solid {RULE}">
<a href="Landing.dc.html" style="display: flex; align-items: center; gap: 9px">
{logo_mark(23, PAPER, '#E0B266', '#E8A0A0', PAPER)}
<span style="font-family: 'Reem Kufi', sans-serif; font-size: 17px; font-weight: 600">جامع الوقوف</span></a>
<div style="display: flex; gap: 18px; font-size: 14px">
<a href="Reader.dc.html" style="color: {SAGE}">القارئ</a>
<a href="Main.dc.html" style="color: {SAGE}">الجوال</a>
<a href="AdminRiwayat.dc.html" style="color: {SAGE}">إدارة الروايات</a>
</div>
</header>

<main style="flex: 1; min-height: 0; overflow-y: auto; padding: 26px 30px 36px">
<h1 style="margin: 0 0 5px; font-family: 'Reem Kufi', sans-serif; font-size: 27px; font-weight: 500">الموضع نفسه في الروايات الأربع</h1>
<p style="margin: 0 0 24px; font-size: 14.5px; line-height: 1.9; color: {SAGE}; max-width: 84ch">هذه شاشة التطبيق نفسها، تنتقل بين الروايات. والرواية تغيّر النصّ والخطّ معاً لا الخطّ وحده: قارن رسم الكلمات في الإطارين الأولين تَرَ الفرق. وأحكام الوقف محفوظة على فهرس حفص، وتُعرض على كل رواية بمحاذاة الكلمات.</p>

<div style="display: flex; gap: 24px; margin-bottom: 30px">{cards}</div>

<section style="background: {PAPER}; border: 1px solid {RULE}; padding: 20px 24px">
<h2 style="margin: 0 0 3px; font-family: 'Reem Kufi', sans-serif; font-size: 18px; font-weight: 500">محاذاة كل رواية على فهرس حفص</h2>
<p style="margin: 0 0 13px; font-size: 12.5px; color: {SAGE}">الكلمة التي لا مقابل لها تبقى بلا علامة، ولا يُخمَّن لها موضع.</p>
{rowsHtml}
</section>
</main>
</div>'''

open(ROOT+'Riwayat.dc.html','w',encoding='utf-8').write(
    doc('الروايات الأربع — جامع الوقوف', body,
        'class Component extends DCLogic { renderVals(){ return {}; } }', 1440, 1060))
print('Riwayat.dc.html written')
