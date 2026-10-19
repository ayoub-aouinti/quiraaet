FONT = '/_blob/484c9509b2aaba89df67d9f5aedb0554'
FONT_QALUN = '/_blob/3a06ceb654931132e350f516680cab01'
FONT_DURI  = '/_blob/b7c5b2d64d55afa0ac600a6447761299'
FONT_HAFS  = '/_blob/9ef7d8b90d5aec353ba80e54e5cfbb12'

# خطّ كل رواية: خطوط المجمع للمشرقية، والخطّ المغربي للمصحف المحمدي
RIW_FONT = {
    'hafs':  ("'UthHafs', serif",   '25px', '21px'),
    'warsh': ("'Maghribi', serif",  '25px', '20px'),
    'qalun': ("'UthQalun', serif",  '25px', '21px'),
    'duri':  ("'UthDuri', serif",   '25px', '21px'),
}
RIW_COLOR = {'hafs': '#1E3A5F', 'warsh': '#2F6B5E', 'qalun': '#A8762C', 'duri': '#8C2F39'}

HELMET = '''<helmet>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Amiri+Quran&family=Reem+Kufi:wght@400;500;600;700&family=Readex+Pro:wght@200;300;400;500;600&display=swap" rel="stylesheet">
<style>
@font-face { font-family: "Maghribi"; src: url("%s") format("opentype"); font-display: swap; }
@font-face { font-family: "UthQalun"; src: url("%s") format("truetype"); font-display: swap; }
@font-face { font-family: "UthDuri";  src: url("%s") format("truetype"); font-display: swap; }
@font-face { font-family: "UthHafs";  src: url("%s") format("opentype"); font-display: swap; }
body { margin: 0; background: #E9E6DC; }
a { color: inherit; text-decoration: none; }
::selection { background: #1E3A5F; color: #F3F1EA; }
</style>
</helmet>''' % (FONT, FONT_QALUN, FONT_DURI, FONT_HAFS)

# ألوان مستمدّة من تقليد الزخرفة المغربية: اللازورد والمُغرة والقرمز
INK, LEAF, PAPER, RULE = '#1C1815', '#E9E6DC', '#F6F4EE', '#CFC9BA'
LAPIS, LAPIS_L, OCHRE, CARMINE, SAGE = '#1E3A5F', '#2E5584', '#A8762C', '#8C2F39', '#5A6B5D'

SRC = {
 'ashmuni':       ('الأشموني', '#6B5436', 'منار الهدى', 11651),
 'akhshid':       ('ابن الأخشيذ', '#2E5E7A', 'منازل القرآن في الوقوف', 10795),
 'hubti':         ('الوقف الهبطي', '#2F6B5E', 'مصحفا ورش وقالون', 9980),
 'ansari':        ('الأنصاري', '#5A4A7A', 'المقصد', 7871),
 'amani':         ('العُماني', '#9A5B2E', 'المرشد في الوقف والابتداء', 7556),
 'saj':           ('السجاوندي', '#8C2F39', 'علل الوقوف', 6814),
 'nahhas':        ('النحاس', '#7A3E8C', 'القطع والائتناف', 5651),
 'dani':          ('الداني', '#1E3A5F', 'المكتفى', 5207),
 'ghazzal':       ('ابن الغزّال', '#3C6E8F', 'الوقف والابتداء', 3871),
 'anbari':        ('ابن الأنباري', '#B05A28', 'إيضاح الوقف والابتداء', 2732),
 'ibn_sadan':     ('ابن سعدان', '#4A6B33', 'الوقف والابتداء', 411),
}

# مصادر مسجَّلة بلا نصّ بعد — تظهر مطفأة في الواجهة
PENDING = []
CAT = {
 'tam':    ('وقف تام',   'ت',  '#1B5E3F'),
 'kafi':   ('وقف كاف',   'ك',  '#1E3A5F'),
 'hasan':  ('وقف حسن',   'ح',  '#8A6A1F'),
 'jaiz':   ('وقف جائز',  'ج',  '#5A6B5D'),
 'mamnu':  ('وقف ممنوع', 'لا', '#8C2F39'),
 'muanaqa':('معانقة',    '∴', '#5A4A7A'),
}

def doc(title, body, script, w, h, fill=False):
    prev = '' if fill else ',"$preview":{"width":%d,"height":%d}' % (w, h)
    if fill:
        prev = ',"$preview":{"width":%d,"height":%d}' % (w, h)
    return f'''<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
{HELMET}
{body}
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"x":{{"editor":null}}{prev}}}'>
{script}
</script>
</body>
</html>
'''


def logo_mark(size, c1=None, c2=None, c3=None, rule=None):
    """علامة جامع الوقوف: فجوة في السطر، وفوقها ∴ المعانقة بثلاثة ألوان."""
    c1 = c1 or LAPIS; c2 = c2 or OCHRE; c3 = c3 or CARMINE; rule = rule or INK
    u = size / 32.0
    r = 2.55 * u
    cx, y = 16 * u, 22 * u
    gw, sw = 7 * u, 1.9 * u
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" fill="none" aria-hidden="true">'
            f'<circle cx="{cx}" cy="{8.5*u}" r="{r}" fill="{c1}"/>'
            f'<circle cx="{cx-5.4*u}" cy="{15.2*u}" r="{r}" fill="{c2}"/>'
            f'<circle cx="{cx+5.4*u}" cy="{15.2*u}" r="{r}" fill="{c3}"/>'
            f'<path d="M{4*u} {y} H{cx-gw/2}" stroke="{rule}" stroke-width="{sw}" stroke-linecap="round"/>'
            f'<path d="M{cx+gw/2} {y} H{28*u}" stroke="{rule}" stroke-width="{sw}" stroke-linecap="round"/>'
            '</svg>')
