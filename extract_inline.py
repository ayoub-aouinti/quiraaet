#!/usr/bin/env python3
"""استخراج مواضع الوقف من الكتب التي تُدمج فيها الآية في الشرح بلا أقواس.

مثل «المقصد» لزكريا الأنصاري و«منار الهدى» للأشموني في نسخ المكتبة الشاملة،
وفيها يأتي الحكم عقب الكلمة الموقوف عليها مباشرة:
    «... لا ريب تام إن رفع هدى بفيه ... للمتقين تام إن جعل الذين ...»

الطريقة: يُبحث عن المصطلح أولاً، ثم يُرتدّ إلى الوراء لأطول تتابع قرآني
ينتهي عنده. هذا يلتقط الاقتباسات ولو كانت كلمة واحدة، بخلاف المسح الأمامي.
"""
import json, re, csv, sys, os
from locator import Locator
from normalize import norm
import readers

# يلتقط الاسم المفرد والمركّب معاً: «البقرة» و«آل عمران» و«ص» و«ق».
# (?<![ء-ي]) يمنع التقاط «السورة» على أنها «سورة»، وهو ما كان
# يُنتج رؤوس سور كاذبة من مثل «آخر السورة تام».
SURA_HEAD = re.compile(
    r'(?<![ء-ي])سورة\s+([ء-ي]{1,15}(?:\s+[ء-ي]{2,15})?)')

# أسماء بديلة تشيع في كتب الوقف
ALIASES = {
    'المؤمن': 40, 'بنيإسرائيل': 17, 'بنياسرائيل': 17, 'الإسرا': 17,
    'حمالسجدة': 41, 'فصلت': 41, 'المصابيح': 41, 'الملائكة': 35,
    'القتال': 47, 'براءة': 9, 'التوبه': 9, 'الأنفال': 8,
    'الدهر': 76, 'الإنسان': 76, 'هلأتى': 76, 'المطفقين': 83,
    'عبس': 80, 'الطلاق': 65, 'التحريم': 66, 'المنافقين': 63,
    'الفاتحه': 1, 'أمالقرآن': 1, 'الحمد': 1, 'المسبحات': 57,
}
MAX_LOOKBACK = 9        # أطول اقتباس يُرتدّ إليه
MIN_LEN = 1             # الكلمة الواحدة تُقبل، لكن بترجيح التسلسل لا بذاتها
FORWARD_WINDOW = 400    # أقصى قفزة أمام الموضع السابق تُقبل بالترتيب

# نفي الحكم: «غير تام» و«ليس بكاف» عكس «تام» و«كاف»، فلا يصحّ تسجيلها حكماً.
# تُلتقط هذه قبل المصطلح فيُسقَط الموضع ويُسجَّل في قائمة المسقَطات.
NEGATION = [tuple(x.split()) for x in (
    'غير', 'ليس', 'وليس', 'لا', 'ولا', 'بغير', 'فليس', 'وإلا', 'والا',
    'ليس ب', 'لم يكن',
)]
NEG_NORM = None         # يُهيّأ عند أول استعمال


def is_negated(toks, i):
    """هل يسبق المصطلحَ نفيٌ؟ يُفحص ما قبله بكلمتين."""
    global NEG_NORM
    if NEG_NORM is None:
        NEG_NORM = {norm(w) for grp in NEGATION for w in grp}
    for back in (1, 2):
        if i - back >= 0 and toks[i - back] in NEG_NORM:
            return True
    return False


def tokenize(text):
    toks, spans = [], []
    for m in re.finditer(r'\S+', text):
        t = norm(m.group())
        if t:
            toks.append(t)
            spans.append((m.start(), m.end()))
    return toks, spans


def build_terms(cfg):
    tmap = {}
    for k, v in cfg['terms'].items():
        key = tuple(norm(x) for x in k.split() if norm(x))
        if key:
            tmap.setdefault(key, (k, v))
    return tmap, max(len(k) for k in tmap)


def sura_marks(text, suras):
    """مواضع رؤوس السور في النصّ، لتُنسب إليها المواضع التالية لها."""
    byname = dict(ALIASES)
    for num, nm in suras.items():
        byname.setdefault(norm(nm), num)
        byname.setdefault(norm(nm.replace(' ', '')), num)
        byname.setdefault(norm(nm).lstrip('ا').lstrip('ل'), num)   # بلا «ال»
    out = []
    for m in SURA_HEAD.finditer(text):
        raw = m.group(1).strip()
        # جرّب الاسم المركّب أولاً، فإن لم يُعرف فأوّل كلمة منه
        for cand in (raw, raw.split()[0]):
            num = byname.get(norm(cand.replace(' ', '')) ) or byname.get(norm(cand))
            if num:
                out.append((m.start(), num, cand))
                break
    return out


