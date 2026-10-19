#!/usr/bin/env python3
"""تنظيف أحكام الوقف وبناء قاعدة البيانات بالبنية ذات الطبقتين.

الطبقة الأولى: الرمز والمصطلح كما ورد في المصدر — لا يُستبدل أبداً.
الطبقة الثانية: فئة عامة للعرض فقط، مع علم approx حين تكون المطابقة تقريبية.
"""
import json, re, sqlite3, csv, sys, os

TERMS = json.load(open(os.path.join(os.path.dirname(__file__), 'terms.json'), encoding='utf-8'))
SOURCES, CATS, TYPOS = TERMS['sources'], TERMS['categories'], TERMS['typos']


def parse_cell(raw, src):
    """يفكّ الخلية إلى: رمز أساسي، رمز بديل، ملاحظة نصية، حالة المراجعة."""
    if not raw:
        return None
    v = re.sub(r'\s+', ' ', str(raw).strip())
    note, review = None, None
    table = SOURCES[src]['terms']

    if v in TYPOS:
        fixed = TYPOS[v]
        if fixed is None:
            return {'raw': v, 'primary': None, 'alt': None, 'note': None,
                    'review': 'قيمة غير مفهومة، تحتاج مراجعة الأصل'}
        note, review = f'صُحّح من «{v}»', 'تصحيح إملائي مقترح'
        v = fixed

    # ملاحظة نصية حرة ملحقة بالرمز: «ت/في الكل إلا مواضع»
    m = re.match(r'^([^/]+)/\s*(.+)$', v)
    alt = None
    if m:
        a, b = m.group(1).strip(), m.group(2).strip()
        if a in table and b in table:
            v, alt = a, b                       # وجهان: ت/ك
        elif a in table:
            v, note = a, (note + ' · ' if note else '') + b   # رمز + تعليق
        else:
            return {'raw': raw, 'primary': None, 'alt': None, 'note': v,
                    'review': 'صيغة مركّبة غير معروفة'}
    elif v not in table:
        if re.search(r'[ء-ي]{3,}', v):
            return {'raw': raw, 'primary': None, 'alt': None, 'note': v,
                    'review': 'نص حرّ بلا رمز'}
        return {'raw': raw, 'primary': None, 'alt': None, 'note': None,
                'review': 'رمز غير معروف'}

    return {'raw': raw, 'primary': v, 'alt': alt, 'note': note, 'review': review}


def enrich(p, src):
    if not p or not p['primary']:
        return p
    t = SOURCES[src]['terms'][p['primary']]
    p['term'] = t['term']
    p['category'] = t['category']
    p['approx'] = t['approx']
    if p['alt']:
        ta = SOURCES[src]['terms'][p['alt']]
        p['alt_term'], p['alt_category'] = ta['term'], ta['category']
    return p


def main(indexed, outdir):
    words = json.load(open(indexed, encoding='utf-8'))
    rulings, review = [], []
    for w in words:
        for src, col in (('dani', 'dani'), ('saj', 'saj')):
            p = enrich(parse_cell(w[col], src), src)
            if not p:
                continue
            rulings.append({
                'seq': w['seq'], 'sura': w['sura'], 'sura_name': w['sura_name'],
                'ayah': w['ayah'], 'wpos': w['wpos'], 'word': w['text'],
                'source': src, **p,
            })
            if p.get('review'):
                review.append({'seq': w['seq'],
                               'الموضع': f"{w['sura_name']} {w['sura']}:{w['ayah']}",
                               'الكلمة': w['text'], 'المصدر': SOURCES[src]['name'],
                               'القيمة في الملف': p['raw'], 'سبب المراجعة': p['review']})

    con = sqlite3.connect(f'{outdir}/waqf.db')
    con.executescript('''
    DROP TABLE IF EXISTS words; DROP TABLE IF EXISTS rulings; DROP TABLE IF EXISTS sources;
    CREATE TABLE words (seq INTEGER PRIMARY KEY, sura INT, sura_name TEXT, ayah INT,
                        wpos INT, text TEXT, conf TEXT);
    CREATE TABLE sources (id TEXT PRIMARY KEY, name TEXT, author TEXT, died TEXT);
    CREATE TABLE rulings (seq INT, source TEXT, raw TEXT, symbol TEXT, term TEXT,
                          category TEXT, approx INT, alt_symbol TEXT, alt_term TEXT,
                          note TEXT, review TEXT,
                          PRIMARY KEY (seq, source));
    CREATE INDEX idx_w ON words(sura, ayah);
    CREATE INDEX idx_r ON rulings(source, category);
    ''')
    con.executemany('INSERT INTO words VALUES (?,?,?,?,?,?,?)',
                    [(w['seq'], w['sura'], w['sura_name'], w['ayah'], w['wpos'],
                      w['text'], w.get('conf')) for w in words])
    con.executemany('INSERT INTO sources VALUES (?,?,?,?)',
                    [(k, v['name'], v['author'], v['died']) for k, v in SOURCES.items()])
    con.executemany('INSERT INTO rulings VALUES (?,?,?,?,?,?,?,?,?,?,?)',
                    [(r['seq'], r['source'], str(r['raw']), r['primary'], r.get('term'),
                      r.get('category'), int(bool(r.get('approx'))), r.get('alt'),
                      r.get('alt_term'), r.get('note'), r.get('review')) for r in rulings])
    con.commit()

    json.dump(rulings, open(f'{outdir}/rulings.json', 'w', encoding='utf-8'), ensure_ascii=False)
    if review:
        with open(f'{outdir}/review_queue.csv', 'w', encoding='utf-8-sig', newline='') as f:
            wri = csv.DictWriter(f, fieldnames=list(review[0].keys()))
            wri.writeheader(); wri.writerows(review)

    ok = sum(1 for r in rulings if r['primary'])
    print(f'أحكام مستخرجة: {len(rulings)}   مفهومة: {ok}   للمراجعة: {len(review)}')
    for s in SOURCES:
        n = sum(1 for r in rulings if r['source'] == s and r['primary'])
        a = sum(1 for r in rulings if r['source'] == s and r.get('approx'))
        print(f"  {SOURCES[s]['name']:<28} {n:>6} حكماً، منها {a} بمطابقة تقريبية")
    return rulings, review


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
