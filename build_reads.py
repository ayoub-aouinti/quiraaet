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
from canon import diff_idx, canon
from normalize import norm

DATA = 'app/data'
ALL = ['qalun', 'warsh', 'bazzi', 'qunbul', 'duri_a', 'susi', 'hisham', 'ibn_dhakwan', 'shuba', 'hafs',
       'khalaf_h', 'khallad', 'abu_harith', 'duri_k', 'ibn_wardan', 'ibn_jammaz', 'ruways', 'rawh', 'ishaq', 'idris']
MUSH = {'warsh': 'warsh', 'bazzi': 'bazzi', 'qunbul': 'qunbul', 'duri_a': 'duri', 'susi': 'susi',
        'shuba': 'shuba', 'hafs': 'hafs'}                       # الراوي ← معرّف مصحفه
PRIORITY = ['qunbul', 'bazzi', 'warsh', 'susi', 'duri_a', 'shuba', 'hafs']   # ترتيب الاقتباس من الزملاء
OWN_FIRST = ['warsh', 'bazzi', 'qunbul']                        # يُضاف لهم فرق المصحف حيث لا بيان
RNAME = {'hisham': 'هشام عن ابن عامر', 'ibn_dhakwan': 'ابن ذكوان عن ابن عامر', 'khalaf_h': 'خلف عن حمزة',
         'khallad': 'خلّاد عن حمزة', 'abu_harith': 'أبو الحارث عن الكسائي', 'duri_k': 'الدوري عن الكسائي',
         'ibn_wardan': 'ابن وردان عن أبي جعفر', 'ibn_jammaz': 'ابن جمّاز عن أبي جعفر',
         'ruways': 'رويس عن يعقوب', 'rawh': 'روح عن يعقوب', 'ishaq': 'إسحاق عن خلف العاشر',
         'idris': 'إدريس عن خلف العاشر'}


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


def letters(phrase, x):
    dq, dx = diff_idx(phrase, x)
    if len(dq) > 0.6 * max(1, len(phrase.replace(' ', ''))):
        return [], []                    # اختلافُ ترميزٍ عام لا تمييزُ حروف
    return dq, dx


def emit(n, items, stats):
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
                for key in ('x', 'f', 'ap', 'same', 'cond', 'khulf', 'n'):
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
                        if parts and all(parts) and any(p[1] != 0 for p in parts):
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
                        rec['dq'], rec['dx'] = letters(ph, rec['x'])
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
                if rid not in it['r']:
                    it['r'][rid] = {'n': 'إمالة هاء التأنيث وقفاً', 'cond': True}
            if r['bayan'] not in it['b']:
                it['b'].append(r['bayan'])

        # ٢-ب) الأصول المعمَّمة (ميم الجمع، الهمز الساكن، ضم الهاء، المدّ)
        for u in jl('%s/usul/%d.json' % (DATA, n)):
            it = item(u['s'], u['e'])
            it['t'] = it['t'] or 'u'
            for b in u['bk']:
                if b not in it['bk']:
                    it['bk'].append(b)
            for r in u['r']:
                if r['id'] in it['r']:
                    if r.get('n') and r['n'] not in it['r'][r['id']].get('n', ''):
                        it['r'][r['id']]['n'] = (it['r'][r['id']].get('n', '') + ' / ' + r['n']).strip(' /')
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
                if t and t[1] == 1 and q not in covered[rid]:   # الرسم المحض (2) لا يُعدّ خلافَ قراءة
                    dq, dx = letters(qall[q][0], t[0])
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

    stats = {'items': 0}
    for n in range(1, 115):
        emit(n, allitems[n], stats)

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
