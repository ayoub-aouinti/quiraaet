#!/usr/bin/env python3
"""استخراج أحكام الوقف من كتبٍ تُحصر فيها الآيةُ بين قوسين.

مثل «القطع والائتناف» للنحاس و«إيضاح الوقف والابتداء» لابن الأنباري في نسخ
المكتبة الشاملة. والمخرَج واقعةٌ لا نصّ: لفظُ الموضع القرآني، والمصطلح،
ونفيُه، والقائلُ المنسوب إليه، ورقمُ الصفحة — ولا يُحفظ متنُ الكتاب.

والضبطُ ذاتيّ: كل لفظٍ يُطابَق على فهرس المصحف، فما لم ينطبق سقط.
"""
import json, re, sys
from locator import Locator
from normalize import norm

QUOTE = re.compile(r'﴿([^﴿﴾]{1,400})﴾|\(([^()]{1,200})\)')

# مصطلحات المرتبة. المفتاح صورتُها المطبَّعة، والقيمة (اللفظ، الرمز).
TERMS = {
    'تمام': ('تمام', 'ت'), 'التمام': ('التمام', 'ت'), 'تام': ('تام', 'ت'),
    'تاما': ('تامًّا', 'ت'), 'اتم': ('أتمّ', 'ت'), 'التام': ('التام', 'ت'),
    'كاف': ('كافٍ', 'ك'), 'كافي': ('كافٍ', 'ك'), 'كافيا': ('كافيًا', 'ك'),
    'الكافي': ('الكافي', 'ك'), 'كافه': ('كافية', 'ك'),
    'صالح': ('صالح', 'ص'), 'صالحا': ('صالحًا', 'ص'), 'الصالح': ('الصالح', 'ص'),
    'حسن': ('حسن', 'ح'), 'حسنا': ('حسنًا', 'ح'), 'الحسن': ('الحسن', 'ح'),
}
# «ليس بتمام» و«ليس بكافٍ»: الباء ملتصقة بالمصطلح، فتُقرأ صورةً أخرى له،
# وإلا فات أكثرُ النفي وهو نصفُ ما في هذه الكتب من الأحكام.
for _k, _v in list(TERMS.items()):
    TERMS.setdefault('ب' + _k, _v)
# ألفاظ النفي التي تقلب الحكم إلى منعٍ من الوقف
NEG = {'ليس', 'وليس', 'فليس', 'غير', 'بغير', 'لا', 'ولا', 'لم', 'يجوز'}
# «لا يوقف عليه» ونحوه حكمٌ مستقل بالمنع
FORBID = [
    ('لا يوقف عليه', 'لا يوقف عليه'), ('لا يوقف علي', 'لا يوقف عليه'),
    ('ليس بوقف', 'ليس بوقف'), ('ليس بقطع', 'ليس بقطع'),
    ('ليس بموضع قطع', 'ليس بموضع قطع'), ('لا يتم الكلام', 'لا يتمّ الكلام'),
    ('لم يتم الكلام', 'لم يتمّ الكلام'), ('لا تقف', 'لا تقف'),
]
# القائل: الكتب تنقل أقوال غيرها، فلا يُنسب الحكم إلى صاحب الكتاب بلا بيان
SAYER = re.compile(r'(?:قال|وقال|قول|وقول|مذهب|ومذهب|روى|وروى|حكى|وحكى|أجاز|وأجاز)\s+'
                   r'((?:أبو|أبي|ابن|الأخفش|الفراء|الكسائي|نافع|يعقوب|سيبويه|مجاهد|قتادة|'
                   r'عكرمة|قطرب|محمد|علي|أحمد|الحسن|الزجاج)[ء-ي\s]{0,30})')

WINDOW_AFTER = 12      # كلمات تُفحَص بعد الاقتباس
WINDOW_BEFORE = 8      # وكلمات قبله
# حروفٌ وأفعالٌ تقطع اسمَ القائل، فلا يُلحق به ما ليس منه
STOPW = {'قال', 'وقال', 'إن', 'أن', 'أنها', 'أنه', 'في', 'فيها', 'فقد', 'هو',
         'هذا', 'وهذا', 'عن', 'إلى', 'على', 'لأن', 'ثم', 'وهي', 'يقول', 'كان'}


def tidy_sayer(s):
    toks = re.sub(r'\s+', ' ', s).strip(' ،.').split()
    out = []
    for t in toks[:5]:
        if t in STOPW and out:
            break
        out.append(t)
    return ' '.join(out) or None


def toks_of(s):
    return [t for t in (norm(w) for w in s.split()) if t]


