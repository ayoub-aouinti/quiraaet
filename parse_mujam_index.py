#!/usr/bin/env python3
"""تفكيك «فهرس الموضوعات» من معجم مصنفات الوقف والابتداء إلى سجلّات.

الفهرس يذكر كل مصنَّف برقمه وعنوانه ومؤلفه وصفحاته في المعجم، تحت عنوان
بابه وفصله، وهو الموضع الوحيد في الكتاب الذي تجتمع فيه المصنفات كلها.

المِرساة المعتمدة في التقطيع هي: «عنوان بين علامتَي اقتباس يتلوه نقطتان»،
لا رقم المدخل، لأن التعرّف الضوئي يُفسد الأرقام الهندية ولا يُفسد الاقتباس.
"""
import json, re, unicodedata

RAW = 'out/mujam_index_raw.txt'
OUT = 'out/mujam_index.json'

RUN_HEAD = re.compile(r'(الفهارس العلمية|معجم مصنفات الوقف|دراسة تاريخية تحليلية)')
PAGE_MARK = re.compile(r'^@@@ PDF (\d+)$')
BIDI = dict.fromkeys(map(ord, '‎‏‪‫‬‭‮⁦⁧⁨⁩'), None)

HEAD_PAT = re.compile(r'(الباب\s+(?:الأول|الثاني|الثالث|الرابع)\s*:'
                      r'|الفصل\s+(?:الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر|الحادي عشر|الثاني عشر)\s*:'
                      r'|الكتب المصنفة في الوقف والابتداء في القرن'
                      r'|خاتمة في\s*:'
                      r'|خاتمة الكتاب)')

# ملاحظة: التعرّف الضوئي يقلب الفاصلة العربية «،» إلى «»»، فلا تُستثنى من داخل العنوان.
# ويفصل المعجمُ العنوانَ عن مؤلفه بنقطتين غالباً، وبفاصلة أو نقطة أحياناً،
# فيُقبل الفصلان معاً، والثاني مشروطٌ بأن يليه ما يدلّ على نسبة الكتاب.
ATTR = (r'ل[ء-ي]|المنسوب|إعداد|بقلم|جمع\b|عرض\b|تأليف|اختصار|نظم\b|شرح\b|'
        r'كلاهما|كلتاهما|ثلاثتها|وجميعها|من إملاء|ترجمة')
ANCHOR = re.compile(r'["“”‟]([^"“”‟\n]{3,300}?)["“”‟]\s*'
                    r'(?:[:：]|[،.؛»]?\s*(?=' + ATTR + r'))')
TAIL_NUM = re.compile(r'[\s٠-٩۰-۹0-9،.\-–_|ضا]{2,}$')

CENTURY_WORDS = {
    'الثاني': 2, 'الثالث': 3, 'الرابع': 4, 'الخامس': 5, 'السادس': 6,
    'السابع': 7, 'الثامن': 8, 'التاسع': 9, 'العاشر': 10,
    'الحادي عشر': 11, 'الثاني عشر': 12, 'الثالث عشر': 13,
    'الرابع عشر': 14, 'الخامس عشر': 15,
}
CENT_RE = re.compile(r'القرن\s+(الحادي عشر|الثاني عشر|الثالث عشر|الرابع عشر|الخامس عشر|'
                     r'الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر)')

# ترتيب فصول الباب الأول كما نصّت عليه مقدمة المؤلف، تصحيحاً لخطأ في طبع الفهرس
FASL_ORDER = {'الأول': None, 'الثاني': 5, 'الثالث': 6, 'الرابع': 7, 'الخامس': 8,
              'السادس': 9, 'السابع': 10, 'الثامن': 11, 'التاسع': 12,
              'العاشر': 13, 'الحادي عشر': 14, 'الثاني عشر': 15}
FASL_NUM = re.compile(r'الفصل\s+(الحادي عشر|الثاني عشر|الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر)')


def clean(s):
    s = s.translate(BIDI)
    s = ''.join(c for c in s if not unicodedata.category(c).startswith('Cf'))
    s = re.sub(r'[ً-ْٰ]', '', s)
    return re.sub(r'\s+', ' ', s).strip()


def strip_tail(s):
    return TAIL_NUM.sub('', s).strip(' .،-–|')


def segments():
    """يقسّم الفهرس إلى مقاطع، كل مقطع عنوانٌ أو نصٌّ تحته."""
    out = []
    pdf_page = None
    buf = []
    ctx = {'bab': None, 'fasl': None, 'century': None}

    def push():
        if buf:
            out.append({'kind': 'text', 'text': ' '.join(buf),
                        'pdf_page': pdf_page, **ctx})
            buf.clear()

    for ln in open(RAW, encoding='utf-8').read().split('\n'):
        m = PAGE_MARK.match(ln.strip())
        if m:
            push()
            pdf_page = int(m.group(1))
            continue
        s = clean(ln)
        if not s or RUN_HEAD.search(s):
            continue
        h = HEAD_PAT.search(s)
        if h:
            push()
            txt = strip_tail(s[h.start():])
            if txt.startswith('الباب'):
                ctx = {'bab': txt, 'fasl': None, 'century': None}
            else:
                ctx = dict(ctx)
                ctx['fasl'] = txt
                c = CENT_RE.search(txt)
                cent = CENTURY_WORDS.get(c.group(1)) if c else None
                if ctx['bab'] and ctx['bab'].startswith('الباب الأول'):
                    f = FASL_NUM.search(txt)
                    if f and FASL_ORDER.get(f.group(1)):
                        cent = FASL_ORDER[f.group(1)]   # ترتيب المقدمة هو الحَكَم
                ctx['century'] = cent
            out.append({'kind': 'head', 'text': txt, 'pdf_page': pdf_page, **ctx})
            continue
        buf.append(s)
    push()
    return out


