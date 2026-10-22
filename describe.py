#!/usr/bin/env python3
"""وصفٌ موجَزٌ لفرق كلمة الراوي عن كلمة قالون، مستخرَجٌ آلياً من مقابلة الحروف والحركات (لا من نصّ كتاب).

هو توصيفٌ لما يظهر في الكلمتين، وليس حكماً في القراءة؛ فالعلاماتُ التي تسقطها المقارنة (الإمالة والإشمام والمدّ)
لا يكشفها، وتُعرَض الكلمةُ الملوَّنةُ معه دائماً.
"""
import re
from difflib import SequenceMatcher

WAQF = re.compile('[ۖ-ۜ۞۩]')
NAMES = {'ء': 'الهمزة', 'ا': 'الألف', 'ب': 'الباء', 'ت': 'التاء', 'ث': 'الثاء', 'ج': 'الجيم', 'ح': 'الحاء',
         'خ': 'الخاء', 'د': 'الدال', 'ذ': 'الذال', 'ر': 'الراء', 'ز': 'الزاي', 'س': 'السين', 'ش': 'الشين',
         'ص': 'الصاد', 'ض': 'الضاد', 'ط': 'الطاء', 'ظ': 'الظاء', 'ع': 'العين', 'غ': 'الغين', 'ف': 'الفاء',
         'ق': 'القاف', 'ك': 'الكاف', 'ل': 'اللام', 'م': 'الميم', 'ن': 'النون', 'ه': 'الهاء', 'و': 'الواو',
         'ي': 'الياء', 'ة': 'التاء المربوطة'}
LETTER = {'ٱ': 'ا', 'أ': 'ء', 'إ': 'ء', 'ؤ': 'ء', 'ئ': 'ء', 'ى': 'ي', 'ے': 'ي', 'ی': 'ي', 'ک': 'ك'}
VOW = {'َ': 'a', 'ً': 'a', 'ٗ': 'a', 'ُ': 'u', 'ٌ': 'u', 'ٞ': 'u', 'ِ': 'i', 'ٍ': 'i', 'ٖ': 'i', 'ْ': 's', 'ۡ': 's'}
INITIAL_HAMZA = 'همزة الكلمة مرسومة ألفاً'
VN = {'a': 'فتح', 'u': 'ضمّ', 'i': 'كسر', 's': 'سكون'}
VT = {'a': 'الفتح', 'u': 'الضمّ', 'i': 'الكسر'}
VPRO = {'a': 'فتحها', 'u': 'ضمّها', 'i': 'كسرها'}


def tokens(word):
    """[حرف، حركة، شدّة] مع توحيد اصطلاحات الرسم؛ والحرفُ المعلَّم بالدائرة الصغيرة (لا يُنطَق) يُسقَط"""
    T = []
    w = WAQF.sub('', word)
    for ch in w:
        if ch in VOW:
            if T:
                T[-1][1] = VOW[ch]
        elif ch == 'ّ':
            if T:
                T[-1][2] = True
        elif ch in '۟۠':
            if T:
                T.pop()
        elif ch == 'ٰ':
            T.append(['ا', None, False])
        elif ch == 'ۥ':
            T.append(['و', None, False])
        elif ch == 'ۦ':
            T.append(['ي', None, False])
        elif ch == 'ٓ':
            if T and T[-1][0] == 'ء':
                T.append(['ا', None, False])
        elif ch == 'آ':
            T.append(['ء', 'a', False]); T.append(['ا', None, False])
        elif ch in 'ـۣۢٔ':
            continue
        elif 'ً' <= ch <= 'ٟ' or 'ۖ' <= ch <= 'ۭ':
            continue
        elif ch in LETTER or ch in NAMES:
            T.append([LETTER.get(ch, ch), None, False])
    # الألف الوصلية في أول الكلمة: لا حركة لها
    if T and T[0][0] == 'ا':
        T[0][1] = None
    return T


def _vow(a, b):
    return a if a and b and a != b else None


