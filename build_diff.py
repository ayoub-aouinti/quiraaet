#!/usr/bin/env python3
"""فروق الروايات مقابل قالون (المرجع) كلمةً كلمة، وحرفاً حرفاً داخل الكلمة.

المرجع هو قالون. تُحاذى كلمات كل رواية أخرى عليه مباشرةً (لا عبر حفص)،
ثم تُصنَّف كل كلمة:

  same     لا فرق
  rasm     فرق في حروف الرسم               (موثوق: يُلوَّن)
  harakat  الحروف واحدة والحركات تختلف     (مرشَّح: يحتاج مراجعة)
  added    كلمة في الرواية لا مقابل لها في قالون
  missing  كلمة في قالون لا مقابل لها في الرواية

تنبيه المنهج: ضبطُ الورشي في القاعدة بترميز الخط لا بيونيكود قياسي، فمقارنة
حركاته غير موثوقة، فيُكتفى فيه بفرق الرسم. أما الدوري وحفص فبيونيكود فيُقارَن
ضبطهما. ولا يُنسَب فرقٌ إلى قارئ بعينه هنا: هذا فرقُ نصٍّ لا حكمُ قراءة.
"""
import json, sqlite3, sys, unicodedata
from difflib import SequenceMatcher
from normalize import norm

SKIP = {'warsh'}  # الضبط بترميز الخط: فرق الرسم فقط
VOW = set('ًٌٍَُِ')   # فتحة ضمة كسرة وتنوينات
MAP = {'ٱ': 'ا', 'أ': 'ا', 'إ': 'ا', 'آ': 'ا',
       'ؤ': 'و', 'ئ': 'ي', 'ى': 'ي', 'ة': 'ه',
       'ی': 'ي'}


def vcanon(w):
    """الحروف والحركات القصيرة فقط؛ تُسقَط الشدّة والسكون والألف الخنجرية وعلامات الوقف."""
    w = unicodedata.normalize('NFC', w)
    out = []
    for ch in w:
        ch = MAP.get(ch, ch)
        if ch in VOW or 'ء' <= ch <= 'ي':
            out.append(ch)
    return ''.join(out)


def spans(a, b):
    """مواضع الاختلاف في a (قالون) و b (الرواية) على مستوى الحرف: (i1,i2,j1,j2)."""
    sm = SequenceMatcher(None, a, b, autojunk=False)
    return [(i1, i2, j1, j2) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != 'equal']


def classify(q, o):
    if norm(q) != norm(o):
        return 'rasm'
    return 'harakat' if vcanon(q) != vcanon(o) else 'same'


def main(db):
    con = sqlite3.connect(db)
    ref = con.execute("SELECT pos,text FROM riwaya_words WHERE riwaya='qalun' ORDER BY pos").fetchall()
    rn = [norm(t) or t for _, t in ref]
    con.executescript("""
    DROP TABLE IF EXISTS qalun_diff;
    CREATE TABLE qalun_diff (
      riwaya TEXT NOT NULL, qpos INTEGER, opos INTEGER,
      kind TEXT NOT NULL,        -- rasm | harakat | added | missing
      qtext TEXT, otext TEXT,
      spans TEXT,                -- json [[i1,i2,j1,j2],...] على vcanon (حركات) أو على النص (رسم)
      reliable INTEGER NOT NULL  -- 0 = ضبط بترميز الخط
    );
    CREATE INDEX idx_qd ON qalun_diff (riwaya, qpos);
    """)
    for rid, in con.execute("SELECT id FROM riwayat WHERE id!='qalun' AND has_text=1").fetchall():
        oth = con.execute("SELECT pos,text FROM riwaya_words WHERE riwaya=? ORDER BY pos", (rid,)).fetchall()
        on = [norm(t) or t for _, t in oth]
        sm = SequenceMatcher(None, rn, on, autojunk=False)
        rows, cnt = [], {}
        rel = 0 if rid in SKIP else 1

        def add(kind, qi, oi, sp=None):
            cnt[kind] = cnt.get(kind, 0) + 1
            rows.append((rid, ref[qi][0] if qi is not None else None,
                         oth[oi][0] if oi is not None else None, kind,
                         ref[qi][1] if qi is not None else None,
                         oth[oi][1] if oi is not None else None,
                         json.dumps(sp) if sp else None, rel))

        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == 'equal':
                for k in range(i2 - i1):
                    q, o = ref[i1 + k][1], oth[j1 + k][1]
                    if rid in SKIP:
                        continue
                    if classify(q, o) == 'harakat':
                        add('harakat', i1 + k, j1 + k, spans(vcanon(q), vcanon(o)))
                continue
            n = min(i2 - i1, j2 - j1)
            for k in range(n):
                q, o = ref[i1 + k][1], oth[j1 + k][1]
                add('rasm', i1 + k, j1 + k, spans(norm(q), norm(o)))
            for k in range(n, i2 - i1):
                add('missing', i1 + k, None)
            for k in range(n, j2 - j1):
                add('added', None, j1 + k)
        con.executemany('INSERT INTO qalun_diff VALUES (?,?,?,?,?,?,?,?)', rows)
        print(rid, len(oth), 'كلمة', cnt, 'ضبط موثوق' if rel else 'رسم فقط')
    con.commit()


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'out/waqf.db')
