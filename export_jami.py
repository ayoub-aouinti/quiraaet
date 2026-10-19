#!/usr/bin/env python3
"""إخراج «جامع الوقوف» ملفَّ إكسل: كلمةٌ في كل سطر، ولكل مصدرٍ عمود.

أربع أوراق:
  ١- الكلمات المفهرسة: كلماتُ المصحف على ترتيبها، وفي كل عمودٍ مصطلحُ مصدرٍ
     بلفظه هو، لا بالتصنيف العام — فالمصطلح الأصلي لا يُستبدل.
  ٢- الأحكام: كلُّ حكمٍ بتفصيله، ومعه الفئة العامة والتقريب والحاشية.
  ٣- المصادر: المصدر وصاحبه وطبعته وعددُ مواضعه وحالُه (محقَّق أم مقترَح).
  ٤- المصطلحات: جدول المطابقة بين مصطلح كل مصدرٍ والفئة العامة، وفيه
     عمودُ «روجِعت» ليملأه المتخصص.
"""
import json, sqlite3, sys
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

HEAD = PatternFill('solid', fgColor='1E3A5F')
PROP = PatternFill('solid', fgColor='A8762C')
NOTE = PatternFill('solid', fgColor='FFF4D6')
AR = 'Arial'

CATNAME = {'tam': 'تام', 'kafi': 'كاف', 'hasan': 'حسن', 'jaiz': 'جائز',
           'mamnu': 'ممنوع', 'muanaqa': 'معانقة'}


def head(ws, cols, widths, marks=()):
    ws.sheet_view.rightToLeft = True
    ws.append(cols)
    for i, (c, w) in enumerate(zip(cols, widths), start=1):
        cell = ws.cell(row=1, column=i)
        cell.font = Font(name=AR, bold=True, color='FFFFFF', size=11)
        cell.fill = PROP if (i - 1) in marks else HEAD
        cell.alignment = Alignment(horizontal='center', vertical='center',
                                   wrap_text=True)
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = 'A2'


