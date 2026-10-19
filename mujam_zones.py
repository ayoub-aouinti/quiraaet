#!/usr/bin/env python3
"""استخراج حدود الأبواب والفصول من ترويسات صفحات المعجم.

ترويسةُ كل صفحة فردية تذكر بابَها وفصلَها، فمنها تُبنى خريطةُ الكتاب،
فيُقصَر البحثُ عن كل مدخل على موضعه من الكتاب لا على الكتاب كله.
"""
import json, re, unicodedata
import ocr_pdf as O

BODY = range(30, 2432)
BIDI = dict.fromkeys(map(ord, '‎‏‪‫‬‭‮'), None)

BAB = re.compile(r'الباب\s+(الأول|الثاني|الثالث|الرابع)\s*:')
FASL = re.compile(r'الفصل\s+(الحادي عشر|الثاني عشر|الأول|الثاني|الثالث|الرابع|الخامس|'
                  r'السادس|السابع|الثامن|التاسع|العاشر)\s*:')
CENT = re.compile(r'الق[رو]ن\s+(الحادي عشر|الثاني عشر|الثالث عشر|الرابع عشر|الخامس عشر|'
                  r'الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر)')
CENTURY = {'الثاني': 2, 'الثالث': 3, 'الرابع': 4, 'الخامس': 5, 'السادس': 6,
           'السابع': 7, 'الثامن': 8, 'التاسع': 9, 'العاشر': 10,
           'الحادي عشر': 11, 'الثاني عشر': 12, 'الثالث عشر': 13,
           'الرابع عشر': 14, 'الخامس عشر': 15}
BABN = {'الأول': 1, 'الثاني': 2, 'الثالث': 3, 'الرابع': 4}
# ترتيب فصول الباب الأول كما نصّت عليه مقدمة المؤلف
FASL_CENT = {'الثاني': 5, 'الثالث': 6, 'الرابع': 7, 'الخامس': 8, 'السادس': 9,
             'السابع': 10, 'الثامن': 11, 'التاسع': 12, 'العاشر': 13,
             'الحادي عشر': 14, 'الثاني عشر': 15}


def head(p):
    t = O.text('ocr/mujam', p)[:260].translate(BIDI)
    t = ''.join(c for c in t if not unicodedata.category(c).startswith('Cf'))
    return re.sub(r'[ً-ْٰ]|\s+', lambda m: ' ' if m.group().isspace() else '', t)


def scan():
    rows = []
    for p in BODY:
        h = head(p)
        b = BAB.search(h)
        f = FASL.search(h)
        c = CENT.search(h)
        bab = BABN.get(b.group(1)) if b else None
        cent = None
        if bab == 1 and f and FASL_CENT.get(f.group(1)):
            cent = FASL_CENT[f.group(1)]
        elif bab == 2 and f:
            # فصولُ الباب الثاني ثلاثة، على القرون الثاني والثالث والرابع
            cent = {'الأول': 2, 'الثاني': 3, 'الثالث': 4}.get(f.group(1))
        elif bab in (1, 2) and c:
            cent = CENTURY[c.group(1)]
        rows.append({'page': p, 'bab': bab, 'cent': cent})
    # ملء الفراغات: الصفحة الزوجية ترويستُها عامة، فترث ما قبلها
    last = {'bab': None, 'cent': None}
    for r in rows:
        if r['bab'] is None and r['cent'] is None:
            r.update(last)
        else:
            if r['bab'] is None:
                r['bab'] = last['bab']
            if r['cent'] is None and r['bab'] == last['bab']:
                r['cent'] = last['cent']
            last = {'bab': r['bab'], 'cent': r['cent']}
    return rows


def biggest_run(pages, gap=8):
    """أكبرُ حشدٍ متّصل من الصفحات؛ فالقراءةُ الضوئية تُخطئ في ترويسةٍ هنا وهناك،
    فلا يصحّ أخذُ أصغر رقمٍ وأكبره، بل يُؤخذ الحشدُ الغالب."""
    if not pages:
        return None
    pages = sorted(set(pages))
    runs, cur = [], [pages[0], pages[0], 1]
    for p in pages[1:]:
        if p - cur[1] <= gap:
            cur[1], cur[2] = p, cur[2] + 1
        else:
            runs.append(cur)
            cur = [p, p, 1]
    runs.append(cur)
    best = max(runs, key=lambda r: r[2])
    return [best[0], best[1]]


def zones(rows):
    """نطاقاتُ الصفحات لكل (باب، قرن) ولكل باب."""
    byb, byp = {}, {}
    for r in rows:
        if r['bab']:
            byb.setdefault(r['bab'], []).append(r['page'])
            if r['cent']:
                byp.setdefault(f"{r['bab']}:{r['cent']}", []).append(r['page'])
    bab_rng = {k: biggest_run(v) for k, v in byb.items()}
    pair_rng = {k: biggest_run(v) for k, v in byp.items()}
    return {'bab': bab_rng, 'pair': pair_rng}


if __name__ == '__main__':
    rows = scan()
    z = zones(rows)
    json.dump(z, open('out/mujam_zones.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('الأبواب:', z['bab'])
    for k in sorted(z['pair'], key=lambda s: (int(s.split(':')[0]), int(s.split(':')[1]))):
        print('  ', k, z['pair'][k])