def items(q, x):
    A, B = tokens(q), tokens(x)
    sm = SequenceMatcher(None, [t[0] for t in A], [t[0] for t in B], autojunk=False)
    out = []

    def add(s):
        if s not in out:
            out.append(s)

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                a, b = A[i1 + k], B[j1 + k]
                if a[0] in 'اويء' and a[1] is None and b[1] is None:
                    continue
                last = i1 + k == len(A) - 1
                if last and len(B) > len(A) and B[-1][0] in 'وي' and a[0] in 'مه':
                    continue                  # صلةُ الميم والهاء: يُذكر الإلحاقُ لا تحريكُ الحرف
                if last and a[0] == 'ي' and a[1] and not b[1]:
                    add('إسكان الياء')
                    continue
                if a[1] and b[1] and a[1] != b[1]:
                    nm = NAMES[a[0]]
                    if b[1] == 's':
                        add('إسكان %s' % nm)
                    elif a[1] == 's':
                        add('تحريك %s ب%s' % (nm, VT[b[1]]) if False else 'تحريك %s %s' % (nm, 'بالفتح' if b[1] == 'a' else 'بالضمّ' if b[1] == 'u' else 'بالكسر'))
                    else:
                        add('%s %s بدل %s' % (VN[b[1]], nm, VPRO[a[1]]))
                if a[2] != b[2]:
                    add(('تشديد %s' if b[2] else 'تخفيف %s') % NAMES[a[0]])
        elif tag == 'replace':
            if i2 - i1 == j2 - j1:
                for k in range(i2 - i1):
                    a, b = A[i1 + k][0], B[j1 + k][0]
                    if a == 'ء' and b == 'ا' and i1 + k == 0:
                        add(INITIAL_HAMZA)       # همزةٌ أولَ الكلمة مرسومةٌ ألفاً: ليس إبدالاً (يُحسَم في build_reads بالكلمة السابقة)
                    elif a == 'ء' and b in 'اوي':
                        add('إبدال الهمزة %s' % {'ا': 'ألفاً', 'و': 'واواً', 'ي': 'ياءً'}[b])
                    elif b == 'ء' and a in 'اوي':
                        add('همزة بدل %s' % NAMES[a])
                    else:
                        add('ب%s بدل %s' % (NAMES[b], NAMES[a]))
            else:
                add('اختلاف في حروف الكلمة')
        elif tag == 'delete':
            for t in A[i1:i2]:
                add('حذف %s' % NAMES[t[0]])
        elif tag == 'insert':
            for k, t in enumerate(B[j1:j2]):
                prev = A[i1 - 1][0] if i1 > 0 else ''
                if t[0] in 'وي' and j2 == len(B) and prev == 'ه':
                    add('صلة هاء الضمير ب%s لفظية' % ('ياء' if t[0] == 'ي' else 'واو'))
                elif t[0] in 'وي' and j2 == len(B) and prev == 'م':
                    add('صلة %s ب%s' % (NAMES[prev], NAMES[t[0]]))
                elif t[0] == 'ا':
                    add('إثبات ألف')
                elif t[0] == 'ء':
                    add('زيادة همزة')
                else:
                    add('زيادة %s' % NAMES[t[0]])
    # نقل الحركة: رسمُ ورش يكتب الهمزة المنقولة ألفاً صامتة بلا حركة (اِ۬لَارْضِ) وقد حُرِّك الساكنُ قبلها بحركتها
    if len(A) == len(B):
        for i in range(1, len(A)):
            if (A[i][0] == 'ء' and B[i][0] == 'ا' and B[i][1] is None and A[i - 1][1] == 's' and A[i][1] in 'aui'
                    and B[i - 1][1] == A[i][1] and A[i - 1][0] == B[i - 1][0]):
                mv = {'a': 'بالفتح', 'u': 'بالضمّ', 'i': 'بالكسر'}[A[i][1]]
                out = [t for t in out if t not in ('تحريك %s %s' % (NAMES[A[i - 1][0]], mv), 'إبدال الهمزة ألفاً')]
                if 'نقل حركة الهمزة إلى الساكن قبلها' not in out:
                    out.insert(0, 'نقل حركة الهمزة إلى الساكن قبلها')
    if 'حذف الهمزة' in out and any(t.startswith('تحريك ') for t in out):
        out = [t for t in out if t != 'حذف الهمزة' and not t.startswith('تحريك ')]
        out.insert(0, 'نقل حركة الهمزة إلى الساكن قبلها')
    return out


def has_taqlil(x):
    """علامةُ التقليل في مصحف ورش: نقطةٌ تحت الحرف (U+06EA) في غير الألف الوصلية أول الكلمة"""
    return any(m.start() > 2 or x[:1] not in 'اٱ' for m in re.finditer('۪', x))


def describe(q, x, warsh=False):
    qs, xs = q.split(), x.split()
    out = []
    if len(qs) == len(xs):
        for a, b in zip(qs, xs):
            for t in items(a, b):
                if t not in out:
                    out.append(t)
    else:
        out = items(q.replace(' ', ''), x.replace(' ', ''))
    if warsh and has_taqlil(x):
        out.insert(0, 'التقليل')
    if not out:
        return None
    return '، '.join(out[:3]) + ('، وغيره' if len(out) > 3 else '')


if __name__ == '__main__':
    for a, b in [('وَمَا يُخَٰدِعُونَ', 'وَمَا يَخۡدَعُونَ'), ('يُؤْمِنُونَ', 'يُومِنُونَ'), ('عَلَيْهِمْ', 'عَلَيۡهِمُۥ'),
                 ('يُغْفَرْ لَكُمْ', 'نَّغۡفِرۡ لَكُمۡ'), ('إِنِّيَ أَعْلَمُ', 'إِنِّيٓ أَعۡلَمُ'), ('وَلَا يُقْبَلُ', 'وَلَا تُقۡبَلُ'),
                 ('شِئْتُمَاۖ', 'شِّيتُمَا'), ('وَٰعَدْنَا', 'وَعَدۡنَا'), ('أَبْصَٰرِهِمْ', 'أَبۡصَٰرِهِمُۥ')]:
        print(a, '|', b, '→', describe(a, b))
