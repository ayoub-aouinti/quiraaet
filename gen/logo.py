import sys
sys.path.insert(0,'gen')
from tokens import *
ROOT='/tmp/claude-0/-home-claude/3d4ae7fd-b04d-5598-b44d-3e07691c2ad4/scratchpad/w/project/'

def mark(size, c1, c2, c3, rule, gap=True, sw=None):
    """العلامة: فجوة في السطر، وفوقها ثلاث نقاط — ∴ المعانقة.
    النقاط الثلاث لعائلات المصادر: الكتب، المصاحف المشرقية، المغاربية."""
    s=size; u=s/32.0
    r=2.55*u                       # نصف قطر النقطة
    y_rule=22*u; x0=4*u; x1=28*u
    gw=7*u                         # عرض الفجوة
    cx=16*u
    stroke=sw if sw else 1.9*u
    if gap:
        line=(f'<path d="M{x0} {y_rule} H{cx-gw/2}" stroke="{rule}" stroke-width="{stroke}" stroke-linecap="round"/>'
              f'<path d="M{cx+gw/2} {y_rule} H{x1}" stroke="{rule}" stroke-width="{stroke}" stroke-linecap="round"/>')
    else:
        line=f'<path d="M{x0} {y_rule} H{x1}" stroke="{rule}" stroke-width="{stroke}" stroke-linecap="round"/>'
    return (f'<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" fill="none" aria-hidden="true">'
            f'<circle cx="{cx}" cy="{8.5*u}" r="{r}" fill="{c1}"/>'
            f'<circle cx="{cx-5.4*u}" cy="{15.2*u}" r="{r}" fill="{c2}"/>'
            f'<circle cx="{cx+5.4*u}" cy="{15.2*u}" r="{r}" fill="{c3}"/>'
            f'{line}</svg>')

C1,C2,C3 = LAPIS, OCHRE, CARMINE

def tile(label, note, inner, bg=PAPER, pad='26px', h=None):
    hs=f'height: {h}; ' if h else ''
    return f'''<figure style="margin: 0">
<div style="background: {bg}; border: 1px solid {RULE}; {hs}padding: {pad}; display: flex; align-items: center; justify-content: center">{inner}</div>
<figcaption style="margin-top: 9px; font-size: 13px; color: {INK}">{label}
<span style="display: block; font-size: 11.5px; color: {SAGE}; margin-top: 2px">{note}</span></figcaption>
</figure>'''

def lockup(size, col, c1, c2, c3, rule, gap=True):
    return (f'<span style="display: inline-flex; align-items: center; gap: {size*0.34}px">'
            f'{mark(size, c1, c2, c3, rule, gap)}'
            f'<span style="font-family: \'Reem Kufi\', sans-serif; font-size: {size*0.74}px; '
            f'font-weight: 600; letter-spacing: 0.4px; color: {col}; line-height: 1">جامع الوقوف</span></span>')

sizes=''.join(f'''<div style="display: flex; flex-direction: column; align-items: center; gap: 8px">
{mark(n, C1, C2, C3, INK)}
<span style="font-size: 11.5px; color: {SAGE}">{n}px</span></div>''' for n in [96,56,32,20,16])

