#!/usr/bin/env python3
"""نقلُ «جامع الوقوف» من SQLite إلى Postgres.

لا يُصلِح بياناً ولا يُخمِّن: ينقل ما في القاعدة كما هو، بما في ذلك المواضعُ
التي لم يُفهَم رمزُها وهي محفوظةٌ معلَّمةٌ بـreview. ويُثري الجداولَ من ملفّات
التهيئة: حدودُ النسخ وتنبيهاتُها من books.json، وجدولُ المصطلحات من terms.json.

ثم يتحقَّق: يُقابِل عددَ كلِّ جدولٍ على الأصل، ويَعُدَّ المواضعَ لكلِّ مصدر،
ويَرُدَّ خطأً إن اختلف شيء. فالهجرةُ غيرُ المتحقَّقِ منها دَينٌ لا إنجاز.

    python3 db/migrate.py out/waqf.db "postgresql://user:pass@localhost/jamei"
"""
import json, sqlite3, sys
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

ROOT = Path(__file__).resolve().parent.parent

# الفئاتُ العامّة ولونُها، كما في gen/tokens.py — مصدرُها واحدٌ فلا تتفرّق
CATEGORIES = [
    ('tam',     'وقف تام',   'ت',  '#1B5E3F', 1),
    ('kafi',    'وقف كاف',   'ك',  '#1E3A5F', 2),
    ('hasan',   'وقف حسن',   'ح',  '#8A6A1F', 3),
    ('jaiz',    'وقف جائز',  'ج',  '#5A6B5D', 4),
    ('mamnu',   'وقف ممنوع', 'لا', '#8C2F39', 5),
    ('muanaqa', 'معانقة',    '∴',  '#5A4A7A', 6),
]


def load_json(name):
    p = ROOT / name
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}


def main(sqlite_path, dsn):
    src = sqlite3.connect(sqlite_path)
    src.row_factory = sqlite3.Row
    books = load_json('books.json')
    terms = load_json('terms.json')

    pg = psycopg2.connect(dsn)
    cur = pg.cursor()
    cur.execute((ROOT / 'db' / 'schema.sql').read_text(encoding='utf-8'))

    execute_values(cur, 'INSERT INTO categories (id,label,symbol,color,ord) VALUES %s',
                   CATEGORIES)

    # ----- المصادر، مُثراةً من books.json -----
    rows = []
    for r in src.execute('SELECT * FROM sources'):
        meta = books.get(r['id'], {})
        lo, hi = (meta.get('suras') or (None, None))
        caveats = {k: v for k, v in meta.items() if k.startswith('_')}
        rows.append((r['id'], r['name'], r['author'], r['died'],
                     r['kind'] or 'book', r['edition'],
                     bool(r['has_text']), bool(r['verified']), lo, hi,
                     bool(meta.get('owner_unattributed')),
                     meta.get('owner') or [],
                     json.dumps(caveats, ensure_ascii=False)))
    execute_values(cur, '''INSERT INTO sources
        (id,name,author,died,kind,edition,has_text,verified,
         sura_lo,sura_hi,owner_unattributed,owner,caveats) VALUES %s''', rows)

    # ----- الكلمات -----
    words = [(r['seq'], r['sura'], r['sura_name'], r['ayah'], r['wpos'], r['text'])
             for r in src.execute('SELECT * FROM words ORDER BY seq')]
    execute_values(cur, 'INSERT INTO words (seq,sura,sura_name,ayah,wpos,text) VALUES %s',
                   words, page_size=5000)

    # ----- الأحكام: تُنقَل كما هي، والمجهولُ رمزُه يبقى معلَّماً -----
    rul = [(r['seq'], r['source'], r['raw'], r['symbol'], r['term'], r['category'],
            bool(r['approx']), r['alt_symbol'], r['alt_term'], r['note'],
            r['review'], r['status'] or 'proposed', r['confidence'], r['context'])
           for r in src.execute('SELECT * FROM rulings')]
    execute_values(cur, '''INSERT INTO rulings
        (seq,source,raw,symbol,term,category,approx,alt_symbol,alt_term,
         note,review,status,confidence,context) VALUES %s''', rul, page_size=5000)

    # ----- المصطلحات من terms.json -----
    tr = []
    for sid, blk in (terms.get('sources') or {}).items():
        for sym, t in (blk.get('terms') or {}).items():
            tr.append((sid, sym, t['term'], t.get('category'),
                       bool(t.get('approx')), bool(t.get('reviewed'))))
    known = {r[0] for r in rows}
    skipped = [t for t in tr if t[0] not in known]
    tr = [t for t in tr if t[0] in known]
    if tr:
        execute_values(cur, '''INSERT INTO terms
            (source,symbol,term,category,approx,reviewed) VALUES %s''', tr)

    # ----- الروايات -----
    riw = [(r['id'], r['name'], r['line'], r['region'], r['script'],
            r['word_count'] or 0, bool(r['has_text']))
           for r in src.execute('SELECT * FROM riwayat')]
    if riw:
        execute_values(cur, '''INSERT INTO riwayat
            (id,name,line,region,script,word_count,has_text) VALUES %s''', riw)
    rw = [(r['riwaya'], r['pos'], r['text'], r['hafs_seq'], r['align'])
          for r in src.execute('SELECT * FROM riwaya_words')]
    if rw:
        execute_values(cur, '''INSERT INTO riwaya_words
            (riwaya,pos,text,hafs_seq,align) VALUES %s''', rw, page_size=5000)

    pg.commit()

    # ----- التحقُّق: لا يُقال «تمّ» إلا بعد المقابلة -----
    bad = []
    for tbl in ('sources', 'words', 'rulings', 'riwayat', 'riwaya_words'):
        a = src.execute(f'SELECT COUNT(*) FROM {tbl}').fetchone()[0]
        cur.execute(f'SELECT COUNT(*) FROM {tbl}')
        b = cur.fetchone()[0]
        print(f'  {tbl:14s} {a:7d} → {b:7d}' + ('' if a == b else '   ✗ اختلف'))
        if a != b:
            bad.append(tbl)

    a = dict(src.execute('SELECT source,COUNT(*) FROM rulings GROUP BY source').fetchall())
    cur.execute('SELECT source,COUNT(*) FROM rulings GROUP BY source')
    b = dict(cur.fetchall())
    if a != b:
        bad.append('توزيعُ المصادر')
        for k in sorted(set(a) | set(b)):
            if a.get(k) != b.get(k):
                print(f'   ✗ {k}: {a.get(k)} ≠ {b.get(k)}')

    # المواضعُ التي لم يُفهَم رمزُها يجب أن تَعبُر لا أن تسقط
    cur.execute("SELECT COUNT(*) FROM rulings WHERE category IS NULL")
    n_unknown = cur.fetchone()[0]
    a_unknown = src.execute('SELECT COUNT(*) FROM rulings WHERE category IS NULL').fetchone()[0]
    print(f'  مواضعُ لم يُفهَم رمزُها (محفوظةٌ معلَّمة): {a_unknown} → {n_unknown}')
    if a_unknown != n_unknown:
        bad.append('المواضع المجهولة الرمز')

    print(f'  المصطلحات: {len(tr)}' + (f' · تُرك {len(skipped)} لمصدرٍ غير مسجَّل' if skipped else ''))

    if bad:
        pg.close()
        sys.exit('فشلَ التحقُّق في: ' + '، '.join(bad))
    print('تمّ، والعددُ مُطابق.')
    pg.close()


if __name__ == '__main__':
    main(*sys.argv[1:3])
