#!/usr/bin/env python3
"""يقسّم «البدور الزاهرة في القراءات العشر المتواترة» (عبد الفتاح القاضي) إلى مداخل.

المدخل فقرةٌ تبدأ بـ « " كلمة " »، وتُلحَق به الفقراتُ التالية حتى المدخل الذي يليه.
نصُّ المدخل يُحفَظ **حرفياً** كما في ملف الشاملة (نسخة موافقة للمطبوع)، ولا يُعدَّل.
السورة تُعرَف من عنوانها: «سورة X» فقرةً مستقلة (البقرة وآل عمران) أو مدخلاً مقتبساً
«" سورة النساء "». وما قبل البقرة (الاستعاذة والبسملة والفاتحة) سورةٌ 1.
"""
import glob, json, re, sys
from normalize import norm
from read_doc import read_doc
from link_khilaf import plain_names

SRC = 'sources/books/badur'
OUT = 'out/badur_entries.jsonl'


def main():
    text = '\n'.join(read_doc(f) for f in sorted(glob.glob(SRC + '/*.doc')))
    # العناوين: «" سورة X "» أو «(سورة X)» وقد تأتي في ذيل فقرةٍ أو مطلعها: تُفصَل فقرةً مستقلة
    text = re.sub(r'(?:"\s*|\(\s*)سورة\s+([^"\)\n\x0b]{2,30}?)\s*(?:"|\))',
                  lambda m: '\x0b@@SURA:' + m.group(1) + '@@\x0b', text)
    paras = [p.strip() for p in text.split('\x0b') if p.strip()]
    names = plain_names()
    keys = [(norm(re.sub(r'^ال', '', n)) or norm(n), i + 1) for i, n in enumerate(names)]
    keys.sort(key=lambda x: -len(x[0]))

    ALIAS = {'المؤمن': 'غافر', 'القتال': 'محمد', 'ألم نشرح': 'الشرح', 'الدهر': 'الإنسان', 'بني إسرائيل': 'الإسراء',
             'الملائكة': 'فاطر', 'حم السجدة': 'فصلت', 'السجدة': 'السجدة', 'ألم تنزيل': 'السجدة', 'التحريم': 'التحريم'}

    def sura_of(s):
        s = ALIAS.get(s.strip(), s)
        """اسم السورة من نصٍّ يبدأ بها: أطول اسمٍ يطابق مطلعَ النص."""
        t = norm(re.sub(r'^ال', '', s.strip().strip('"').strip()))
        for k, i in keys:
            if t.startswith(k):
                return i
        return None

    entries, cur, sura, last = [], None, 1, 0
    for p in paras:
        mh = re.match(r'^@@SURA:(.*)@@$', p)
        if mh:
            if sura_of(mh.group(1)):
                sura = sura_of(mh.group(1))
            cur = None
            continue
        m = re.match(r'^"\s*(.*?)\s*"\s*(.*)$', p, re.S)
        plain = re.match(r'^سورة\s+(.*)$', p)
        if plain and len(p) < 80 and sura_of(plain.group(1)):
            sura = sura_of(plain.group(1))
            cur = None
            continue
        if m:
            word, rest = m.group(1), m.group(2)
            sm = re.match(r'^سورة\s+(.*)$', word)
            if sm and not rest.strip() and sura_of(sm.group(1)):
                sura = sura_of(sm.group(1))   # عنوان السورة مدخلٌ مقتبس
                cur = None
                continue
            cur = {'id': 'b%04d' % (len(entries) + 1), 'sura': sura, 'w': word, 't': p}
            entries.append(cur)
        elif cur is not None:
            cur['t'] += '\n' + p
    with open(OUT, 'w', encoding='utf-8') as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')
    from collections import Counter
    c = Counter(e['sura'] for e in entries)
    print(len(entries), 'مدخلاً', 'في', len(c), 'سورة')
    print('أول مدخل:', entries[0]['t'][:60])
    print('عدد المداخل في سور:', [(s, c[s]) for s in (1, 2, 3, 4, 6, 18, 36, 112, 114)])
    nm = sum(1 for s in range(1, 115) if c[s] == 0)
    print('سور بلا مداخل:', nm)


if __name__ == '__main__':
    main()
