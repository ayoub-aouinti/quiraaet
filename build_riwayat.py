#!/usr/bin/env python3
"""بناء طبقة الروايات: نصّ مستقلّ لكل رواية، ومحاذاة بينها.

الروايات تختلف في النصّ نفسه لا في العرض فقط: كلمات ورش ٧٧٨٤٦ وحفص ٧٧٤٣٦،
والفروق في الرسم والعدّ والوقف. فلكل رواية جدول كلماتها الخاصّ، ويُربط
بالفهرس المرجعي (حفص) بجدول محاذاة، لتُعرض أحكام الوقف على أي رواية.

حفص هو الفهرس المرجعي لأن أكثر مصادر الوقف المرقمنة عندنا مبنية عليه.
"""
import json, re, sqlite3, sys
from difflib import SequenceMatcher
from normalize import norm
import extract_hubti as H

RIWAYAT = {
    'hafs':   {'name': 'حفص عن عاصم',      'line': 'عاصم الكوفي',  'region': 'المشرق',  'script': 'عثماني'},
    'warsh':  {'name': 'ورش عن نافع',       'line': 'نافع المدني',  'region': 'المغرب',  'script': 'مغربي'},
    'qalun':  {'name': 'قالون عن نافع',     'line': 'نافع المدني',  'region': 'تونس وليبيا', 'script': 'مغربي'},
    'duri':   {'name': 'الدوري عن أبي عمرو', 'line': 'أبو عمرو البصري', 'region': 'السودان والقرن الأفريقي', 'script': 'عثماني'},
}


def load_warsh(docx_path):
    """كلمات المصحف المغربي بترميزها الأصلي، ومعها علامة الهبطي."""
    return H.read_words(docx_path)


def align_to_hafs(src, hafs_words):
    """يربط كل كلمة في الرواية بكلمة حفص المقابلة، أو يتركها بلا مقابل."""
    a = [x['n'] for x in src]
    b = [x['n'] for x in hafs_words]
    sm = SequenceMatcher(None, a, b, autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal' or (i2 - i1) == (j2 - j1):
            kind = 'exact' if tag == 'equal' else 'variant'
            for k in range(i2 - i1):
                out.append((i1 + k, hafs_words[j1 + k]['seq'], kind))
        else:
            for k in range(i1, i2):
                out.append((k, None, 'unmatched'))
    return out


def main(db, warsh_docx, words_indexed):
    hafs = json.load(open(words_indexed, encoding='utf-8'))
    con = sqlite3.connect(db)
    con.executescript('''
    DROP TABLE IF EXISTS riwayat;
    DROP TABLE IF EXISTS riwaya_words;
    CREATE TABLE riwayat (
      id TEXT PRIMARY KEY, name TEXT, line TEXT, region TEXT, script TEXT,
      word_count INTEGER DEFAULT 0, has_text INTEGER DEFAULT 0);
    CREATE TABLE riwaya_words (
      riwaya TEXT NOT NULL, pos INTEGER NOT NULL,   -- ترتيب الكلمة داخل الرواية
      text TEXT NOT NULL,                            -- النصّ بترميز الرواية
      hafs_seq INTEGER,                              -- المقابل في الفهرس المرجعي
      align TEXT,                                    -- exact | variant | unmatched
      PRIMARY KEY (riwaya, pos));
    CREATE INDEX idx_rw_hafs ON riwaya_words (riwaya, hafs_seq);
    ''')

    for rid, meta in RIWAYAT.items():
        con.execute('INSERT INTO riwayat VALUES (?,?,?,?,?,0,0)',
                    (rid, meta['name'], meta['line'], meta['region'], meta['script']))

    # حفص: الفهرس المرجعي نفسه
    con.executemany('INSERT INTO riwaya_words VALUES (?,?,?,?,?)',
                    [('hafs', w['seq'], w['text'], w['seq'], 'exact') for w in hafs])
    con.execute('UPDATE riwayat SET word_count=?, has_text=1 WHERE id=?', (len(hafs), 'hafs'))
    print(f'حفص: {len(hafs)} كلمة (الفهرس المرجعي)')

    # ورش: من المصحف المحمدي، محاذىً على حفص
    src = load_warsh(warsh_docx)
    pairs = align_to_hafs(src, hafs)
    con.executemany('INSERT INTO riwaya_words VALUES (?,?,?,?,?)',
                    [('warsh', i, src[i]['raw'], seq, kind) for i, seq, kind in pairs])
    con.execute('UPDATE riwayat SET word_count=?, has_text=1 WHERE id=?', (len(src), 'warsh'))
    ex = sum(1 for _, _, k in pairs if k == 'exact')
    un = sum(1 for _, _, k in pairs if k == 'unmatched')
    print(f'ورش: {len(src)} كلمة · مطابقة تامة لحفص {ex} · بلا مقابل {un}')

    con.commit()
    for r in con.execute('SELECT id,name,word_count,has_text FROM riwayat'):
        state = 'نصّ محمّل' if r[3] else 'بلا نصّ — ينتظر الاستيراد'
        print(f'   {r[1]:<22} {r[2]:>7}   {state}')


if __name__ == '__main__':
    main(*sys.argv[1:4])