def sura_of(page, starts):
    cur = None
    for p, s in starts:
        if page >= p:
            cur = s
        else:
            break
    return cur


def find_terms(words):
    """كلُّ مصطلحٍ في النافذة، ولكلٍّ نفيُه الخاص.

    لا يصحّ الاكتفاء بأول مصطلح: «كافٍ وليس بتمام» حكمان لا حكمٌ واحد،
    الأولُ إثباتٌ للكفاية والثاني نفيٌ للتمام، فلو أُخذ الأول وحده ضاع
    النفي، ولو نُسب النفيُ إليه انقلب الحكم.
    """
    out = []
    for i, w in enumerate(words):
        if w in TERMS:
            neg = any(words[j] in NEG for j in range(max(0, i - 2), i))
            out.append((TERMS[w], neg, i))
    return out


def find_forbid(text_norm):
    for pat, label in FORBID:
        if pat in text_norm:
            return label
    return None


def extract_page(body, page, sura, loc, state):
    out = []
    for m in QUOTE.finditer(body):
        quote = m.group(1) or m.group(2) or ''
        qt = toks_of(quote)
        if not qt or len(qt) > 25:
            continue
        hits = loc.match_seq(qt)
        loose = False
        if not hits and len(qt) >= 2:
            hits = loc.match_seq_loose(qt)   # الإملائي مقابل العثماني
            loose = bool(hits)
        if not hits:
            continue                      # ليس نصّاً قرآنياً
        after_raw = body[m.end():m.end() + 220]
        before_raw = body[max(0, m.start() - 160):m.start()]
        after = toks_of(after_raw)[:WINDOW_AFTER]
        before = toks_of(before_raw)[-WINDOW_BEFORE:]

        found = [(t, n, 'بعد') for t, n, _ in find_terms(after)]
        if not found:
            found = [(t, n, 'قبل') for t, n, _ in find_terms(before)]
        forbid = find_forbid(' '.join(after[:6])) or find_forbid(' '.join(before[-6:]))
        if not found and forbid is None:
            continue

        # ترجيح الموضع: داخل السورة، ثم بعد آخر موضع مقبول
        ins = [h for h in hits if sura is None or loc.w[h]['sura'] == sura]
        use = ins or hits
        fwd = [h for h in use if h >= state['last'] - 40]
        use2 = fwd or use
        n = len(use2)
        pos = loc.seq_position(use2[0], len(qt))
        if n == 1 and len(qt) >= 2 and ins:
            conf = 'عالية'
        elif n == 1 or len(qt) >= 4:
            conf = 'متوسطة'
        else:
            conf = 'تحتاج مراجعة'
        if loose and conf == 'عالية':
            conf = 'متوسطة'
        if conf != 'تحتاج مراجعة':
            state['last'] = max(state['last'], use2[0])

        say = None
        sm = list(SAYER.finditer(body[:m.start()]))
        if sm and m.start() - sm[-1].end() < 600:
            say = tidy_sayer(sm[-1].group(1))

        items = [((t[0], t[1]), n_, w_) for t, n_, w_ in found]
        if forbid:
            items.append(((forbid, 'لا'), False, 'بعد'))
        for (term_text, sym), neg, where in items:
            out.append({
                'page': page, 'sura_book': sura,
                'quote_words': len(qt),
                'term': ('ليس بـ' + term_text) if neg else term_text,
                'symbol': 'لا' if neg else sym,
                'negated': bool(neg),
                'where': where,
                'sayer': say,
                'seq': pos['end_seq'], 'ayah': f"{pos['sura']}:{pos['ayah']}",
                'sura_name': pos['sura_name'], 'stop_word': pos['stop_word'],
                'candidates': n, 'conf': conf,
            })
    return out


def main(jsonl, suras_json, out_csv):
    loc = Locator('out/words_indexed.json')
    starts = json.load(open(suras_json, encoding='utf-8'))['starts']
    rows, state = [], {'last': -1}
    prev_sura = None
    for line in open(jsonl, encoding='utf-8'):
        rec = json.loads(line)
        pg = rec['page_id']
        s = sura_of(pg, starts)
        if s != prev_sura:
            state['last'] = -1
            prev_sura = s
        rows += extract_page(rec['body'], pg, s, loc, state)
    import csv
    with open(out_csv, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    from collections import Counter
    print('أحكام:', len(rows))
    print('الثقة:', Counter(r['conf'] for r in rows))
    print('المصطلح:', Counter(r['symbol'] for r in rows))
    print('منفيّ:', sum(1 for r in rows if r['negated']))
    print('منسوب لقائل:', sum(1 for r in rows if r['sayer']))


if __name__ == '__main__':
    main(*sys.argv[1:4])
