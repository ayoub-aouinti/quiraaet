#!/usr/bin/env python3
"""استيراد مصحف رواية من ملفات مجمع الملك فهد ومحاذاته على فهرس حفص.

ملفات المجمع بترميز يونيكود قياسي، بخلاف المصاحف المطبوعة بخطوط خاصة.
فيُكتفى بإسقاط رؤوس السور وأرقام الآي، ثم تُحاذى الكلمات.

تُستخرج أيضاً علامات الوقف المضمَّنة في نصّ الرواية، إن وُجدت، مصدراً
مستقلاً باسم الرواية، لأنها علامات مصحفها لا علامات مصحف آخر.
"""
import json, re, sqlite3, sys
from difflib import SequenceMatcher
from normalize import norm

SURA_HEAD = re.compile(r'^\s*سُورَةُ\s+\S+')
AYAH_NUM = re.compile(r'[٠-٩۰-۹]+')

# علامات الوقف المصحفية المضمَّنة في النصّ
MARKS = {
    'ۘ': ('م',   'وقف لازم',     'tam',     False),
    'ۗ': ('قلى', 'الوقف أولى',   'kafi',    True),
    'ۖ': ('صلى', 'الوصل أولى',   'jaiz',    True),
    'ۚ': ('ج',   'وقف جائز',     'jaiz',    False),
    'ۙ': ('لا',  'لا يوقف عليه', 'mamnu',   False),
    'ۛ': ('∴', 'معانقة',    'muanaqa', False),
    'ۜ': ('س',   'سكتة',         'jaiz',    True),
}


def read_words(docx_path):
    """كلمات المصحف، ومع كل كلمة ما تحمله من علامات وقف."""
    import docx
    d = docx.Document(docx_path)
    out = []
    for p in d.paragraphs:
        line = p.text.strip()
        if not line or SURA_HEAD.match(line):
            continue
        for tok in line.split():
            if AYAH_NUM.fullmatch(tok.strip('()[]')):
                continue                      # رقم آية
            tok = AYAH_NUM.sub('', tok)
            n = norm(tok)
            if not n:
                continue
            out.append({'raw': tok, 'n': n,
                        'marks': [c for c in tok if c in MARKS]})
    return out


def align(src, hafs):
    a = [x['n'] for x in src]
    b = [x['n'] for x in hafs]
    sm = SequenceMatcher(None, a, b, autojunk=False)
    pairs = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            pairs += [(i1 + k, hafs[j1 + k]['seq'], 'exact') for k in range(i2 - i1)]
        elif (i2 - i1) == (j2 - j1):
            pairs += [(i1 + k, hafs[j1 + k]['seq'], 'variant') for k in range(i2 - i1)]
        else:
            pairs += [(k, None, 'unmatched') for k in range(i1, i2)]
    return pairs


def main(db, docx_path, riwaya_id, words_indexed):
    hafs = json.load(open(words_indexed, encoding='utf-8'))
    src = read_words(docx_path)
    pairs = align(src, hafs)
    ex = sum(1 for _, _, k in pairs if k == 'exact')
    va = sum(1 for _, _, k in pairs if k == 'variant')
    un = sum(1 for _, _, k in pairs if k == 'unmatched')
    print(f'{riwaya_id}: {len(src)} كلمة · مطابق {ex} · مختلف الرسم {va} · بلا مقابل {un}')

    con = sqlite3.connect(db)
    con.execute('DELETE FROM riwaya_words WHERE riwaya=?', (riwaya_id,))
    con.executemany('INSERT INTO riwaya_words VALUES (?,?,?,?,?)',
                    [(riwaya_id, i, src[i]['raw'], seq, kind) for i, seq, kind in pairs])
    con.execute('UPDATE riwayat SET word_count=?, has_text=1 WHERE id=?',
                (len(src), riwaya_id))

    # علامات الوقف المضمَّنة في هذه الرواية
    marks = []
    for i, seq, kind in pairs:
        if seq is None:
            continue
        for ch in src[i]['marks']:
            sym, term, cat, apx = MARKS[ch]
            marks.append((seq, f'mushaf_{riwaya_id}', f'U+{ord(ch):04X}', sym, term,
                          cat, int(apx), None, None, None, None, 'imported',
                          'يقين — رمز مضمَّن في نصّ الرواية', None))
    if marks:
        con.execute('DELETE FROM rulings WHERE source=?', (f'mushaf_{riwaya_id}',))
        con.executemany('''INSERT OR REPLACE INTO rulings
          (seq,source,raw,symbol,term,category,approx,alt_symbol,alt_term,note,review,
           status,confidence,context) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', marks)
        print(f'   علامات وقف مضمَّنة: {len(marks)}')
    con.commit()
    return len(src), ex, va, un, len(marks)


if __name__ == '__main__':
    main(*sys.argv[1:5])
