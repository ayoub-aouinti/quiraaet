#!/usr/bin/env python3
"""استخراج علامات وقف المصحف من رموز اليونيكود المضمَّنة في الرسم العثماني.

علامات مصحف المدينة ليست حاشية على النصّ بل جزء من ترميزه: كل علامة محرف
مستقلّ يلحق الكلمة التي يُوقف بعدها. فاستخراجها نقلٌ محض لا اجتهاد فيه،
بخلاف ما يُستخرج من الكتب.
"""
import json, re, sys, csv
from normalize import norm

MARKS = {
    'ۘ': ('م',   'وقف لازم',        'tam',     False),
    'ۗ': ('قلى', 'الوقف أولى',      'kafi',    True),
    'ۖ': ('صلى', 'الوصل أولى',      'jaiz',    True),
    'ۚ': ('ج',   'وقف جائز',        'jaiz',    False),
    'ۙ': ('لا',  'لا يوقف عليه',    'mamnu',   False),
    'ۛ': ('∴', 'معانقة',       'muanaqa', False),
    'ۜ': ('س',   'سكتة',            'jaiz',    True),
}


def extract(quran_json, words_indexed):
    ref = json.load(open(quran_json, encoding='utf-8'))
    words = json.load(open(words_indexed, encoding='utf-8'))

    # فهرس (سورة، آية، موضع الكلمة) -> تسلسل الكلمة في قاعدتنا
    bypos = {}
    for w in words:
        if w.get('wpos'):
            bypos[(w['sura'], w['ayah'], w['wpos'])] = w

    out, missed = [], 0
    for s in ref:
        for v in s['verses']:
            for i, tok in enumerate(v['text'].split(), start=1):
                hits = [c for c in tok if c in MARKS]
                if not hits:
                    continue
                w = bypos.get((s['id'], v['id'], i))
                if not w:
                    missed += 1
                    continue
                for ch in hits:
                    sym, term, cat, approx = MARKS[ch]
                    out.append({
                        'seq': w['seq'], 'sura': s['id'], 'sura_name': s['name'],
                        'ayah': v['id'], 'wpos': i, 'word': w['text'],
                        'symbol': sym, 'term': term, 'category': cat,
                        'approx': approx, 'codepoint': f'U+{ord(ch):04X}',
                    })
    return out, missed


def main(quran_json, words_indexed, outdir):
    rows, missed = extract(quran_json, words_indexed)
    json.dump(rows, open(f'{outdir}/mushaf_marks.json', 'w', encoding='utf-8'),
              ensure_ascii=False)
    with open(f'{outdir}/mushaf_marks.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    from collections import Counter
    c = Counter(r['symbol'] for r in rows)
    print(f'علامات مستخرجة: {len(rows)}   كلمات لم تُطابَق: {missed}')
    for k, n in c.most_common():
        print(f'   {k:<5} {n}')
    return rows


if __name__ == '__main__':
    main(*sys.argv[1:4])
