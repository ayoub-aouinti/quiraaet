#!/usr/bin/env python3
"""كلماتُ التقليل لورش التي نُصّ فيها على «بخلف عنه»، مستخرَجةٌ من قوائم «الممال» في مداخل الكتاب.
تُستعمَل وسماً داخلياً فقط (لا يُعرَض نصُّ الكتاب): الكلمةُ المختزلة ← مجموعة القيم المرصودة {True (بخلف), False}.
والوسمُ لا يُعتمَد إلا حيث لا تتعارض الملاحظات (القيمة {True} وحدها)."""
import json, re
from normalize import norm

VERB = re.compile(r'أمال\S*|يميل\S*|بالإمالة|قلل\S*|يقلل\S*|بالتقليل|والتقليل|لا تقليل|أماله')
STOP = {'معا', 'عند', 'الوقف', 'لدى', 'عليه', 'عليها', 'عليهما', 'كله', 'كلها', 'الثلاثة', 'الأربعة', 'الخمسة',
        'الجميع', 'ذلك', 'لفظ', 'نحو', 'ومثله', 'مثله', 'كذلك', 'على', 'في', 'وقفا', 'ثم', 'و', 'التي', 'بعد',
        'الياء', 'الألف'}
KHULF = re.compile(r'ورش\s+(?:بخلف|بالخلاف)')


def load():
    res = {}
    for l in open('out/badur_entries.jsonl', encoding='utf-8'):
        t = json.loads(l)['t']
        if 'الممال' not in t:
            continue
        sec = re.split('المدغم', t[t.index('الممال'):])[0]
        pending = []
        for seg in re.split(r'[،.\n\r]+', sec):
            seg = seg.strip()
            if not seg:
                continue
            m = VERB.search(seg)
            head = seg[:m.start()] if m else seg
            words = [w for w in re.findall(r'[ء-ي]+', head) if w not in STOP and len(w) > 1]
            if not m:
                pending += words
                continue
            words = pending + words
            pending = []
            tail = seg[m.start():]
            if 'ورش' not in tail:
                continue
            kh = bool(KHULF.search(tail))
            for w in words:
                res.setdefault(norm(w), set()).add(kh)
    return res


if __name__ == '__main__':
    r = load()
    print(len(r), sum(1 for v in r.values() if v == {True}), sum(1 for v in r.values() if v == {True, False}))
    print([k for k, v in r.items() if v == {True, False}])
