#!/usr/bin/env python3
"""تحليل ملفات «خُلف قراءة X مقارنة برواية قالون» إلى سجلات.

كل ملف: عناوين «سورة X» تتخللها جداول. الصفان الأولان في كل جدول رأسٌ
(أسماء القراء)، ثم صفوف: [كلمة قالون + رقم الآية | قراءة كل راوٍ ... | بيان القراءة].

قانون الأمانة: هذه الملفات أُعدَّت بمعونة نموذج ولم تُراجَع على كتب القراءات،
فكل سجلٍّ يخرج بحال `unverified`، و`bayan` يُنقَل بلفظه ولا يُلخَّص.
"""
import glob, json, os, re, sys
import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

SRC = 'sources/khilaf'
BRACKETS = re.compile(r'[﴿﴾]')
AYAH = re.compile(r'^(.*?)((?:\s+[0-9٠-٩]+)+)\s*$')


def to_int(s):
    return int(s.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')))


def body(d):
    """الفقرات والجداول بترتيب ورودها."""
    for el in d.element.body.iterchildren():
        if el.tag.endswith('}p'):
            yield Paragraph(el, d)
        elif el.tag.endswith('}tbl'):
            yield Table(el, d)


def uniq(cells):  # غير مستعمل الآن، يُبقى للتشخيص
    out, last = [], None
    for c in cells:
        if c._tc is not last:
            out.append(c)
        last = c._tc
    return out


def parse_file(path):
    d = docx.Document(path)
    sura, recs, skipped = None, [], 0
    title = ''
    for blk in body(d):
        if isinstance(blk, Paragraph):
            t = blk.text.strip()
            if t.startswith('سورة '):
                sura = t[5:].strip()
            elif not title and t:
                title = t
            continue
        rows = blk.rows
        if len(rows) < 3:
            skipped += 1
            continue
        # أعمدة الشبكة: الخلية المدمجة تتكرّر في كل عمودٍ تمتدّ عليه
        h2 = [c.text.strip() for c in rows[1].cells]
        readers = h2[1:-1]
        for r in rows[2:]:
            cells = [c.text.strip() for c in r.cells]
            if len(cells) != len(h2):
                skipped += 1
                continue
            m = AYAH.match(BRACKETS.sub('', cells[0]).strip())
            if not m:
                skipped += 1
                continue
            recs.append({
                'sura': sura,
                'ayat': [to_int(x) for x in m.group(2).split()],
                'qalun': m.group(1).strip(),
                'readings': {n: BRACKETS.sub('', v).strip() for n, v in zip(readers, cells[1:-1])},
                'bayan': cells[-1],
            })
    return title, recs, skipped


def main():
    out = {}
    for f in sorted(glob.glob(os.path.join(SRC, '*.docx'))):
        name = os.path.basename(f)
        title, recs, sk = parse_file(f)
        print(f'{len(recs):6d} موضعاً · تُجوهل {sk:4d} · {name}')
        out[name] = {'title': title, 'status': 'unverified', 'records': recs}
    os.makedirs('out', exist_ok=True)
    with open('out/khilaf.json', 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False)


if __name__ == '__main__':
    main()