body=f'''
<div dir="rtl" style="width: 1440px; min-height: 1180px; background: {LEAF}; color: {INK}; font-family: 'Readex Pro', sans-serif; padding: 34px 40px 44px; box-sizing: border-box">

<header style="margin-bottom: 30px">
<h1 style="margin: 0 0 6px; font-family: 'Reem Kufi', sans-serif; font-size: 28px; font-weight: 500">الشعار</h1>
<p style="margin: 0; font-size: 14.5px; line-height: 1.9; color: {SAGE}; max-width: 90ch">الوقف فجوةٌ في السطر، وفوقها علامة. فالشعار سطرٌ مقطوع عند موضع، وفوق القطع ثلاث نقاط على هيئة ∴ — وهي علامة المعانقة في المصحف، رمزٌ قرآني لا يشبه غيره. والنقاط الثلاث ألوانها ألوان عائلات المصادر الثلاث في الجامع: كتب الوقف، والمصاحف المشرقية، والمغاربية.</p>
</header>

<div style="display: grid; grid-template-columns: 330px minmax(0, 1fr); gap: 26px; margin-bottom: 26px">
<div style="background: {PAPER}; border: 1px solid {RULE}; display: flex; align-items: center; justify-content: center; padding: 40px">
{mark(168, C1, C2, C3, INK)}
</div>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px">
{tile('الشعار الكامل','على الورق', lockup(44, INK, C1, C2, C3, INK), PAPER, '30px 24px', '126px')}
{tile('أحادي اللون','للطباعة والختم', lockup(44, INK, INK, INK, INK, INK), PAPER, '30px 24px', '126px')}
{tile('معكوس','على الداكن', lockup(44, PAPER, '#7FA8D4', '#E0B266', '#E08A8A', PAPER), '#211D19', '30px 24px', '126px')}
{tile('العلامة وحدها','حين يضيق المكان', mark(56, C1, C2, C3, INK), PAPER, '26px', '126px')}
{tile('بلا فجوة','للتطريز والحفر', mark(56, INK, INK, INK, INK, False), PAPER, '26px', '126px')}
{tile('على المُغرة','خلفية ملوّنة', mark(56, PAPER, PAPER, PAPER, PAPER), OCHRE, '26px', '126px')}
</div>
</div>

<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 26px; margin-bottom: 26px">

<section style="background: {PAPER}; border: 1px solid {RULE}; padding: 22px 24px">
<h2 style="margin: 0 0 4px; font-family: 'Reem Kufi', sans-serif; font-size: 17px; font-weight: 500">المقاسات</h2>
<p style="margin: 0 0 18px; font-size: 12px; color: {SAGE}">تُقرأ حتى ١٦ بكسل</p>
<div style="display: flex; align-items: flex-end; justify-content: space-between; gap: 10px">{sizes}</div>
</section>

<section style="background: {PAPER}; border: 1px solid {RULE}; padding: 22px 24px">
<h2 style="margin: 0 0 4px; font-family: 'Reem Kufi', sans-serif; font-size: 17px; font-weight: 500">أيقونة التطبيق</h2>
<p style="margin: 0 0 18px; font-size: 12px; color: {SAGE}">iOS وأندرويد</p>
<div style="display: flex; align-items: center; gap: 18px">
<div style="width: 92px; height: 92px; border-radius: 21px; background: {PAPER}; border: 1px solid {RULE}; display: flex; align-items: center; justify-content: center">{mark(58, C1, C2, C3, INK)}</div>
<div style="width: 92px; height: 92px; border-radius: 21px; background: {LAPIS}; display: flex; align-items: center; justify-content: center">{mark(58, PAPER, '#E0B266', '#E8A0A0', PAPER)}</div>
</div>
</section>

<section style="background: {PAPER}; border: 1px solid {RULE}; padding: 22px 24px">
<h2 style="margin: 0 0 4px; font-family: 'Reem Kufi', sans-serif; font-size: 17px; font-weight: 500">في الموقع</h2>
<p style="margin: 0 0 18px; font-size: 12px; color: {SAGE}">شريط علوي</p>
<div style="border: 1px solid {RULE}">
<div style="display: flex; align-items: center; justify-content: space-between; gap: 14px; padding: 12px 15px; background: {PAPER}; border-bottom: 1px solid {RULE}">
{lockup(26, INK, C1, C2, C3, INK)}
<span style="display: flex; gap: 13px; font-size: 11.5px; color: {SAGE}"><span>المصحف</span><span>المصادر</span></span>
</div>
<div style="height: 54px; background: {LEAF}"></div>
</div>
</section>

<section style="background: {PAPER}; border: 1px solid {RULE}; padding: 22px 24px">
<h2 style="margin: 0 0 4px; font-family: 'Reem Kufi', sans-serif; font-size: 17px; font-weight: 500">الهامش الآمن</h2>
<p style="margin: 0 0 18px; font-size: 12px; color: {SAGE}">لا يقترب منه شيء</p>
<div style="display: flex; justify-content: center">
<div style="position: relative; padding: 23px; border: 1px dashed {RULE}">
{mark(74, C1, C2, C3, INK)}
<span style="position: absolute; top: 5px; right: 6px; font-size: 10.5px; color: {SAGE}">نصف ارتفاع العلامة</span>
</div>
</div>
</section>
</div>

<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 26px">
<section style="background: {PAPER}; border: 1px solid {RULE}; padding: 22px 24px">
<h2 style="margin: 0 0 11px; font-family: 'Reem Kufi', sans-serif; font-size: 17px; font-weight: 500">لماذا هذا الشكل</h2>
<ul style="margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 11px; font-size: 13px; line-height: 1.85; color: #44423D">
<li style="padding-inline-start: 13px; border-inline-start: 2px solid {LAPIS}">الفجوة في السطر هي الوقف نفسه، لا رمزاً له.</li>
<li style="padding-inline-start: 13px; border-inline-start: 2px solid {OCHRE}">النقاط الثلاث ∴ علامة المعانقة، أخصّ ما في الباب.</li>
<li style="padding-inline-start: 13px; border-inline-start: 2px solid {CARMINE}">ألوانها ألوان عائلات المصادر، فالجمع ظاهر في الشكل.</li>
<li style="padding-inline-start: 13px; border-inline-start: 2px solid {SAGE}">هندسيّ بلا منحنيات، فيثبت عند التصغير ولا ينطمس.</li>
</ul>
</section>

<section style="background: {PAPER}; border: 1px solid {RULE}; padding: 22px 24px">
<h2 style="margin: 0 0 11px; font-family: 'Reem Kufi', sans-serif; font-size: 17px; font-weight: 500">ما لا يُفعل</h2>
<ul style="margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 10px; font-size: 13px; line-height: 1.8; color: #44423D">
<li>لا يُمال ولا يُدوَّر — السطر أفقيّ لأنه سطر.</li>
<li>لا تُردم الفجوة، فهي معنى الشعار.</li>
<li>لا يُستبدل لون نقطة بلون خارج اللوحة.</li>
<li>لا يُوضع على صورة ذات تفاصيل، بل على لون صامت.</li>
</ul>
</section>

<section style="background: {PAPER}; border: 1px solid {RULE}; padding: 22px 24px">
<h2 style="margin: 0 0 11px; font-family: 'Reem Kufi', sans-serif; font-size: 17px; font-weight: 500">الألوان والخطّ</h2>
<div style="display: flex; gap: 9px; margin-bottom: 14px">
<span style="flex: 1"><span style="display: block; height: 42px; background: {LAPIS}"></span><span style="display: block; font-size: 11px; color: {SAGE}; margin-top: 5px">لازوردي {LAPIS}</span></span>
<span style="flex: 1"><span style="display: block; height: 42px; background: {OCHRE}"></span><span style="display: block; font-size: 11px; color: {SAGE}; margin-top: 5px">مُغرة {OCHRE}</span></span>
<span style="flex: 1"><span style="display: block; height: 42px; background: {CARMINE}"></span><span style="display: block; font-size: 11px; color: {SAGE}; margin-top: 5px">قرمز {CARMINE}</span></span>
<span style="flex: 1"><span style="display: block; height: 42px; background: {INK}"></span><span style="display: block; font-size: 11px; color: {SAGE}; margin-top: 5px">حبر {INK}</span></span>
</div>
<p style="margin: 0; font-size: 13px; line-height: 1.85; color: #44423D">الاسم بخطّ <b>Reem Kufi</b> وزن ٦٠٠، وهو كوفيّ هندسيّ يوافق هندسة العلامة، وعليه تُكتب عناوين السور في المصاحف.</p>
</section>
</div>
</div>'''

open(ROOT+'Logo.dc.html','w',encoding='utf-8').write(
  doc('الشعار — جامع الوقوف', body,
      'class Component extends DCLogic { renderVals(){ return {}; } }', 1440, 1180))
print('Logo.dc.html written')
