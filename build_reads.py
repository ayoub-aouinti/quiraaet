#!/usr/bin/env python3
"""طبقةُ الخلاف الموحَّدة: app/data/reads/<سورة>.json.

لكل موضعٍ من كلمات قالون (s..e) عنصرٌ فيه رواةٌ يخالفونه، ولكل راوٍ:
  x  كلمةُ قراءته   f  خطُّها (رواية المصحف الذي أُخذت منه)   ap  ≈ مقرَّبةٌ من مصحف راوٍ اتفق معه في الوجه
  same  كقالون (بنصّ المصدر)   dq/dx  الحروف المخالفة في عبارة قالون وفي كلمته   cond/khulf  تقييد/بخلف
و b بيانُ المصدر بلفظه، و u مشكوكٌ في وسمه، و t درجةُ الربط (p: معمَّمٌ على نظير، m: فرقُ مصحف).

مصادر كلمة الراوي بالترتيب: (١) مصحفُه الخاصّ إن وُجد (ورش والبزي وقنبل والدوري والسوسي وشعبة وحفص)،
(٢) نصُّ ملف الخلاف له، (٣) مصحفُ أحد من اتفق معه في الوجه في ذلك الجانب (تقريب ≈)،
(٤) نصُّ ملف الخلاف لأحد من اتفق معه (تقريب ≈). وإلا لا كلمة له: يُعرَض البيانُ وحده.

التعميم: ما أُخذ تقريباً من مصحف زميلٍ ولم يكن مقيَّداً ولا بخلف يُعمَّم على كل موضعٍ فيه الكلمةُ نفسُها
في قالون إن أظهر مصحفُ الزميل في ذلك الموضع التغييرَ عينَه (وسمُ t = p، وفيه ≈).
"""
import json, os, re
from difflib import SequenceMatcher
import unicodedata
from canon import diff_idx, canon, silah_idx
from normalize import norm
from describe import describe, has_taqlil, tokens, INITIAL_HAMZA
from warsh_khulf import load as load_khulf
from build_usul import tarqiq_idx, taghliz_idx, FAW

DATA = 'app/data'
ALL = ['qalun', 'warsh', 'bazzi', 'qunbul', 'duri_a', 'susi', 'hisham', 'ibn_dhakwan', 'shuba', 'hafs',
       'khalaf_h', 'khallad', 'abu_harith', 'duri_k', 'ibn_wardan', 'ibn_jammaz', 'ruways', 'rawh', 'ishaq', 'idris']
MUSH = {'warsh': 'warsh', 'bazzi': 'bazzi', 'qunbul': 'qunbul', 'duri_a': 'duri', 'susi': 'susi',
        'shuba': 'shuba', 'hafs': 'hafs'}                       # الراوي ← معرّف مصحفه
PRIORITY = ['qunbul', 'bazzi', 'warsh', 'susi', 'duri_a', 'shuba', 'hafs']   # ترتيب الاقتباس من الزملاء
IK = ('bazzi', 'qunbul')                                      # ابن كثير: تُلوَّن صلةُ الهاء في مصحفَيهما
OWN_FIRST = ['warsh', 'bazzi', 'qunbul']                        # يُضاف لهم فرق المصحف حيث لا بيان
RNAME = {'hisham': 'هشام عن ابن عامر', 'ibn_dhakwan': 'ابن ذكوان عن ابن عامر', 'khalaf_h': 'خلف عن حمزة',
         'khallad': 'خلّاد عن حمزة', 'abu_harith': 'أبو الحارث عن الكسائي', 'duri_k': 'الدوري عن الكسائي',
         'ibn_wardan': 'ابن وردان عن أبي جعفر', 'ibn_jammaz': 'ابن جمّاز عن أبي جعفر',
         'ruways': 'رويس عن يعقوب', 'rawh': 'روح عن يعقوب', 'ishaq': 'إسحاق عن خلف العاشر',
         'idris': 'إدريس عن خلف العاشر'}


NAMES = {'ورش': ['warsh'], 'البزي': ['bazzi'], 'قنبل': ['qunbul'], 'الدوري': ['duri_a', 'duri_k'], 'السوسي': ['susi'],
         'هشام': ['hisham'], 'ابن ذكوان': ['ibn_dhakwan'], 'شعبة': ['shuba'], 'حفص': ['hafs'], 'خلف': ['khalaf_h'],
         'خلاد': ['khallad'], 'أبو الحارث': ['abu_harith'], 'ابن وردان': ['ibn_wardan'], 'ابن جماز': ['ibn_jammaz'],
         'رويس': ['ruways'], 'روح': ['rawh'], 'إسحاق': ['ishaq'], 'إدريس': ['idris']}


