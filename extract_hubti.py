#!/usr/bin/env python3
"""استخراج وقف الهبطي من المصحف المحمدي المغربي برواية ورش.

الملف مكتوب بترميز خطّ AALMAGHRIBI، لا بترميز عربي قياسي: حروف مُزاحة إلى
مواقع محارف أخرى (ژ=ك، چ=ق، ڤ=ف، ۰۱۴=ألف وصل)، وعلامة الوقف الهبطي مرمّزة
بـ U+0610. فتُردّ الحروف أولاً إلى أصلها، ثم يُحاذى النصّ على فهرس الكلمات،
فتُسنَد كل علامة إلى الكلمة التي تلحقها.

العدّ في هذا المصحف مدنيّ أخير، ويخالف العدّ الكوفي في أرقام الآي، ولذلك
تُعتمد المحاذاة التسلسلية لا أرقام الآيات.
"""
import json, re, sys, csv
from difflib import SequenceMatcher
from normalize import norm

HUBTI_MARK = 'ؐ'          # علامة وقف الهبطي في هذا الترميز

# حروف مُزاحة في خطّ AALMAGHRIBI تُردّ إلى أصلها.
# استُنبطت هذه الخريطة من البيانات نفسها: حوذيت كلمات الملف على النصّ
# المرجعي، ثم قوبلت المختلفة حرفاً حرفاً لاستخراج الإبدالات المتكرّرة.
LETTERS = {
    # صور ألف الوصل والهمزة
    '۰': 'ا', '۱': 'ا', '۴': 'ا', '۶': 'ا', '۷': 'ا',
    '۸': 'ا', '۹': 'ا', 'ٱ': 'ا', 'è': 'ا',
    'ﭐ': 'ا', 'ﹹ': 'ا', '"': 'ا', "'": 'ا',
    # صور اللام (الخطّ المغربي يستعمل أكثر من موقع لها)
    'ﻟ': 'ل', 'ڤ': 'ل', 'چ': 'ل',
    'ژ': 'ك',
}

# علامات ضبط ومحارف زينة تُحذف قبل المقارنة
STRIP = set('ؐؕ؛ٰٖٓٔٗ٘ٙٛ'
            'ۣۭۢ۬۝ـ﮲;„”®©¥—“')


def fold(word):
    return norm(''.join(LETTERS.get(c, c) for c in word if c not in STRIP))


def read_words(path):
    """كلمات المصحف المغربي، ومع كل كلمة هل تحمل علامة الهبطي."""
    import docx
    d = docx.Document(path)
    text = '\n'.join(p.text for p in d.paragraphs)
    text = re.sub(r'\[[^\]]*\]', ' ', text)          # عناوين السور
    text = re.sub(r'\(\s*\d+\s*\)', ' ', text)        # أرقام الآي
    out = []
    for tok in text.split():
        n = fold(tok)
        if n:
            out.append({'raw': tok, 'n': n, 'mark': HUBTI_MARK in tok})
    return out


def align(src, words):
    a = [x['n'] for x in src]
    b = [x['n'] for x in words]
    sm = SequenceMatcher(None, a, b, autojunk=False)
    pairs, gaps = [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                pairs.append((src[i1 + k], words[j1 + k], 'exact'))
        elif (i2 - i1) == (j2 - j1):
            for k in range(i2 - i1):
                pairs.append((src[i1 + k], words[j1 + k], 'replace'))
            gaps.append((tag, i2 - i1, [src[i]['raw'] for i in range(i1, min(i2, i1 + 4))],
                         [words[j]['text'] for j in range(j1, min(j2, j1 + 4))]))
        else:
            gaps.append((tag, i2 - i1, [src[i]['raw'] for i in range(i1, min(i2, i1 + 4))],
                         [words[j]['text'] for j in range(j1, min(j2, j1 + 4))]))
    return pairs, gaps


def main(docx_path, words_indexed, outdir):
    words = json.load(open(words_indexed, encoding='utf-8'))
    src = read_words(docx_path)
    marks_in_src = sum(1 for x in src if x['mark'])
    print(f'كلمات المصحف المغربي: {len(src)}   علامات الهبطي فيه: {marks_in_src}')

    pairs, gaps = align(src, words)
    exact = sum(1 for _, _, t in pairs if t == 'exact')
    print(f'محاذاة: {len(pairs)} كلمة ({exact} مطابقة تامة) · فجوات {len(gaps)}')

    rows, lost = [], marks_in_src
    for s, w, kind in pairs:
        if not s['mark']:
            continue
        lost -= 1
        rows.append({
            'seq': w['seq'], 'sura': w['sura'], 'sura_name': w['sura_name'],
            'ayah': w['ayah'], 'word': w['text'], 'maghribi': s['raw'],
            'symbol': 'ص', 'term': 'وقف الهبطي (صالح للوقف)', 'category': 'jaiz',
            'align': kind,
        })
    print(f'علامات أُسنِدت: {len(rows)} · لم تُسنَد (في فجوات): {lost}')

    json.dump(rows, open(f'{outdir}/hubti_marks.json', 'w', encoding='utf-8'),
              ensure_ascii=False)
    with open(f'{outdir}/hubti_marks.csv', 'w', encoding='utf-8-sig', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wr.writeheader(); wr.writerows(rows)
    json.dump([{'tag': g[0], 'n': g[1], 'maghribi': g[2], 'ref': g[3]} for g in gaps[:300]],
              open(f'{outdir}/hubti_gaps.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    return rows, gaps


if __name__ == '__main__':
    main(*sys.argv[1:4])
