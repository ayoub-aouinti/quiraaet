#!/usr/bin/env python3
"""تحديد موضع كل مصنَّف في متن المعجم، ثم استخراج ما صرّح به المؤلف عن حاله.

يُبنى المتنُ كلّه نصّاً واحداً متصلاً، ويُحدَّد لكل مدخلٍ موضعُ عنوانه فيه،
فيكون نطاقُه ما بين عنوانه وعنوان الذي يليه. ثم يُلتمس في نطاقه أولُ لفظٍ
من ألفاظ المؤلف الصريحة في بيان الحال، فيكون هو الحال، ويُحفظ شاهدُه.

ولا يُستنبط شيء: ما خلا نطاقُه من تصريحٍ يُترك «لم يُعثر على تصريح».
"""
import bisect, json, re, unicodedata
import ocr_pdf as O

OCR_DIR = 'ocr/mujam'
BODY = range(30, 2432)
MAX_CHARS = 12000     # أقصى ما يُفحص من نصّ المدخل الواحد (نحو خمس صفحات)
NEAR = 12000          # ولا يُعتدّ بشاهدٍ أبعدَ من هذا عن العنوان

FOLD = str.maketrans({'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا', 'ى': 'ي', 'ئ': 'ي',
                      'ؤ': 'و', 'ة': 'ه', 'ـ': ''})
DIAC = re.compile(r'[ؐ-ًؚ-ْٰۖ-ۭ]')
NONAR = re.compile(r'[^ء-ي\s]')

STATE_RULES = [
    ('مفقود', r'(في عداد المفقود|ما زال مفقود|وهو مفقود|والكتاب مفقود|الكتاب مفقود|'
              r'كتاب مفقود|كتيب مفقود|رساله مفقوده|في حكم المفقود|لم يصل الينا|'
              r'لم تصل الينا|لم اقف له علي نسخه|لم اقف لها علي نسخه|'
              r'لم اقف علي نسخه منه|ولم اعثر له علي نسخه|'
              r'الكتاب المفقود|كتابه المفقود|وهو من المفقود)'),
    # عبارةٌ عن المؤلف لا عن الكتاب: لم يصل إليه، وقد يكون مطبوعاً
    ('لم يقف عليه المؤلف', r'(لم يتيسر لي الوقوف علي|ولم اتمكن من الوقوف علي|'
                           r'ولم اطلع علي)'),
    ('محقَّق', r'(طبع بتحقيق|وحققه|حققه الدكتور|بتحقيق الدكتور|دراسه وتحقيق|'
               r'تحقيقا ودراسه|رساله ماجستير|رساله دكتوراه|اطروحه دكتوراه|'
               r'نال بها درجه)'),
    ('مطبوع', r'(وقد طبع|وطبع الكتاب|وطبعه|طبعاته|طبعتاه|صدرت الطبعه|الطبعه الاولي|'
              r'الطبعه الثاني|وقد نشر|نشرته دار|صدر عن دار|طبع في|وهو مطبوع|'
              r'الكتاب مطبوع|طبع ضمن|نشرتها|مطبوع بتحقيق|وقد طبعه)'),
    ('مخطوط', r'(نسخه خطيه|نسخ خطيه|النسخ الخطيه|نسخه الخطيه|نسخته الخطيه|'
              r'محفوظه بمكتبه|محفوظ بمكتبه|النسخه المحفوظه|نسخه محفوظه|'
              r'ضمن مجموع|مصوره عن نسخه|يوجد منه نسخه|توجد منه نسخه|يوجد منه نسخ)'),
]
STATE_RE = [(k, re.compile(p)) for k, p in STATE_RULES]


def soft(s):
    """تجريدٌ خفيف: يُسقط التشكيل ويوحّد الألف والياء، ويبقي الحروف العربية."""
    s = DIAC.sub('', unicodedata.normalize('NFKC', s)).translate(FOLD)
    return re.sub(r'\s+', ' ', NONAR.sub(' ', s)).strip()


def build_corpus():
    """نصُّ المتن كلّه متصلاً، مع جدولٍ يردّ كل موضعٍ إلى صفحته."""
    parts, offsets, pgs = [], [], []
    pos = 0
    for p in BODY:
        t = O.text(OCR_DIR, p)
        if not t.strip():
            continue
        s = soft(t) + ' '
        parts.append(s)
        offsets.append(pos)
        pgs.append(p)
        pos += len(s)
    return ''.join(parts), offsets, pgs


def page_of(off, offsets, pgs):
    i = bisect.bisect_right(offsets, off) - 1
    return pgs[max(0, i)]


def _occurrences(corpus, key, start, limit=60, stop=None):
    out = []
    stop = len(corpus) if stop is None else stop
    p = corpus.find(key, start, stop)
    while p >= 0 and len(out) < limit:
        out.append(p)
        p = corpus.find(key, p + 1, stop)
    return out


def span_of(pages_rng, offsets, pgs, total):
    if not pages_rng:
        return None
    i = bisect.bisect_left(pgs, pages_rng[0])
    j = bisect.bisect_right(pgs, pages_rng[1])
    lo = offsets[i] if i < len(offsets) else 0
    hi = offsets[j] if j < len(offsets) else total
    return (lo, hi) if hi > lo else None