def add_note(rec, text):
    if text and text not in rec.get('n', '') and ('إمالة هاء التأنيث' not in text or 'إمالة هاء التأنيث' not in rec.get('n', '')):
        rec['n'] = (rec.get('n', '') + ' / ' + text).strip(' /')


def bayan_to_notes(it, e):
    """بيانُ ملف الخلاف يصير ملاحظةً أمام الراوي: السطرُ المسمّى لصاحبه، وغيرُ المسمّى لكل من يخالف قالون في الموضع"""
    ids = {r['id']: r for r in e['r']}
    for l in [x.strip() for x in e['b'].splitlines() if x.strip()]:
        m = re.match(r'^([^:]{1,40}?)\s*:\s*(.+)$', l)
        nm = re.sub('[ّ]', '', m.group(1)).strip() if m else None
        if m and nm in NAMES:
            for rid in NAMES[nm]:
                if rid in ids and not ids[rid]['same']:
                    add_note(it['r'][rid], m.group(2).strip())
        else:
            for rid, r in ids.items():
                if not r['same']:
                    add_note(it['r'][rid], l)


def imala_letter(t, i):
    """الألفُ أو الياءُ الممالة بعد الحرف i: ألفٌ خنجرية في عنقوده، وإلا أولُ حرفٍ تالٍ من ا ى ي ے"""
    j = i + 1
    while j < len(t) and not unicodedata.category(t[j]).startswith('L'):
        if t[j] == 'ٰ':
            return j
        j += 1
    return j if j < len(t) and t[j] in 'اىيے' else None


def taqlil_idx(q, x):
    """موضعُ الألف/الياء الممالة في كلمة ورش (بعلامة النقطة تحتَ الحرف قبلها) وفي المقابل من كلمة قالون"""
    base = []
    for m in re.finditer('۪', x):
        i = m.start() - 1
        while i > 0 and not unicodedata.category(x[i]).startswith('L'):
            i -= 1
        if i >= 0 and not (i == 0 and x[0] in 'اٱ'):
            base.append(i)
    cq, cx = canon(q), canon(x)
    sm = SequenceMatcher(None, ''.join(c for c, _ in cq), ''.join(c for c, _ in cx), autojunk=False)
    pos_x = {p_: k for k, (c, p_) in enumerate(cx)}
    dq, dx = set(), set()
    for b in base:
        a = imala_letter(x, b)
        if a is not None:
            dx.add(a)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != 'equal':
            continue
        for b in base:
            k = pos_x.get(b)
            if k is not None and j1 <= k < j2:
                a = imala_letter(q, cq[i1 + k - j1][1])
                if a is not None:
                    dq.add(a)
    return sorted(dq), sorted(dx)


def skel(w):
    t = norm(w)
    return t[:1] + re.sub('[اويى]', '', t[1:]) if t else ''


def cstr(w):
    return ''.join(c for c, _ in canon(w))


def jl(p):
    return json.load(open(p, encoding='utf-8'))