def main(db, outfile):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    srcs = con.execute('''SELECT s.id, s.name, s.kind, s.has_text,
            (SELECT count(*) FROM rulings WHERE source=s.id) n,
            (SELECT count(*) FROM rulings WHERE source=s.id AND status='proposed') np
        FROM sources s ORDER BY s.has_text DESC, n DESC''').fetchall()
    live = [s for s in srcs if s['n']]
    wb = Workbook()

    # ───────────── ١ · الكلمات المفهرسة ─────────────
    ws = wb.active
    ws.title = 'الكلمات المفهرسة'
    cols = ['تسلسل', 'السورة', 'اسم السورة', 'الآية', 'موضع الكلمة', 'الكلمة']
    widths = [8, 7, 15, 7, 10, 26]
    marks = set()
    for i, s in enumerate(live):
        prop = s['np'] == s['n']
        cols.append(s['name'] + (' (مقترَح)' if prop else ''))
        widths.append(20)
        if prop:
            marks.add(len(cols) - 1)
    head(ws, cols, widths, marks)

    byseq = {}
    for r in con.execute('SELECT seq, source, raw, term FROM rulings'):
        byseq.setdefault(r['seq'], {})[r['source']] = (r['raw'] or '').strip() or r['term']
    nwords = 0
    for w in con.execute('SELECT seq,sura,sura_name,ayah,wpos,text FROM words ORDER BY seq'):
        d = byseq.get(w['seq'], {})
        ws.append([w['seq'], w['sura'], w['sura_name'], w['ayah'], w['wpos'], w['text']]
                  + [d.get(s['id']) for s in live])
        nwords += 1

    # ───────────── ٢ · الأحكام: لكلِّ كتابٍ خانتُه ─────────────
    # هذه هي هيئةُ الملف الأول: الموضعُ سطرٌ واحد، وكلُّ كتابٍ عمودٌ فيه
    # مصطلحُه بلفظه. وهي أصلحُ للموازنة بالعين من سطرٍ لكل حكم.
    # ولا يُحسَب هنا عمودُ «وفاق» أو «خلاف»: الفئاتُ العامّة للّون لا للمقارنة،
    # والموازنةُ بين مصطلحَين من مدرستين حكمٌ لا يُؤتَمن عليه الحاسب.
    ws2 = wb.create_sheet('الأحكام')
    cols2 = ['تسلسل', 'الموضع', 'الوقف بعد كلمة', 'عدد المصادر']
    widths2 = [8, 20, 26, 11]
    marks2 = set()
    for s in live:
        prop = s['np'] == s['n']
        cols2.append(s['name'] + (' (مقترَح)' if prop else ''))
        widths2.append(20)
        if prop:
            marks2.add(len(cols2) - 1)
    head(ws2, cols2, widths2, marks2)

    n2 = 0
    wrow = {w['seq']: w for w in con.execute(
        'SELECT seq,sura,sura_name,ayah,text FROM words')}
    for seq in sorted(byseq):
        w = wrow.get(seq)
        if w is None:
            continue
        d = byseq[seq]
        ws2.append([seq, f"{w['sura_name']} {w['sura']}:{w['ayah']}", w['text'], len(d)]
                   + [d.get(s['id']) for s in live])
        n2 += 1

    # ───────────── ٢ب · تفصيل الأحكام ─────────────
    # الهيئةُ المفصَّلة تبقى في ورقةٍ على حدة، فلا تضيع فيها نفائسُ لا يحملها
    # عمودٌ واحد: عزوُ الداني لأصحابه، وعلّةُ السجاوندي لكل وقف.
    ws2b = wb.create_sheet('تفصيل الأحكام')
    head(ws2b, ['تسلسل', 'الموضع', 'الوقف بعد كلمة', 'المصدر', 'مصطلح المصدر',
                'المصطلح المعياري', 'الفئة العامة', 'تقريبية', 'أقوال أخرى',
                'الحال', 'الثقة', 'العلّة والعزو والحاشية'],
         [8, 18, 24, 28, 18, 16, 12, 9, 16, 12, 12, 70])
    n2b = 0
    for r in con.execute('''
        SELECT r.seq, w.sura_name, w.sura, w.ayah, w.text, s.name src, r.raw, r.term,
               r.category, r.approx, r.alt_term, r.status, r.confidence, r.note
        FROM rulings r JOIN words w ON w.seq=r.seq JOIN sources s ON s.id=r.source
        ORDER BY r.seq, s.name'''):
        ws2b.append([r['seq'], f"{r['sura_name']} {r['sura']}:{r['ayah']}", r['text'],
                     r['src'], r['raw'], r['term'],
                     CATNAME.get(r['category'], r['category']),
                     'نعم' if r['approx'] else 'لا', r['alt_term'],
                     'مقترَح' if r['status'] == 'proposed' else 'محقَّق',
                     r['confidence'], r['note']])
        n2b += 1

    # ───────────── ٣ · المصادر ─────────────
    ws3 = wb.create_sheet('المصادر')
    cols3 = ['المعرّف', 'المصدر', 'المؤلف', 'الوفاة', 'النوع', 'الطبعة المعتمدة',
             'عدد المواضع', 'الحال']
    head(ws3, cols3, [12, 40, 32, 10, 10, 40, 12, 12])
    cols_have = {c[1] for c in con.execute('PRAGMA table_info(sources)')}
    for s in srcs:
        row = dict(con.execute('SELECT * FROM sources WHERE id=?', (s['id'],)).fetchone())
        state = ('ينتظر النصّ' if not s['n'] else
                 'مقترَح' if s['np'] == s['n'] else
                 'محقَّق' if s['np'] == 0 else 'مختلط')
        ws3.append([s['id'], s['name'], row.get('author'), row.get('died'),
                    {'book': 'كتاب', 'mushaf': 'مصحف'}.get(s['kind'], s['kind']),
                    row.get('edition'), s['n'], state])

    # ───────────── ٤ · المصطلحات ─────────────
    ws4 = wb.create_sheet('المصطلحات')
    head(ws4, ['المصدر', 'الرمز', 'مصطلح المصدر', 'الفئة العامة',
               'مطابقة تقريبية', 'روجِعت'], [36, 8, 22, 14, 14, 12])
    terms = json.load(open('terms.json', encoding='utf-8'))
    n4 = 0
    for sid, s in terms['sources'].items():
        for sym, t in s['terms'].items():
            ws4.append([s['name'], sym, t['term'],
                        CATNAME.get(t['category'], t['category']),
                        'نعم' if t.get('approx') else 'لا',
                        'نعم' if t.get('reviewed') else 'لا'])
            n4 += 1
    for row in ws4.iter_rows(min_row=2, min_col=6, max_col=6):
        for c in row:
            c.fill = NOTE

    for s in wb.worksheets:
        for row in s.iter_rows(min_row=2):
            for c in row:
                c.font = Font(name=AR, size=11)
                c.alignment = Alignment(horizontal='right', vertical='center')

    wb.save(outfile)
    print(f'حُفظ {outfile}')
    print(f'  كلمات: {nwords} · أحكام: {n2} · مصادر: {len(srcs)} '
          f'(منها {len(live)} بنصّ) · مصطلحات: {n4}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