# أدوات العطف التي تحمل الحكم إلى مواضع تالية بالحكم نفسه.
# «يفعلون كاف وكذا فإذا رأيتم فيها وما كنتم تكتمون» = أربعة مواضع لا واحد،
# وهذا أكبر مصدر للنقص في الاستخراج إن أُهمل.
CARRY = {'وكذا', 'وكذلك', 'ومثله', 'ومثلها', 'ونظيره', 'وكذاك'}
CARRY_N = {norm(w) for w in CARRY}
MAX_CARRY = 12          # أقصى عدد مواضع تُحمل بعطف واحد


def extract(text, cfg, loc, suras, ocr=False):
    toks, spans = tokenize(text)
    tmap, maxterm = build_terms(cfg)
    heads = sura_marks(text, suras)

    def sura_at(char_pos):
        cur = (None, None)
        for start, num, nm in heads:
            if start < char_pos:
                cur = (num, nm)
            else:
                break
        return cur

    # المرساة: آخر موضع مقبول داخل السورة الجارية. تُصفَّر عند كل رأس سورة،
    # لئلا تفسد مرساةٌ خاطئة كل ما بعدها.
    out, i, last, last_sura = [], 0, [-1], [None]
    BACK_TOL = 60                   # رجوع يسير مقبول: الكتاب يعيد الموضع أحياناً
    while i < len(toks):
        hit = None
        for L in range(min(maxterm, len(toks) - i), 0, -1):
            key = tuple(toks[i:i + L])
            if key in tmap:
                hit = (key, L)
                break
        if not hit:
            i += 1
            continue
        key, L = hit
        term_text, term_sym = tmap[key]

        # «غير تام» نفيٌ لا حكم، و«وليس بوقف» حكمٌ مستقل في جدول المصطلحات.
        if term_sym != 'لا' and is_negated(toks, i):
            i += L
            continue

        cur_sura, cur_name = sura_at(spans[i][0])
        # المرساة تُصفَّر عند كل رأس سورة مرصود، لئلا تفسد مرساةٌ خاطئة كل
        # ما بعدها. جرّبتُ مرساةً عامة لا تُصفَّر فانهارت الحصيلة، لأن الكتب
        # تعود إلى الوراء داخل السورة الواحدة تناقش الوجوه.
        if cur_sura != last_sura[0]:
            last_sura[0], last[0] = cur_sura, -1
        m = loc.match_before(toks, i, MAX_LOOKBACK, sura=cur_sura)
        if not m or m['len'] < MIN_LEN:
            i += L
            continue

        # ترجيح بالتسلسل: هذه الكتب تمشي على ترتيب المصحف، فالموضع التالي
        # يقع بعد سابقه بقليل. هذا يحسم الكلمة الواحدة التي تتكرّر في السورة
        # («رحيم» و«يعلمون»)، وهي كثيرة في اقتباسات هذين الكتابين.
        hits = m['hits']
        ordered = [h for h in hits if last[0] < h <= last[0] + FORWARD_WINDOW]
        by_order = len(ordered) == 1 and len(hits) > 1
        if ordered:
            hits = ordered
        n_hits = len(hits)
        pos = loc.seq_position(hits[0], m['len'])

        # التفرّد أقوى دليل: تتابع لا يرد في القرآن إلا مرة واحدة محسومٌ
        # بذاته، سواء أصاب رأس السورة المرصود أم أخطأه — ورؤوس السور لا
        # تُلتقط كلها، فتقييد المحسوم بها يُسقط آلافاً بلا موجب.
        if n_hits == 1 and (m['in_sura'] or m['len'] >= 2 or by_order):
            conf = 'عالية'
        elif n_hits == 1 or m['len'] >= 4:
            conf = 'متوسطة'
        else:
            conf = 'تحتاج مراجعة'
        # الرجوع الكبير إلى الوراء دليل خطأ، لأن الكتب تمشي على ترتيب المصحف.
        # أما الرجوع اليسير فمقبول، فالكتاب يعيد ذكر الموضع ويناقش وجوهه.
        back_jump = last[0] >= 0 and hits[0] < last[0] - BACK_TOL
        if conf == 'عالية' and back_jump:
            conf = 'تحتاج مراجعة'
        if conf in ('عالية', 'متوسطة') and not back_jump:
            last[0] = max(last[0], hits[0])
        if ocr and conf == 'عالية':
            conf = 'متوسطة'

        ctx_a, ctx_b = spans[max(0, i - m['len'])][0], spans[min(i + L, len(spans) - 1)][1]
        out.append({
            'الاقتباس': text[ctx_a:spans[i - 1][1]][-70:] if i else '',
            'المصطلح': term_text,
            'الرمز': term_sym,
            'السورة في الكتاب': cur_name or '',
            'طول المطابقة': m['len'],
            'عدد المرشحين': n_hits,
            'seq': pos['end_seq'],
            'الموضع': f"{pos['sura_name']} {pos['sura']}:{pos['ayah']}",
            'الوقف بعد': pos['stop_word'],
            'السياق': re.sub(r'\s+', ' ', text[max(0, ctx_a - 40):ctx_b + 60]),
            'الثقة': conf,
            'ملاحظة': 'يخالف ترتيب المصحف' if back_jump else '',
        })
        i += L

        # حمل الحكم على ما بعد «وكذا» و«ومثله»: كل تتابع قرآني تالٍ موضعٌ
        # مستقلّ يحمل الحكم نفسه، حتى ينقطع النصّ القرآني أو يرد مصطلح جديد.
        if i < len(toks) and toks[i] in CARRY_N:
            conj, j, made = spans[i][0], i + 1, 0
            while j < len(toks) and made < MAX_CARRY:
                if any(tuple(toks[j:j + k]) in tmap for k in range(1, maxterm + 1)):
                    break
                best = None
                for ln in range(min(MAX_LOOKBACK, len(toks) - j), 0, -1):
                    hs = loc.match_seq(toks[j:j + ln])
                    if not hs:
                        continue
                    ins = [h for h in hs if cur_sura is None or loc.w[h]['sura'] == cur_sura]
                    fwd = [h for h in (ins or hs) if last[0] < h <= last[0] + FORWARD_WINDOW]
                    if len(fwd) == 1:
                        best = (ln, fwd[0])
                        break
                    if len(ins) == 1 and best is None:
                        best = (ln, ins[0])
                if not best:
                    break
                ln, h = best
                p = loc.seq_position(h, ln)
                out.append({
                    'الاقتباس': text[spans[j][0]:spans[j + ln - 1][1]][:70],
                    'المصطلح': term_text, 'الرمز': term_sym,
                    'السورة في الكتاب': cur_name or '',
                    'طول المطابقة': ln, 'عدد المرشحين': 1,
                    'seq': p['end_seq'],
                    'الموضع': f"{p['sura_name']} {p['sura']}:{p['ayah']}",
                    'الوقف بعد': p['stop_word'],
                    'السياق': re.sub(r'\s+', ' ',
                                     text[max(0, conj - 60):spans[min(j + ln + 2, len(spans) - 1)][1]]),
                    'الثقة': 'عالية' if ln >= 2 else 'متوسطة',
                    'ملاحظة': 'محمول بالعطف',
                })
                last[0] = max(last[0], h)
                j += ln
                made += 1
            i = j
    return out


def main(book, cfg_path, words_indexed, outdir):
    cfg = json.load(open(cfg_path, encoding='utf-8'))
    loc = Locator(words_indexed)
    suras = {w['sura']: w['sura_name'] for w in loc.w}
    print(f'قراءة {os.path.basename(book)} ...')
    text = readers.clean(readers.read(book))
    info = readers.last_read_info()

    rows = extract(text, cfg, loc, suras, ocr=info['ocr_pages'] > 0)
    high = [r for r in rows if r['الثقة'] == 'عالية']
    rest = [r for r in rows if r['الثقة'] != 'عالية']

    base = os.path.join(outdir, cfg['id'])
    for name, data in (('_proposed.csv', high), ('_review.csv', rest)):
        if not data:
            continue
        with open(base + name, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(data)

    print(f"{cfg['name']}: استُخرج {len(rows)} موضعاً")
    print(f'  ثقة عالية: {len(high)}  ->  {cfg["id"]}_proposed.csv')
    print(f'  تحتاج مراجعة: {len(rest)}  ->  {cfg["id"]}_review.csv')
    return rows


if __name__ == '__main__':
    main(*sys.argv[1:5])