CARRY = re.compile(r'(كلاهما|كلتاهما|ثلاثتها|ثلاثتهم|أربعتها|كلها|كلّها|جميعها|وجميعها|الأربعة|الثلاثة)')
# كل عنوان في هذا الفن لا يخلو من إحدى هذه الكلمات، فما خلا منها فهو شظيّة سطرٍ لا عنوان
TOPIC = re.compile(r'(وقف|وقوف|ابتدا|مقاطع|مباد|تمام|قطع|ائتناف|استئناف|كلا|كلّا|ماءات|'
                   r'موصول|مفصول|قرآن|مصحف|تلاوة|تجويد|قراء)')
# أرقام الصفحات المبعثرة تتخلّل اسم المؤلف أحياناً، فيُقطع الاسم عند أول كتلة رقمية
NUMBLOB = re.compile(r'[٠-٩۰-۹0-9]')


def drop_pagenums(s):
    """أرقام الصفحات تتخلّل السطور، فتُسقط الكلمات التي تحمل رقماً وحدها."""
    keep = [t for t in s.split()
            if not NUMBLOB.search(t) and t not in ('ض', '|', '--', '_', 'ا')]
    return ' '.join(keep)


CARRY_HEAD = re.compile(r'^(ل?كلاهما|ل?كلتاهما|لها|كلها|لأربعة|الأربعة|الثلاثة|'
                        r'ثلاثتها|جميعها|وجميعها|لاما|لهما)\s+')


def tidy_author(s):
    out = CARRY_HEAD.sub('', drop_pagenums(s).strip(' .،؛-–|'))
    out = re.split(r'\s[-–]\s', out)[0]
    out = re.sub(r'\s*\.\s*$', '', out).strip()
    return out[:140] or None


def parse():
    recs, heads = [], []
    for seg in segments():
        if seg['kind'] == 'head':
            heads.append({k: seg[k] for k in ('text', 'pdf_page', 'bab', 'fasl', 'century')})
            continue
        t = seg['text']
        anchors = list(ANCHOR.finditer(t))
        for i, a in enumerate(anchors):
            end = anchors[i + 1].start() if i + 1 < len(anchors) else len(t)
            rest = strip_tail(t[a.end():end])
            recs.append({
                'title': a.group(1).strip(' :،.'),
                'rest': rest,
                'bab': seg['bab'], 'fasl': seg['fasl'], 'century': seg['century'],
                'pdf_page': seg['pdf_page'],
            })

    # دمج شظايا السطور: عنوانٌ خلا من ألفاظ الفنّ وليس معه مؤلف ليس عنواناً
    merged = []
    for r in recs:
        if merged and not TOPIC.search(r['title']) and not re.search(r'ل[ء-ي]', r['rest'][:40]):
            merged[-1]['title'] += ' ' + r['title']
            merged[-1]['rest'] = r['rest'] or merged[-1]['rest']
            continue
        merged.append(r)
    recs = merged

    # المؤلف من بقية المدخل؛ ومدخلٌ بلا مؤلف يرث مؤلف التالي إذا صرّح بـ«كلاهما»
    MARK = (r'(المنسوب(?:ة)?|نُسبت|نسبت|نُسب|نسب)?\s*'
            r'(ل[ء-ي][^.]{2,170}|إعداد[^.]{2,170}|بقلم[^.]{2,170}|'
            r'جمع[^.]{2,170}|عرض[^.]{2,170}|تأليف[^.]{2,170}|اختصار[^.]{2,170}|'
            r'نظم[^.]{2,170}|من إملاء[^.]{2,170})')
    for r in recs:
        rest = drop_pagenums(r['rest'])
        m = re.search(MARK, rest)
        r['attributed'] = bool(m and m.group(1)) or bool(re.match(r'\s*(المنسوب|نسب)', rest))
        r['author'] = tidy_author(m.group(2)) if m else None
        r['shared'] = bool(CARRY.search(rest))
    for i, r in enumerate(recs):
        if r['author'] is None:
            for j in range(i + 1, min(i + 5, len(recs))):
                if recs[j].get('shared') and recs[j]['author']:
                    r['author'] = recs[j]['author']
                    r['author_inherited'] = True
                    break
    return recs, heads


if __name__ == '__main__':
    recs, heads = parse()
    json.dump({'entries': recs, 'headings': heads}, open(OUT, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('عناوين:', len(heads), '· مداخل:', len(recs),
          '· بمؤلف:', sum(1 for r in recs if r['author']),
          '· بقرن:', sum(1 for r in recs if r['century']))