def dump(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(o, f, ensure_ascii=False, separators=(',', ':'))


def gidx(a, rid):
    for i, g in enumerate(a['g']):
        if rid in g.get('r', []):
            return i
    for i, g in enumerate(a['g']):
        if g.get('rest'):
            return i
    return -1


def letters(phrase, x, sil=False):
    dq, dx = diff_idx(phrase, x)
    if len(dq) > 0.6 * max(1, len(phrase.replace(' ', ''))):
        return [], []                    # اختلافُ ترميزٍ عام لا تمييزُ حروف
    if sil:                              # صلة هاء الضمير (ابن كثير): علامتُها تُسقِطها الصورةُ المختزلة
        da, db = silah_idx(phrase, x)
        dq, dx = sorted(set(dq) | set(da)), sorted(set(dx) | set(db))
    return dq, dx


KHULF = {}
for _w, _v in load_khulf().items():
    KHULF.setdefault(skel(_w), set()).update(_v)


def emit(n, items, stats, phrase=None, prevw=None):
    out = []
    for k in sorted(items):
        it = items[k]
        if not it['r']:
            continue
        rs = []
        for rid in ALL:
            if rid in it['r']:
                r = it['r'][rid]
                d = {'id': rid}
                if rid == 'warsh' and r.get('x') and r.get('f') == 'warsh' and it['s'] == it['e'] and has_taqlil(r['x']):
                    # بخلفٍ عنه: إن اتفقت كلُّ ملاحظات الكتاب على ذلك للكلمة (وإلا لم يُوسَم لتعارض الملاحظات)
                    qw = phrase(it['s'], it['e'])
                    vals = set()
                    for v in {skel(qw), skel(qw[1:]) if qw[:1] in 'وفبلك' else ''}:
                        vals |= KHULF.get(v, set())
                    if vals == {True}:
                        r = dict(r, khulf=True)
                    tq, tx = taqlil_idx(qw, r['x'])
                    r = dict(r, dqa=tq, dxa=tx)
                if r.get('x') and not r.get('same') and phrase and r.get('f') != 'qalun' and r.get('src') != 'd':
                    # وصفُ فرق الكلمة من مقابلة الحروف (لا من بيان ملف الخلاف)، ويُقدَّم على ما عمّمته الأصول
                    qw_ = phrase(it['s'], it['e'])
                    dq_, dx_ = silah_idx(qw_, r['x'])
                    if rid in IK and r['f'] in IK and dx_ and cstr(qw_) == cstr(r['x']):
                        # الفرق صلةُ الهاء وحدها: يُوصَف بها (ولا يُترك لوصف الحروف فيخلط ما أسقطته الصورةُ المختزلة)
                        kinds = sorted({'بياء لفظية' if r['x'][i] == 'ۦ' else 'بواو لفظية' for i in dx_})
                        dsc = 'صلة هاء الضمير ' + ' وب'.join(kinds) if len(kinds) == 1 else 'صلة هاء الضمير ' + ' و'.join(kinds)
                    else:
                        dsc = describe(qw_, r['x'], warsh=(rid == 'warsh'))
                    if dsc and INITIAL_HAMZA in dsc and rid == 'warsh' and prevw and it['s'] == it['e']:
                        # الهمزة الأولى مرسومةٌ ألفاً: إن تغيّر آخرُ الكلمة السابقة في مصحف ورش (ساكنٌ حُرِّك) فهو نقلُ حركتها إليه
                        pq, pw = prevw(it['s'])
                        A_, B_ = tokens(pq), tokens(pw)
                        if A_ and B_ and A_[-1][1] == 's' and B_[-1][1] in ('a', 'u', 'i') and A_[-1][0] == B_[-1][0]:
                            dsc = dsc.replace(INITIAL_HAMZA, 'نقل حركة الهمزة إلى الساكن قبلها (آخر الكلمة السابقة)')
                    if not r.get('n') or (dsc and dsc not in r['n']):
                        r = dict(r, n=' / '.join(x for x in (dsc or ('' if r.get('n') else 'فرق في ضبط الكلمة'), r.get('n')) if x))
                for key in ('x', 'f', 'ap', 'same', 'cond', 'khulf', 'n', 'dqa', 'dxa'):
                    if r.get(key):
                        d[key] = r[key]
                if r.get('dq'):
                    d['dq'] = r['dq']
                if r.get('dx'):
                    d['dx'] = r['dx']
                rs.append(d)
        out.append({'s': it['s'], 'e': it['e'], 't': it['t'], 'u': it['u'], 'r': rs, 'b': it['b'], 'bk': it.get('bk', [])})
    stats['items'] += len(out)
    dump('%s/reads/%d.json' % (DATA, n), out)


def main():
    # مصاحف الرواة: q ← (نص، تصنيف)
    mw = {}
    for rid in set(MUSH.values()):
        m = {}
        for n in range(1, 115):
            for _, ws in jl('%s/riw/%s/%d.json' % (DATA, rid, n))['ayat']:
                for w in ws:
                    if w[1] and w[1] not in m:
                        m[w[1]] = (w[0], w[2])
        mw[rid] = m
    qall = {}
    for n in range(1, 115):
        for _, ws in jl('%s/qalun/%d.json' % (DATA, n))['ayat']:
            for s, t in ws:
                qall[s] = (t, n)

    # مواضع إمالة هاء التأنيث وقفاً (الكسائي): ملفٌّ مستقلٌّ من ملفات الخلاف
    ha = {}
    for r in json.load(open('out/khilaf_linked.json', encoding='utf-8'))['linked']:
        if 'مواضع إمالة هاء التأنيث' in r['file'] and r['links']:
            ha.setdefault(r['sura'], []).append(r)
    allitems, prop = {}, {}
    for n in range(1, 115):
        qseqs = sorted(s for s, (t, nn) in qall.items() if nn == n)
        items = {}

        def item(s, e):
            return items.setdefault((s, e), {'s': s, 'e': e, 't': None, 'u': False, 'r': {}, 'b': [], 'bk': []})

        def phrase(s, e):
            return ' '.join(qall[i][0] for i in range(s, e + 1) if i in qall)

        # ١) ملفات الخلاف: كلمةُ القراءة منصوصة
        for e in jl('%s/khilaf/%d.json' % (DATA, n)):
            it = item(e['s'], e['e'])
            it['t'] = it['t'] or e['t']
            if e['b'] not in it['b']:
                it['b'].append(e['b'])
            if e['t'] in ('exact', 'rasm'):
                it.setdefault('db', []).append(e['b'])
            for r in e['r']:
                it['r'][r['id']] = {'x': None if r['same'] else r['x'], 'f': 'hafs', 'same': bool(r['same']),
                                    'dq': r['dq'], 'dx': r['dx'], 'src': 'd'}
            bayan_to_notes(it, e)
        docs = {k: dict(v['r']) for k, v in items.items()}

        # ٢) المداخل المسنَدة إلى كتب القراءات: من يخالف قالون في كل جانب
        for E in jl('%s/badur/%d.json' % (DATA, n)):
            s, e = E['s'], E['e']
            it = item(s, e)
            it['u'] = it['u'] or E['u']
            ph = phrase(s, e)

            def qeff(a):
                """مرجعُ قالون في الجانب. إن كان «بخلفٍ عنه» وكان نصُّه في المصحف يخالف كلمةَ زميلٍ في مجموعته
                المنصوصة فوجهُه الأول هو وجهُ «الباقين» (كصلة ميم الجمع)، والمنصوصُ ثانيه؛ وإلا بقي كما نُصّ."""
                q = a['q']
                if q >= 0 and 'qalun' in a.get('kh', []):
                    rest_i = next((i for i, gg in enumerate(a['g']) if gg.get('rest')), -1)
                    if rest_i >= 0 and rest_i != q:
                        for m in a['g'][q].get('r', []):
                            mid = MUSH.get(m)
                            parts = [mw[mid].get(x) for x in range(s, e + 1)] if mid else None
                            if parts and all(parts):
                                return (rest_i, q) if cstr(' '.join(p_[0] for p_ in parts)) != cstr(ph) else (q, -1)
                return q, -1

            q0 = re.match(r'^"\s*([^"]*?)\s*"', E['t'])
            okq = False
            if q0 and s == e:
                toks = [x for x in re.split('[،,؛]', q0.group(1))[0].split() if x != 'معا']
                a_, b_ = norm(toks[0]) if toks else '', norm(qall[s][0])
                okq = (len(toks) == 1 and skel(toks[0]) == skel(qall[s][0]) and a_[:1] == b_[:1]
                       and a_[-1:] == b_[-1:])
                if re.search('آخر الربع|آخر السورة|الممال|المدغم|الكبير|الصغير', E['t']):
                    okq = False                    # قوائم مجمَّعة: بيانُها لكلماتٍ شتّى لا للكلمة المقتبسة
                rest = E['t'][q0.end():]
                nq = rest.find('"')
                portion = re.sub(r'\s+', ' ', rest if nq < 0 else rest[:nq])
            # فقراتُ الكتاب تلصق عدّة مداخل مقتبسة: يُقتصَر على ما قبل أول اقتباسٍ تالٍ بياناً وجوانب
            bay, own = E['t'], None
            if q0:
                rest0 = E['t'][q0.end():]
                nq0 = rest0.find('"')
                seg = rest0 if nq0 < 0 else rest0[:nq0]
                own = re.sub(r'\s+', ' ', seg)
                bay = (E['t'][:q0.end()] + seg).strip()
            if bay not in it['bk']:
                it['bk'].append(bay)          # نصُّ الكتاب يُحفَظ في البيانات ولا تعرضه الواجهة
            AS = [a for a in E['a']
                  if own is None or not [g['snip'] for g in a['g'] if g.get('snip')]
                  or any(re.sub(r'\s+', ' ', g['snip']) in own for g in a['g'] if g.get('snip'))]
            for rid in ALL:
                if rid == 'qalun':
                    continue
                diff_aspects = [a for a in AS if qeff(a)[0] >= 0 and gidx(a, rid) >= 0 and gidx(a, rid) != qeff(a)[0]]
                if not diff_aspects:
                    continue
                rec = it['r'].get(rid)
                cond = any(rid in gg.get('cond', []) for a in AS for gg in a['g'])
                snip = a0 = None
                a0 = diff_aspects[0]
                snip = a0['g'][gidx(a0, rid)].get('snip')
                if not (rec and (rec['x'] or rec['same'])):
                    rec = {'x': None, 'f': None}
                    a = diff_aspects[0]
                    g = a['g'][gidx(a, rid)]
                    named = {x for gg in a['g'] for x in gg.get('r', [])}
                    mates = g.get('r', []) if not g.get('rest') else [x for x in ALL if x not in named]
                    mates = [m for m in mates if m != rid]

                    def mush_text(who):
                        mid = MUSH.get(who)
                        if not mid:
                            return None
                        parts = [mw[mid].get(q) for q in range(s, e + 1)]
                        if parts and all(parts) and (any(p[1] != 0 for p in parts) or (
                                mid in IK and silah_idx(ph, ' '.join(p[0] for p in parts))[0])):
                            return ' '.join(p[0] for p in parts), mid
                        return None

                    if rid in MUSH:
                        got = mush_text(rid)
                        if got:
                            rec['x'], rec['f'] = got
                    if not rec['x']:
                        for m in sorted([m for m in mates if m in MUSH], key=PRIORITY.index):
                            got = mush_text(m)
                            if got:
                                rec['x'], rec['f'], rec['ap'] = got[0], got[1], m
                                if s == e and not cond and rid not in E.get('k', []):
                                    prop.setdefault((rid, qall[s][0]), (got[0], got[1], m))
                                break
                    if not rec['x']:
                        for m in mates:
                            d = docs.get((s, e), {}).get(m)
                            if d and d.get('x'):
                                rec['x'], rec['f'], rec['ap'] = d['x'], 'hafs', m
                                break
                    if rec['x']:
                        rec['dq'], rec['dx'] = letters(ph, rec['x'], rec['f'] in IK)
                    it['r'][rid] = rec
                if snip and okq and re.sub(r'\s+', ' ', snip) in portion:
                    it['r'][rid].setdefault('sn', snip)
                if cond:
                    it['r'][rid]['cond'] = True
                if rid in E.get('k', []):
                    it['r'][rid]['khulf'] = True

            # وجهُ قالون الثاني: يُعرَض بجانب من قرؤوا به (لا يُلوَّن: هو المرجع)
            for a in AS:
                qe, q2 = qeff(a)
                if q2 >= 0:
                    for m in a['g'][q2].get('r', []):
                        rr = it['r'].get(m)
                        if m != 'qalun' and rr and rr.get('x'):
                            it['r']['qalun'] = {'x': rr['x'], 'f': rr.get('f'), 'dq': rr.get('dq', []),
                                                'dx': rr.get('dx', []), 'n': 'وجهه الثاني', 'khulf': True}
                            break

        for r in ha.get(n, []):
            _, s0, e0, tier0, _ = r['links'][0]
            it = item(s0, e0)
            it['t'] = it['t'] or tier0
            for rid in ('abu_harith', 'duri_k'):
                rec = it['r'].setdefault(rid, {})
                if 'إمالة هاء التأنيث' not in rec.get('n', ''):
                    rec['n'] = (rec.get('n', '') + ' / إمالة هاء التأنيث وقفاً').strip(' /')
                rec['cond'] = True               # البيان لهذين الراويين لا للكلمة كلها

        # ٢-ب) الأصول المعمَّمة (ميم الجمع، الهمز الساكن، ضم الهاء، المدّ)
        for u in jl('%s/usul/%d.json' % (DATA, n)):
            it = item(u['s'], u['e'])
            it['t'] = it['t'] or 'u'
            for b in u['bk']:
                if b not in it['bk']:
                    it['bk'].append(b)
            for r in u['r']:
                if r['id'] in IK and u['s'] == u['e'] and 'صلة هاء الضمير' in r.get('n', ''):
                    # العبارةُ المتعدّدة الكلمات التي ذكرها الكتاب تشمل الكلمة: تُضاف الملاحظةُ إليها بدل بطاقةٍ ثانية
                    cov_k = [k for k, v in items.items() if k[0] < k[1] and k[0] <= u['s'] <= k[1] and r['id'] in v['r']
                             and v['r'][r['id']].get('x') and not v['r'][r['id']].get('same')]
                    if cov_k:
                        ex = items[cov_k[0]]['r'][r['id']]
                        if r['n'] not in ex.get('n', ''):
                            ex['n'] = (ex.get('n', '') + ' / ' + r['n']).strip(' /')
                        continue
                if r['id'] in it['r']:
                    ex = it['r'][r['id']]
                    if r.get('n') and r['n'] not in ex.get('n', ''):
                        ex['n'] = (ex.get('n', '') + ' / ' + r['n']).strip(' /')
                    if r['id'] in IK and r.get('x') and not ex.get('same') and not ex.get('x'):
                        ex.update({k: r[k] for k in ('x', 'f', 'dq', 'dx')})
                    if r['id'] == 'warsh' and r.get('x') and not ex.get('same'):
                        if not ex.get('x'):
                            ex.update({k: r[k] for k in ('x', 'f', 'dq', 'dx')})
                        elif u['s'] == u['e']:
                            # كلمةُ ورش من مصحفه: تُلوَّن فيها الراءُ واللام بالكشف على صورتها هي
                            ix = (tarqiq_idx(ex['x']) if 'ترقيق الراء' in r['n'] else []) +                                  (taghliz_idx(ex['x']) if 'تغليظ اللام' in r['n'] else [])
                            ex['dx'] = sorted(set(ex.get('dx', [])) | set(ix))
                            ex['dq'] = sorted(set(ex.get('dq', [])) | set(r['dq']))
                    continue
                it['r'][r['id']] = {k: v for k, v in r.items() if k != 'id'}

        # ٣) فرقُ المصحف لورش والبزي وقنبل حيث لا إدخال لهم
        covered = {rid: set() for rid in OWN_FIRST}
        for (s, e), it in items.items():
            for rid in OWN_FIRST:
                r = it['r'].get(rid)
                if r and not r.get('same'):
                    covered[rid].update(range(s, e + 1))
        for q in qseqs:
            for rid in OWN_FIRST:
                t = mw[MUSH[rid]].get(q)
                if t and (t[1] == 1 or (rid in IK and silah_idx(qall[q][0], t[0])[0])) and q in covered[rid]:
                    # البند موجودٌ بلا كلمةٍ للراوي (من أصلٍ معمَّم): تُكتب كلمتُه من مصحفه ويُلوَّن موضعُ الفرق
                    r0 = items.get((q, q), {}).get('r', {}).get(rid)
                    if r0 and not r0.get('x') and not r0.get('same'):
                        r0['x'], r0['f'] = t[0], MUSH[rid]
                        r0['dq'], r0['dx'] = letters(qall[q][0], t[0], rid in IK)
                if t and (t[1] == 1 or (rid in IK and silah_idx(qall[q][0], t[0])[0])) and q not in covered[rid]:
                    # الرسم المحض (2) لا يُعدّ خلافَ قراءة؛ وصلةُ الهاء في مصحف ابن كثير فرقٌ تُسقِطه الصورةُ المختزلة
                    dq, dx = letters(qall[q][0], t[0], rid in IK)
                    it = item(q, q)
                    it['t'] = it['t'] or 'm'
                    it['r'][rid] = {'x': t[0], 'f': MUSH[rid], 'same': False, 'dq': dq, 'dx': dx}
        allitems[n] = items

    # ٤) التعميم على النظائر
    added = 0
    for n in range(1, 115):
        items = allitems[n]
        have = {}
        for (s, e), it in items.items():
            for rid, r in it['r'].items():
                if not r.get('same'):
                    have.setdefault(rid, set()).update(range(s, e + 1))
        by_text = {}
        for (rid, qt), v in prop.items():
            by_text.setdefault(qt, []).append((rid, v))
        for q in sorted(s for s, (t, nn) in qall.items() if nn == n):
            for rid, (x, f, mate) in by_text.get(qall[q][0], []):
                if q in have.get(rid, ()):
                    continue
                mt = mw[MUSH[mate]].get(q)
                if not mt or mt[1] == 0 or mt[0] != x:
                    continue                       # مصحف الزميل لا يُظهر التغيير نفسه هنا
                dq, dx = letters(qall[q][0], x)
                it = items.setdefault((q, q), {'s': q, 'e': q, 't': None, 'u': False, 'r': {}, 'b': [], 'bk': []})
                it['t'] = it['t'] or 'p'
                it['r'][rid] = {'x': x, 'f': f, 'ap': mate, 'dq': dq, 'dx': dx}
                have.setdefault(rid, set()).add(q)
                added += 1

    # ٥) الوقف على الهمز (حمزة وخلف وخلاد وهشام) والإمالة والتقليل: الحكمُ تابعٌ لصورة الكلمة،
    #    فيُعمَّم على كل موضعٍ فيه الكلمةُ نفسُها من موضعٍ نُصَّ فيه عليه (ببيانه حرفياً)
    SHORT = {'warsh': 'ورش', 'bazzi': 'البزي', 'qunbul': 'قنبل', 'duri_a': 'الدوري', 'susi': 'السوسي',
             'hisham': 'هشام', 'ibn_dhakwan': 'ابن ذكوان', 'shuba': 'شعبة', 'hafs': 'حفص', 'khalaf_h': 'خلف',
             'khallad': 'خلاد', 'abu_harith': 'أبو الحارث', 'duri_k': 'الدوري', 'ibn_wardan': 'ابن وردان',
             'ibn_jammaz': 'ابن جماز', 'ruways': 'رويس', 'rawh': 'روح', 'ishaq': 'إسحاق', 'idris': 'إدريس'}
    IMALA = re.compile('إمال|أمال|تقليل|التقليل')
    HAMZ = re.compile('تسهيل|إبدال|ابدال|نقل|حذف|بين بين|روم|إشمام|الهمز|همز')
    WAQF_R = {'khalaf_h', 'khallad', 'hisham'}
    MARKS = re.compile(r'[ۖ-ۜ۞۩\s]')

    def hamza_inside(t):
        # الوقف يؤثّر في الهمز المتوسط والمتطرف لا في الأول
        ls = [c for c in MARKS.sub('', t) if 'ء' <= c <= 'ي']
        return any(c in 'ءأإؤئ' and (i >= 2 or (i >= 1 and i == len(ls) - 1)) for i, c in enumerate(ls))

    def wkey(t):
        return MARKS.sub('', t)

    def texts_for(it, rid):
        out = []
        if it['r'][rid].get('sn'):
            out.append((it['r'][rid]['sn'], False))
        for b in (it.get('db', []) if it['r'][rid].get('src') == 'd' else []):
            lines = [l.strip() for l in b.splitlines() if l.strip()]
            named = [l for l in lines if any(l.startswith(v + ':') or l.startswith(v + ' :') for v in SHORT.values())]
            if named:
                if SHORT[rid] == 'الدوري' and 'duri_a' in it['r'] and 'duri_k' in it['r']:
                    continue                      # الدوريان معاً: لا يُعرَف أيّهما
                out += [(l.split(':', 1)[1].strip(), True) for l in named if l.startswith(SHORT[rid])]
            else:
                out.append((b, True))
        return out

    seeds = {}
    for n in range(1, 115):
        for (s, e), it in allitems[n].items():
            if s != e or s not in qall:
                continue
            for rid, rec in it['r'].items():
                if rec.get('same'):
                    continue
                for T, fromd in texts_for(it, rid):
                    kinds = []
                    if IMALA.search(T):
                        kinds.append('imala')
                    if rid in WAQF_R and 'وقف' in T and HAMZ.search(T) and hamza_inside(qall[s][0]):
                        kinds.append('waqf')
                    for k in kinds:
                        seeds.setdefault((rid, k, wkey(qall[s][0])), (T, rec.get('x'), rec.get('f'), fromd))
    by_word = {}
    for (rid, k, w), v in seeds.items():
        by_word.setdefault(w, []).append((rid, k, v))
    added2 = 0
    for n in range(1, 115):
        items = allitems[n]
        have = {}
        for (s, e), it in items.items():
            for rid, r in it['r'].items():
                if not r.get('same'):
                    have.setdefault(rid, set()).update(range(s, e + 1))
        for q in sorted(sq for sq, (t, nn) in qall.items() if nn == n):
            for rid, k, (T, x, f, fromd) in by_word.get(wkey(qall[q][0]), []):
                if q in have.get(rid, ()):
                    continue
                it = items.setdefault((q, q), {'s': q, 'e': q, 't': None, 'u': False, 'r': {}, 'b': [], 'bk': []})
                it['t'] = it['t'] or 'w'
                rec = {'n': 'إمالة أو تقليل' if k == 'imala' else 'وقفاً على الهمز'}
                if x:
                    rec['x'], rec['f'] = x, f
                if k == 'waqf':
                    rec['cond'] = True
                it['r'][rid] = rec
                tgt = it['b'] if fromd else it['bk']      # بيانُ ملف الخلاف يُعرَض؛ ونصُّ الكتاب يُحفَظ فقط
                if T not in tgt:
                    tgt.append(T)
                have.setdefault(rid, set()).add(q)
                added2 += 1

    # الحروف المقطَّعة: لا خلاف لابن كثير (البزي وقنبل) فيها، فيُزال ما نتج من فرق رسم المصحف
    for n, k in FAW.items():
        fs = set(sorted(sq for sq, (t, nn) in qall.items() if nn == n)[:k])
        for (s_, e_), it in allitems[n].items():
            if s_ == e_ and s_ in fs:
                for rid in ('bazzi', 'qunbul'):
                    it['r'].pop(rid, None)
            elif fs & set(range(s_, e_ + 1)):
                for rid in ('ibn_wardan', 'ibn_jammaz'):     # صفوفٌ مجملة بلا وجه: يغني عنها السكت المنصوص
                    if rid in it['r'] and not it['r'][rid].get('n') and not it['r'][rid].get('x'):
                        del it['r'][rid]

    stats = {'items': 0}
    for n in range(1, 115):
        emit(n, allitems[n], stats, lambda a, b: ' '.join(qall[i][0] for i in range(a, b + 1) if i in qall),
             lambda q: (qall.get(q - 1, ('', 0))[0], (mw['warsh'].get(q - 1) or ('',))[0]))

    # فروق الرسم المحض (تصنيف 2) التي لا يسندها بيانٌ تُزال من مصاحف الروايات: لا علاقة لها بالقراءة
    cov = {rid: set() for rid in MUSH}
    for n in range(1, 115):
        for (s_, e_), it in allitems[n].items():
            for rid, r in it['r'].items():
                if rid in MUSH and not r.get('same'):
                    cov[rid].update(range(s_, e_ + 1))
    dropped = 0
    for rid, mid in MUSH.items():
        for n in range(1, 115):
            path = '%s/riw/%s/%d.json' % (DATA, mid, n)
            d = jl(path)
            ch = False
            for ay in d['ayat']:
                for w in ay[1]:
                    if w[2] == 2 and w[1] not in cov[rid]:
                        w[2] = 0
                        del w[3:]
                        ch = True
                        dropped += 1
                    elif rid in IK and w[1] in cov[rid] and w[1] in qall:
                        da_, db_ = silah_idx(qall[w[1]][0], w[0])     # صلة الهاء: يُعلَّم الحرفُ في مصحف الرواية
                        if db_ and w[2] != 2:
                            have_d = w[3] if len(w) > 3 else []
                            if w[2] == 0 or not set(db_) <= set(have_d):
                                w[2] = 1
                                w[3:] = [sorted(set(have_d) | set(db_))]
                                ch = True
            if ch:
                dump(path, d)

    # قائمة الروايات: لمن لا مصحف له يُعرَض مصحفُ قالون معدَّلاً
    meta = jl(DATA + '/meta.json')
    have_m = {r['id']: r for r in meta.get('fonts_src', meta['riwayat'])}
    riw = []
    for g in meta['groups']:
        for r in g['readers']:
            rid = r['id']
            if rid == 'qalun':
                riw.append({**have_m['qalun'], 'reader': 'qalun'})
            elif rid in MUSH:
                riw.append({**have_m[MUSH[rid]], 'reader': rid, 'mush': MUSH[rid]})
            else:
                riw.append({'id': rid, 'reader': rid, 'name': RNAME[rid], 'font': have_m['qalun']['font'],
                            'bsm': have_m['qalun']['bsm'], 'ref': False, 'mush': None})
    meta['fonts_src'] = list(have_m.values())
    meta['riwayat'] = riw
    meta['fonts'] = [{'id': r['id'], 'font': r['font']} for r in have_m.values()]
    dump(DATA + '/meta.json', meta)
    print('عناصر الخلاف الموحَّدة:', stats['items'], '| معمَّمة على نظائر:', added, '| وقف/إمالة معمَّمة:', added2, '| فروق رسم محضٍ أُزيلت:', dropped)


if __name__ == '__main__':
    main()
