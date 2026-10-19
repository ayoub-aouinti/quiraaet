#!/usr/bin/env python3
"""تصحيحُ الإحالات: من مُعرِّف صفحة الشاملة إلى رقم الصفحة المطبوعة.

كان `extract_shamela.py` يُقيِّد `rec['page_id']` — وهو مُعرِّفٌ داخليٌّ في
الشاملة — ثم تُعرَض الإحالةُ «ص{الرقم}» كأنها صفحةُ المطبوع. فمن فتح الكتابَ
على الرقم المذكور وجد كلاماً آخر، وهذا يُبطِل المراجعةَ من أصلها.

والانزياحُ يختلف من كتابٍ إلى كتاب، وقد قِسته بـshamela_get_citation:

    النحاس   20966   صفر        — إحالاتُه صحيحةٌ أصلاً، فلا تُمسّ
    الأنصاري 10917   +٣ ثابت    — تحقَّقتُ عند 9 و20 و50 و89
    الأشموني 38091   +٤ ثابت    — تحقَّقتُ عند 68 و100 و500 و800 و864
    السجاوندي 30007  متغيّر     — يزحف من +101 إلى +113 على ثلاثة أجزاء،
                                  فلا يصحّ فيه حسابٌ، وخريطتُه في ملفٍّ مستقلّ

ولا يُصحَّح كتابٌ إلا بأحد أمرين: انزياحٌ ثابتٌ تحقَّقتُ منه في طرفَي المدى
ووسطِه، أو خريطةٌ مبنيّةٌ بالاستدعاء. وما عدا ذلك يُترك على حاله.

    python3 fix_pagerefs.py out/waqf.db ashmuni
    python3 fix_pagerefs.py out/waqf.db saj out/pagemap_saj.json
"""
import json, re, sqlite3, sys
from collections import Counter

# المصدر: (الانزياح، شاهدُ التحقُّق)
CONST = {
    'ashmuni': (4, 'تُحقِّق عند page_id 68 و100 و500 و800 و864'),
    'ansari':  (3, 'تُحقِّق عند page_id 9 و20 و50 و89'),
}

REF = re.compile(r'ص(\d+)')


def main(db, source, mapfile=None):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row

    pmap = None
    if mapfile:
        raw = json.load(open(mapfile, encoding='utf-8'))
        pmap = {int(k): v for k, v in raw.items()}
        print(f'خريطةٌ مبنيّةٌ بالاستدعاء: {len(pmap)} مدخلاً')
    elif source in CONST:
        off, why = CONST[source]
        print(f'انزياحٌ ثابت: {off:+d} — {why}')
    else:
        sys.exit(f'لا انزياحَ معروفاً لـ{source} ولا خريطة. لا يُصحَّح بالظنّ.')

    rows = con.execute(
        'SELECT seq, source, note FROM rulings WHERE source=? AND note IS NOT NULL',
        (source,)).fetchall()

    upd, tally = [], Counter()

    def repl(m):
        pid = int(m.group(1))
        if pmap is not None:
            e = pmap.get(pid)
            if e is None:
                tally['خارج الخريطة — تُرك'] += 1
                return m.group(0)
            tally['صُحِّح'] += 1
            part = e.get('part')
            return f"ج{part}/ص{e['page']}" if part else f"ص{e['page']}"
        tally['صُحِّح'] += 1
        return f'ص{pid + CONST[source][0]}'

    for r in rows:
        new = REF.sub(repl, r['note'])
        if new != r['note']:
            upd.append((new, r['seq'], r['source']))

    con.executemany('UPDATE rulings SET note=? WHERE seq=? AND source=?', upd)
    con.commit()

    print('أسطرٌ مسَّها التعديل:', len(upd), 'من', len(rows))
    for k, v in tally.most_common():
        print(f'  {k}: {v}')


if __name__ == '__main__':
    main(*sys.argv[1:4])