def zone_bounds(e, zmap, offsets, pgs, total):
    """حدودُ البحث عن المدخل: فصلُه أولاً، ثم بابُه، ثم الكتابُ كله."""
    b = e.get('bab') or ''
    bab = (1 if b.startswith('الباب الأول') else 2 if b.startswith('الباب الثاني')
           else 3 if b.startswith('الباب الثالث') else 4 if b.startswith('الباب الرابع')
           else None)
    out = []
    if bab:
        for r in (zmap['pair'].get(f"{bab}:{e.get('century')}"),
                  zmap['bab'].get(str(bab))):
            s = span_of(r, offsets, pgs, total)
            if s:
                out.append(s)
    out.append((0, total))
    return out


def locate(entries, corpus, zmap, offsets, pgs):
    """موضعُ عنوان كل مدخل في المتن.

    العناوين في هذا الفنّ يكثر تكرارها («كتاب الوقف والابتداء» مثلاً)، فلا
    يكفي العنوان وحده؛ ولذلك يُقصر البحثُ على فصل المدخل من الكتاب — وحدودُه
    مأخوذةٌ من ترويسات الصفحات — ويُرجَّح الموضعُ الذي يقارنه اسمُ المؤلف.
    """
    total = len(corpus)
    cursor = {}
    for e in entries:
        toks = soft(e['title']).split()
        atoks = [t for t in soft(e.get('author') or '').split() if len(t) > 2]
        aname = ' '.join(atoks[:2]) if atoks else None
        hit, scope = None, None
        for depth, (lo, hi) in enumerate(zone_bounds(e, zmap, offsets, pgs, total)):
            start = max(lo, cursor.get((lo, hi), lo))
            for k in (7, 5, 4, 3, 2):
                if len(toks) < k:
                    continue
                key = ' '.join(toks[:k])
                if len(key) < 9:
                    continue
                cands = _occurrences(corpus, key, start, stop=hi) \
                    or _occurrences(corpus, key, lo, stop=hi)
                if not cands:
                    continue
                if aname:
                    for p in cands:
                        if aname in corpus[max(lo, p - 500):min(hi, p + 600)]:
                            hit = p
                            break
                if hit is None and k >= 4 and depth == 0:
                    hit = cands[0]           # داخل فصله، العنوانُ وحده يكفي
                if hit is not None:
                    break
            if hit is None and atoks and len(toks) >= 2:
                akey = ' '.join(atoks[:3])
                tkey = ' '.join(toks[:3] if len(toks) >= 3 else toks)
                if len(akey) >= 12 and len(tkey) >= 8:
                    for p in _occurrences(corpus, akey, start, limit=80, stop=hi):
                        w0, w1 = max(lo, p - 1500), min(hi, p + 1500)
                        q = corpus.find(tkey, w0, w1)
                        if q >= 0:
                            hit = q
                            break
            if hit is not None:
                scope = depth
                cursor[(lo, hi)] = hit
                break
        e['offset'] = hit
        e['scope'] = scope          # 0 = داخل فصله · 1 = داخل بابه · 2 = الكتاب كله
    return entries


def states(entries, corpus, offsets, pgs):
    offs = [e['offset'] for e in entries]
    for i, e in enumerate(entries):
        o = e['offset']
        e.update(state=None, evidence=[], label=None, body_page=None)
        if o is None:
            continue
        e['body_page'] = page_of(o, offsets, pgs)
        nxt = next((x for x in offs[i + 1:] if x is not None and x > o), None)
        end = min(nxt if nxt else o + MAX_CHARS, o + MAX_CHARS, len(corpus))
        seg = corpus[o:end]
        hits = []
        for name, rx in STATE_RE:
            m = rx.search(seg[:NEAR])     # ما بعُد عن العنوان كثيراً لا يُوثق بنسبته إليه
            if m:
                a, b = max(0, m.start() - 90), min(len(seg), m.end() + 90)
                hits.append((m.start(), name, seg[a:b].strip()))
        hits.sort()
        e['state'] = [h[1] for h in hits]
        e['evidence'] = [{'state': h[1], 'quote': h[2]} for h in hits]
        e['span_chars'] = end - o
        # لا تُرجَّح حالٌ على حال: يُذكر كلُّ ما صرّح به المتن في نطاق المدخل.
        # و«لم يقف عليه المؤلف» خبرٌ عن المؤلف لا عن الكتاب، فلا يُذكر مع غيره.
        order = ['مطبوع', 'محقَّق', 'مخطوط', 'مفقود']
        got = [k for k in order if k in e['state']]
        if got:
            e['label'] = ' · '.join(got)
        elif 'لم يقف عليه المؤلف' in e['state']:
            e['label'] = 'لم يقف عليه المؤلف'
    return entries


if __name__ == '__main__':
    d = json.load(open('out/mujam_index.json', encoding='utf-8'))
    zmap = json.load(open('out/mujam_zones.json', encoding='utf-8'))
    corpus, offsets, pgs = build_corpus()
    print('صفحات المتن المقروءة:', len(pgs), '· حروف:', len(corpus))
    ent = states(locate(d['entries'], corpus, zmap, offsets, pgs),
                 corpus, offsets, pgs)
    d['entries'] = ent
    json.dump(d, open('out/mujam_index.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    from collections import Counter
    print('مواضع في المتن:', sum(1 for e in ent if e['offset'] is not None), '/', len(ent))
    print('نطاق التحديد:', Counter(e.get('scope') for e in ent))
    print(Counter(e['label'] for e in ent))
