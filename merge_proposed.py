#!/usr/bin/env python3
"""دمج المواضع المستخرجة من الكتب في القاعدة، موسومةً بأنها مقترحة.

تبقى منفصلة عن المنقول من ملف الترقيم بحقل status:
    imported  -> منقول من ملف الترقيم (الداني، السجاوندي)
    proposed  -> مستخرج آلياً من نصّ الكتاب، ينتظر اعتماد متخصص
"""
import csv, json, sqlite3, sys, os

TERMS = json.load(open(os.path.join(os.path.dirname(__file__), 'terms.json'), encoding='utf-8'))


def ensure_schema(con):
    cols = [r[1] for r in con.execute('PRAGMA table_info(rulings)')]
    if 'status' not in cols:
        con.execute("ALTER TABLE rulings ADD COLUMN status TEXT DEFAULT 'imported'")
        con.execute("UPDATE rulings SET status='imported' WHERE status IS NULL")
    if 'confidence' not in cols:
        con.execute('ALTER TABLE rulings ADD COLUMN confidence TEXT')
    if 'context' not in cols:
        con.execute('ALTER TABLE rulings ADD COLUMN context TEXT')


def merge(db, src_id, csv_path):
    con = sqlite3.connect(db)
    ensure_schema(con)
    meta = TERMS['sources'][src_id]
    con.execute('INSERT OR REPLACE INTO sources VALUES (?,?,?,?)',
                (src_id, meta['name'], meta['author'], meta['died']))
    rows = list(csv.DictReader(open(csv_path, encoding='utf-8-sig')))
    n = 0
    for r in rows:
        sym = r['الرمز']
        t = meta['terms'].get(sym)
        if not t:
            continue
        con.execute('''INSERT OR REPLACE INTO rulings
            (seq, source, raw, symbol, term, category, approx, alt_symbol, alt_term,
             note, review, status, confidence, context)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                    (int(r['seq']), src_id, r['المصطلح'], sym, t['term'], t['category'],
                     int(t['approx']), None, None, None, None,
                     'proposed', r['الثقة'], r.get('السياق', '')[:300]))
        n += 1
    con.commit()
    print(f'  {meta["name"]}: أُدرج {n} موضعاً مقترحاً')
    return n


if __name__ == '__main__':
    db = sys.argv[1]
    for pair in sys.argv[2:]:
        sid, path = pair.split('=', 1)
        merge(db, sid, path)
