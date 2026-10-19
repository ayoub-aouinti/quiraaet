#!/usr/bin/env python3
"""تطبيع موحّد للرسم العثماني، يستعمله الفهرس والمحدِّد معاً.

الغرض مطابقة الكلمة مهما اختلف ترميز ضبطها أو صور همزتها بين المصادر،
مع الإبقاء على النص الأصلي كما هو في الملف — التطبيع للمقارنة فقط.
"""
import re, unicodedata

# الحركات وعلامات الضبط والتطويل وعلامات التحكم
TASHKEEL = re.compile(r'[ؐ-ًؚ-ٰٟۖ-ۭـ​-‏]')

# توحيد صور الألف والهمزة والياء والتاء المربوطة
FOLD = {
    'ٱ': 'ا',  # ٱ ألف وصل
    'آ': 'ا',  # آ
    'أ': 'ا',  # أ
    'إ': 'ا',  # إ
    'ؤ': 'و',  # ؤ  -> و
    'ئ': 'ي',  # ئ  -> ي
    'ء': '',        # ء المفردة تُحذف
    'ى': 'ي',  # ى  -> ي
    'ة': 'ه',  # ة  -> ه
    'ی': 'ي',
}

ARABIC_ONLY = re.compile(r'[^ء-ي]')
PUNCT = re.compile(r'[﴿﴾«»<>{}‘’“”"\'()\[\]۝]')


def norm(word: str) -> str:
    w = unicodedata.normalize('NFC', word)
    w = TASHKEEL.sub('', w)
    w = ''.join(FOLD.get(ch, ch) for ch in w)
    return ARABIC_ONLY.sub('', w)


def tokens(text: str):
    return [t for t in (norm(x) for x in PUNCT.sub(' ', text).split()) if t]
