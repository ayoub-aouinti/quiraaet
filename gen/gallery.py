import sys, json
sys.path.insert(0,'gen')
from tokens import *
ROOT='/tmp/claude-0/-home-claude/3d4ae7fd-b04d-5598-b44d-3e07691c2ad4/scratchpad/w/project/'
G=json.load(open('out/page_gallery.json',encoding='utf-8'))

def frame(txt, font, size, label, sub, col, h=258):
    return f'''
<figure style="margin: 0">
<div style="border: 1.3px solid {col}; padding: 5px; background: {PAPER}">
<div style="border: 0.7px solid {OCHRE}; padding: 14px 13px; height: {h}px; overflow: hidden">
<p style="margin: 0; font-family: {font}; font-size: {size}; line-height: 2.35; text-align: justify; color: {INK}">{txt}</p>
</div>
</div>
<figcaption style="margin-top: 9px; font-size: 13px; color: {INK}">{label}
<span style="display: block; font-size: 11.5px; color: {SAGE}; margin-top: 2px">{sub}</span></figcaption>
</figure>'''

gal = ''.join(frame(g['warsh'][:620], "'Maghribi', serif", '17px', g['label'],
                    'ورش عن نافع — خطّ مغربي', '#2F6B5E') for g in G)

pair = (frame(G[1]['warsh'][:540], "'Maghribi', serif", '18px',
              'ورش عن نافع', 'المصحف المحمدي — وقف الهبطي في النصّ', '#2F6B5E', 236)
      + frame(G[1]['hafs'][:540], "'Amiri Quran', serif", '19px',
              'حفص عن عاصم', 'الرسم العثماني — رموز الوقف في النصّ', '#1E3A5F', 236))

pending = ''.join(f'''
<figure style="margin: 0">
<div style="border: 1.3px dashed {RULE}; padding: 5px; background: {LEAF}">
<div style="border: 0.7px dashed {RULE}; padding: 14px 13px; height: 236px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 9px; text-align: center">
<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="{RULE}" stroke-width="1.4" aria-hidden="true">
<rect x="4" y="3" width="16" height="18" rx="1"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>
<span style="font-size: 13px; color: #A49E92; line-height: 1.8">ينتظر النصّ</span>
</div></div>
<figcaption style="margin-top: 9px; font-size: 13px; color: #A49E92">{n}
<span style="display: block; font-size: 11.5px; color: #A49E92; margin-top: 2px">{s}</span></figcaption>
</figure>''' for n,s in [('قالون عن نافع','تونس وليبيا'),('الدوري عن أبي عمرو','السودان والقرن الأفريقي')])

SEC = f'''<section style="max-width: 1180px; margin: 92px auto 0; padding: 0 40px">
<h2 style="margin: 0 0 8px; font-family: 'Reem Kufi', sans-serif; font-size: 29px; font-weight: 500">الصفحة كما طُبعت</h2>
<p style="margin: 0 0 30px; font-size: 15.5px; line-height: 1.9; color: {SAGE}; max-width: 62ch">لا نعيد صفّ المصحف ولا نغيّر رسمه. تُعرض الصفحة بنصّها وخطّها كما في مصحفها، وعلامات الوقف فيها من أصل النصّ لا مضافة فوقه.</p>
<div style="display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 26px">{gal}</div>
</section>

<section style="max-width: 1180px; margin: 84px auto 0; padding: 0 40px">
<h2 style="margin: 0 0 8px; font-family: 'Reem Kufi', sans-serif; font-size: 29px; font-weight: 500">الموضع نفسه في روايتين</h2>
<p style="margin: 0 0 30px; font-size: 15.5px; line-height: 1.9; color: {SAGE}; max-width: 62ch">الرواية تغيّر الرسم والخطّ معاً. هاتان صفحتان متقابلتان من المصحف نفسه: يسار الصفحة ويمينها حرفٌ واحد، والفرق في الرسم ظاهر للعين.</p>
<div style="display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 22px">{pair}{pending}</div>
</section>

'''

s=open('gen/landing.py',encoding='utf-8').read()
marker = '''<section style="max-width: 1180px; margin: 92px auto 0; padding: 0 40px">
<h2 style="margin: 0 0 14px; font-family: \\'Reem Kufi\\', sans-serif; font-size: 29px; font-weight: 500">ما في الجامع</h2>'''
marker = marker.replace("\\'", "'")
assert marker in s, 'المرساة غير موجودة'
s = s.replace(marker, SEC.replace('{','{{').replace('}','}}').replace('{{{{','{').replace('}}}}','}') + marker)
open('gen/landing.py','w',encoding='utf-8').write(s)
print('ok')
