#!/usr/bin/env python3
"""كلمات رواية من ملف المجمع (.doc): سورة وآية وموضع، وحدود الأسطر والصفحات.

بنية الملف (كما يكتبها Word): عنوان كل سورة «سُورَةُ X» ينتهي بـ \\r، ثم سطر
البسملة، ثم النصّ. رقم الآية يلي آيتها (رمزٌ منفصل). و\\x0b نهاية سطرٍ في المصحف
المطبوع، و\\x0c نهاية صفحة، و\\x08 علامةُ قسمٍ تتناثر في النصّ فتُهمَل.
"""
import re
from read_doc import read_doc
from normalize import norm

DIGITS = re.compile(r'^[0-9٠-٩]+$')   # بعض الملفات تخلط الأرقام اللاتينية بالهندية
AR2 = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')
CTRL = re.compile('[\x00-\x07\x0e-\x1f]')
HEAD = re.compile('سُورَةُ ([^\r\x0b\x0c\x08]{2,40})\r')
SPLIT = re.compile('(\x0b|\x0c|\\s+)')


def riwaya_words(doc):
    """-> (أسماء السور كما في الملف، الكلمات). كلمة: seq,sura,ayah,wpos,text,lb,pb."""
    text = CTRL.sub(' ', read_doc(doc))
    heads = list(HEAD.finditer(text))
    suras, words = [], []
    line_break = page_break = False
    for n, m in enumerate(heads, 1):
        end = heads[n].start() if n < len(heads) else len(text)
        body = text[m.end():end].replace('\x08', ' ')
        suras.append(m.group(1).strip())
        # سطر البسملة: يُسقَط إلا إن كان له رقم (الفاتحة عند بعض الروايات)
        first, sep, rest = body.partition('\r')
        if sep and norm(first).startswith('بسم') and not any(DIGITS.match(t) for t in first.split()):
            body = rest
        buf, wpos = [], 0
        for tok in SPLIT.split(body.replace('\r', ' ')):
            if tok == '\x0b':
                line_break = True
            elif tok == '\x0c':
                page_break = True
            elif not tok or tok.isspace():
                continue
            elif DIGITS.match(tok):
                for w in buf:
                    w['ayah'] = int(tok.translate(AR2))
                words.extend(buf)
                buf, wpos = [], 0
            else:
                wpos += 1
                buf.append({'sura': n, 'ayah': 0, 'wpos': wpos, 'text': tok,
                            'lb': line_break, 'pb': page_break})
                line_break = page_break = False
        words.extend(buf)       # كلمات بلا رقم بعدها: تبقى آية 0 ويُنبَّه عليها
    for i, w in enumerate(words, 1):
        w['seq'] = i
    return suras, words


def basmala(doc):
    """سطر البسملة كما في ملف الرواية (أول سطر بعد عنوان سورة البقرة)."""
    text = CTRL.sub(' ', read_doc(doc))
    m = list(HEAD.finditer(text))[1]
    line = text[m.end():].split('\r')[0]
    return ' '.join(line.replace('\x08', ' ').replace('\x0b', ' ').split())
