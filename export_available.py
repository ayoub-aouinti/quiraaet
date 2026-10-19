#!/usr/bin/env python3
"""جدولُ مصنَّفات الوقف المتاحة: ما حالُه مطبوعٌ أو محقَّقٌ في «معجم مصنّفات
الوقف والابتداء»، مرتَّباً على القرون، ليُعرَف ما يمكن تحصيلُه وإضافتُه.

وعناوينُ المعجمِ مقروءةٌ آلياً من نسخةٍ مصوَّرة، ففي بعضها تحريفٌ ظاهر
(«ان الفا» و«الولايف»). ولم أُصلِح شيئاً منها: المُصلَحُ بالظنِّ أسوأُ من
المحرَّف المعلومِ تحريفُه، وإنما يُعلَّم بعمودِ «ثقة العنوان».
"""
import json, re, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

INK, HEAD, LEAF, RULE = '1C1815', '1E3A5F', 'E9E6DC', 'CFC9BA'
OCHRE, SAGE = 'A8762C', '5A6B5D'

# حرفٌ عربيٌّ مكرَّرٌ بلا معنى أو حرفٌ لاتينيٌّ أو رقمٌ وسط الكلمة: أثرُ القراءة الآلية
NOISE = re.compile(r'[A-Za-z0-9]|[ء-ي]\d|\(\s*ك\d')


def confidence(title, author):
    s = f'{title} {author}'
    if 'تعذّرت قراءة' in title:
        return 'العنوان غير مقروء'
    if NOISE.search(s):
        return 'في العنوان تحريفُ قراءة'
    return 'سليم ظاهراً'


def main(doc_json, out_xlsx, db=None):
    d = json.load(open(doc_json, encoding='utf-8'))
    rows = []
    for c in d['centuries']:
        for r in c['rows']:
            st = r['state']
            if 'مطبوع' not in st and 'محقَّق' not in st:
                continue
            rows.append({
                'century': c['century'], 'name': c['name'],
                'title': (r['title'] or '').strip(),
                'author': (r['author'] or '').strip(),
                'state': st, 'page': r['page'],
                'conf': confidence(r['title'] or '', r['author'] or ''),
                'quote': (r['evidence'][0]['quote'][:180] if r.get('evidence') else ''),
            })
    rows.sort(key=lambda x: (x['century'], x['title']))

    # ما دخل المشروعَ فعلاً، ليُعرَف الباقي
    inside = set()
    if db:
        import sqlite3
        con = sqlite3.connect(db)
        for (n,) in con.execute('SELECT name FROM sources'):
            inside.add((n or '').strip())

    wb = Workbook()
    ws = wb.active
    ws.title = 'المتاح تحصيله'
    ws.sheet_view.rightToLeft = True
    cols = [('القرن', 8), ('المصنَّف', 52), ('المؤلف', 40), ('الحال', 22),
            ('صفحة المعجم', 13), ('ثقة العنوان', 22), ('في المشروع', 12),
            ('شاهد الحال من المعجم', 70)]
    for i, (h, w) in enumerate(cols, 1):
        c = ws.cell(1, i, h)
        c.font = Font(name='Calibri', bold=True, color='FFFFFF', size=11)
        c.fill = PatternFill('solid', fgColor=HEAD)
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = 'A2'
    ws.row_dimensions[1].height = 30

    thin = Side('thin', color=RULE)
    bd = Border(left=thin, right=thin, top=thin, bottom=thin)
    for n, r in enumerate(rows, 2):
        has = 'نعم' if r['title'] in inside else ''
        vals = [r['century'], r['title'], r['author'], r['state'],
                r['page'], r['conf'], has, r['quote']]
        for i, v in enumerate(vals, 1):
            c = ws.cell(n, i, v)
            c.font = Font(name='Calibri', size=10.5)
            c.border = bd
            c.alignment = Alignment(horizontal='right', vertical='top', wrap_text=(i in (2, 3, 8)))
        if r['conf'] != 'سليم ظاهراً':
            ws.cell(n, 6).fill = PatternFill('solid', fgColor='F2E6D0')
        if has:
            ws.cell(n, 7).font = Font(name='Calibri', size=10.5, bold=True, color=SAGE)
        if 'محقَّق' in r['state']:
            ws.cell(n, 4).font = Font(name='Calibri', size=10.5, bold=True, color=HEAD)

    ws2 = wb.create_sheet('بيانُ الجدول')
    ws2.sheet_view.rightToLeft = True
    ws2.column_dimensions['A'].width = 110
    notes = [
        'جدولُ ما يمكن تحصيلُه من مصنَّفات الوقف والابتداء.',
        '',
        f'مصدرُه: «معجم مصنّفات الوقف والابتداء» لمحمد توفيق حديد، مقروءاً آلياً من نسخةٍ مصوَّرة.',
        f'عددُ المصنَّفات التي حالُها مطبوعٌ أو محقَّق: {len(rows)} من {sum(len(c["rows"]) for c in d["centuries"])} مدخلاً في فصول المعجم.',
        '',
        'عمود «الحال» منقولٌ من تصريح المعجم نفسِه، وشاهدُه في العمود الأخير بلفظه.',
        'ومتى صُرِّح بأكثرَ من حالٍ جُمعت كلُّها ولم يُرجَّح واحدٌ منها، فالكتابُ قد يكون مطبوعاً ومخطوطاً معاً.',
        '',
        'عمود «ثقة العنوان» تحذيرٌ لا تصحيح: العناوينُ مقروءةٌ آلياً، وفي بعضها تحريفٌ ظاهر.',
        'ولم يُصلَح منها شيءٌ بالظنّ، فالعنوانُ المحرَّفُ المعلومُ تحريفُه أسلمُ من المُصلَحِ بالحدس.',
        'فإذا أردتَ طلبَ كتابٍ من هذا الجدول فراجِع عنوانَه في المعجم على صفحته المذكورة.',
        '',
        'عمود «في المشروع» يُعلَّم بـ«نعم» لما دخل قاعدةَ «جامع الوقوف» فعلاً.',
        'وما خلا منه فهو المطلوبُ تحصيلُه: إن رفعتَ نسخةً منه أُدخِلَ على المنهج نفسِه.',
    ]
    for i, t in enumerate(notes, 1):
        c = ws2.cell(i, 1, t)
        c.font = Font(name='Calibri', size=11, bold=(i == 1))
        c.alignment = Alignment(horizontal='right', vertical='top', wrap_text=True)

    wb.save(out_xlsx)
    print('حُفظ', out_xlsx)
    print('  مطبوع أو محقَّق:', len(rows),
          '· عنوانُه سليمٌ ظاهراً:', sum(1 for r in rows if r['conf'] == 'سليم ظاهراً'),
          '· في المشروع:', sum(1 for r in rows if r['title'] in inside))


if __name__ == '__main__':
    main(*sys.argv[1:])
