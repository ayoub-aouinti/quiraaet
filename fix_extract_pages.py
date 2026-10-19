#!/usr/bin/env python3
"""تحويلُ عمود الصفحة في ملفّات الاستخراج من مُعرِّف الشاملة إلى المطبوع.

صُحِّحت الإحالاتُ في قاعدة البيانات، لكنّ ملفّاتِ الاستخراج بقيت على
`page_id`. فمن أعاد تشغيل الخطّ عاد الخطأُ كما كان، وهذا أسوأُ من الخطأ
الأوّل لأنه يعود بعد أن يُظنَّ أنه عولج. فيُصلَح المَنبَع لا المَصبّ.

    python3 fix_extract_pages.py 'out/rulings_saj/*.txt' --map out/pagemap_saj.json
    python3 fix_extract_pages.py 'out/rulings_ashmuni/*.txt' --offset 4
"""
import glob, json, shutil, sys
from collections import Counter


def convert(pattern, pmap=None, offset=None):
    tally = Counter()
    for path in sorted(glob.glob(pattern)):
        shutil.copy(path, path + '.pageid.bak')
        out = []
        for ln in open(path, encoding='utf-8'):
            parts = ln.rstrip('\n').split('|')
            # علامةُ السورة: #سورة|الصفحة|الاسم
            idx = 1 if parts[0].startswith('#') else 0
            raw = parts[idx].strip()
            if not raw.isdigit():
                tally['غير رقمية — تُركت'] += 1
                out.append(ln)
                continue
            pid = int(raw)
            if pmap is not None:
                e = pmap.get(pid)
                if e is None:
                    tally['خارج الخريطة — تُركت'] += 1
                    out.append(ln)
                    continue
                new = f"ج{e['part']}/ص{e['page']}" if e.get('part') else str(e['page'])
            else:
                new = str(pid + offset)
            parts[idx] = (parts[idx].replace(raw, new) if parts[0].startswith('#')
                          else new)
            tally['حُوِّلت'] += 1
            out.append('|'.join(parts) + '\n')
        open(path, 'w', encoding='utf-8').writelines(out)
    return tally


if __name__ == '__main__':
    pat = sys.argv[1]
    pmap = off = None
    if '--map' in sys.argv:
        raw = json.load(open(sys.argv[sys.argv.index('--map') + 1], encoding='utf-8'))
        pmap = {int(k): v for k, v in raw.items()}
    else:
        off = int(sys.argv[sys.argv.index('--offset') + 1])
    t = convert(pat, pmap, off)
    print(pat, '·', dict(t))
