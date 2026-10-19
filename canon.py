#!/usr/bin/env python3
"""مقارنة الكلمات حرفاً حرفاً مع حفظ موضع كل حرفٍ في الكلمة الأصلية.

المقارنة على «صورة مختزلة» للكلمة: الحروف والحركات القصيرة والتنوين فقط، مع توحيد
اصطلاحات الخط المغربي (ے ۓ والتنوين المقلوب) وترتيب الألف والتنوين وضبط «أل».
تُسقَط الشدّة والسكون والألف الخنجرية وعلامات الوقف والإمالة الصغرى، لأنها تختلف
ترميزاً بين خطوط المجمع، فلا تُحسَب فرقاً. وهذا يُفوِّت فروقاً حقيقية في هذه
العلامات، فالنتيجة «مرشَّحٌ للمراجعة» لا حكم قراءة.
"""
import re, unicodedata
from difflib import SequenceMatcher
from normalize import norm as _norm

PRE = {'ے': 'ى', 'ۓ': 'ئ', 'ٖ': 'ٍ', 'ٗ': 'ٌ',
       'ٞ': 'ً'}
# لا تُوحَّد الهمزات (أ إ ؤ ئ) لأن إبدالها وتسهيلها من فروش القراءات (يُؤْمِنُونَ/يُومِنُونَ)
FOLD = {'آ': 'ا', 'ٱ': 'ا', 'ى': 'ي', 'ة': 'ه', 'ی': 'ي'}
VOW = set('ًٌٍَُِ')
TANWIN = 'ًٌٍ'
MARK = '[ً-ِْ-ٰٕۖ-ۭ]*'
ART = re.compile('^(%s[وفبكل]?[ً-ِ]?)([اٱ]%s)(ل)(%sّ?[َُِ]?)'
                 % (MARK, MARK, MARK))
WASL = re.compile('^(%s[وفبكل]?[ً-ِ]?)([اٱ])(%s)' % (MARK, MARK))
LLAH = re.compile('(لّ?ِ)(ل)(?:َّ|َّ)')   # لِلَّه ← لِلهِ


def pre(w):
    return ''.join(PRE.get(c, c) for c in w)


def norm(w):
    return _norm(pre(w))


def canon(w):
    """-> قائمة (حرف، موضعه في w) للصورة المختزلة."""
    w = unicodedata.normalize('NFC', w)
    p = pre(w)                       # تحويل حرفٍ بحرف: المواضع محفوظة
    out = [(FOLD.get(c, c), i) for i, c in enumerate(p)]
    # «أل»: تُبقى الألف واللام (وشدّتها) ويُسقَط ضبط الألف الوصلية وحركة اللام المشدّدة
    m = ART.match(p)
    if m:
        keep = list(range(*m.span(1)))
        a0 = m.start(2)
        l0 = m.start(3)
        sh = [i for i in range(m.start(4), m.end(4)) if p[i] == 'ّ']
        idx = keep + [a0, l0] + sh[:1]
        out = [(FOLD.get(p[i], p[i]), i) for i in idx] + out[m.end():]
    else:
        # ألفٌ وصلية في أول الكلمة بغير «أل» (اِ۪صْطَفَيْنَٰهُ/ٱصۡطَفَيۡنَٰهُ): يُسقَط ضبطها فقط
        m = WASL.match(p)
        if m:
            idx = list(range(*m.span(1))) + [m.start(2)]
            out = [(FOLD.get(p[i], p[i]), i) for i in idx] + out[m.end():]
    s = ''.join(c for c, _ in out)
    m2 = LLAH.search(s)
    while m2:
        out = out[:m2.end(2)] + out[m2.end():]      # أسقِط الشدّة والفتحة
        s = ''.join(c for c, _ in out)
        m2 = LLAH.search(s)
    keep = [(c, i) for c, i in out if c in VOW or ('ء' <= c <= 'ي' and c != 'ـ')]
    # ترتيب الألف والتنوين: «اً» و«ًا» سواء
    j = 0
    while j + 1 < len(keep):
        # والياء الأخيرة كالألف: «هُديٗ» (قالون) و«هُدٗى» (حفص) سواء
        if keep[j][0] in 'اي' and keep[j + 1][0] in TANWIN:
            keep[j], keep[j + 1] = keep[j + 1], keep[j]
            j += 2
        else:
            j += 1
    return keep


def vcanon(w):
    return ''.join(c for c, _ in canon(w))


def classify(a, b):
    """same | harakat | rasm — بين كلمتين."""
    if norm(a) != norm(b):
        return 'rasm'
    return 'harakat' if vcanon(a) != vcanon(b) else 'same'


def diff_idx(a, b):
    """مواضع الاختلاف: (في a، في b) كقائمتي أرقام أحرف الكلمتين الأصليتين."""
    ca, cb = canon(a), canon(b)
    sm = SequenceMatcher(None, ''.join(c for c, _ in ca), ''.join(c for c, _ in cb), autojunk=False)
    da, db = set(), set()
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            continue
        if i1 == i2 and ca:                      # إضافة في b: نعلّم الحرف المجاور في a
            da.add(ca[min(i1, len(ca) - 1)][1])
        for i in range(i1, i2):
            da.add(ca[i][1])
        if j1 == j2 and cb:
            db.add(cb[min(j1, len(cb) - 1)][1])
        for j in range(j1, j2):
            db.add(cb[j][1])
    return sorted(da), sorted(db)
