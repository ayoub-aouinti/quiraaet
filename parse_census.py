#!/usr/bin/env python3
"""استخراج إحصاء الفصل الأول: مصنفات القرون الثاني والثالث والرابع.

هذا الفصل لا تُفصَّل مداخلُه في فهرس الموضوعات، وإنما يسردها المؤلف سرداً
مرقَّماً في صفحات ٥٩-٦٥، فتُستخرج من المتن مباشرة. ورمز «ط» بعد العنوان
علامةُ المؤلف على أن الكتاب مطبوع، نصّ عليها في كشّاف رموزه.
"""
import json, re, unicodedata
import ocr_pdf as O

PAGES = range(59, 66)
DIR = 'ocr/mujam3'
BIDI = dict.fromkeys(map(ord, '‎‏‪‫‬‭‮'), None)

HEAD = re.compile(r'الكتب\s+المصن\S*\s+في\s+الو\S*\s+والابتدا\S*\s*في\s+الق\S*\s+'
                  r'(الثاني|الثالث|الرابع)')
ATTR = (r'(المنسوب|المسوب|المنسوبة)?\s*(ل[ء-ي][^"“”]{3,400})')
ANCHOR = re.compile(r'["“”‟]([^"“”‟\n]{3,200}?)["“”‟]\s*[:：.،]?\s*(?=' + ATTR + ')')
CENT = {'الثاني': 2, 'الثالث': 3, 'الرابع': 4}
DEATH = re.compile(r'\(?\s*(?:ت|نحو|قبل|بعد|بعيد)?\s*'
                   r'([٠-٩0-9]{2,4})\s*(?:-|–)?\s*'
                   r'([٠-٩0-9]{2,4})?\s*ه\s*\)?')


def clean(s):
    s = s.translate(BIDI)
    s = ''.join(c for c in s if not unicodedata.category(c).startswith('Cf'))
    s = re.sub(r'[ً-ْٰ]', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def main():
    recs = []
    cent = None
    for pg in PAGES:
        s = clean(O.text(DIR, pg))
        if not s:
            continue
        # مواضع عناوين القرون داخل الصفحة، ليُنسب كل مدخل إلى قرنه
        marks = [(m.start(), CENT[m.group(1)]) for m in HEAD.finditer(s)]

        def cent_at(pos):
            c = cent
            for st, v in marks:
                if st <= pos:
                    c = v
            return c
        anchors = list(ANCHOR.finditer(s))
        if marks:
            cent = marks[-1][1]
        for i, a in enumerate(anchors):
                end = anchors[i + 1].start() if i + 1 < len(anchors) else len(s)
                rest = s[a.end():end]
                title = a.group(1).strip(' :،.')
                printed = bool(re.search(r'[-–اأ]\s*ط\s*[\'"»]?\s*$', title))
                title = re.sub(r'\s*[-–اأ]\s*ط\s*[\'"»]?\s*$', '', title).strip()
                m = re.match(ATTR, rest)
                author = re.sub(r'\s*[.،]\s*$', '', m.group(2)).strip()[:200] if m else None
                recs.append({'title': title, 'author': author,
                             'attributed': bool(m and m.group(1)),
                             'century': cent_at(a.start()), 'printed_mark': printed,
                             'pdf_page': pg})
    return recs


if __name__ == '__main__':
    recs = main()
    json.dump(recs, open('out/mujam_census.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    from collections import Counter
    print('مداخل الإحصاء:', len(recs), Counter(r['century'] for r in recs))
    print('مطبوعة بعلامة (ط):', sum(1 for r in recs if r['printed_mark']))
    for r in recs[:6]:
        print(' ·', r['century'], '|', r['title'][:60], '|', (r['author'] or '—')[:50])
