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
import json, os
from canon import diff_idx

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
        out.append({'s': it['s'], 'e': it['e'], 't': it['t'], 'u': it['u'], 'r': rs, 'b': it['b']})
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

    allitems, prop = {}, {}
    for n in range(1, 115):
        qseqs = sorted(s for s, (t, nn) in qall.items() if nn == n)
        items = {}

        def item(s, e):
            return items.setdefault((s, e), {'s': s, 'e': e, 't': None, 'u': False, 'r': {}, 'b': []})

        def phrase(s, e):
            return ' '.join(qall[i][0] for i in range(s, e + 1) if i in qall)

        # ١) ملفات الخلاف: كلمةُ القراءة منصوصة
        for e in jl('%s/khilaf/%d.json' % (DATA, n)):
            it = item(e['s'], e['e'])
            it['t'] = it['t'] or e['t']
            if e['b'] not in it['b']:
                it['b'].append(e['b'])
            for r in e['r']:
                it['r'][r['id']] = {'x': None if r['same'] else r['x'], 'f': 'hafs', 'same': bool(r['same']),
                                    'dq': r['dq'], 'dx': r['dx']}
        docs = {k: dict(v['r']) for k, v in items.items()}

        # ٢) المداخل المسنَدة إلى كتب القراءات: من يخالف قالون في كل جانب
        for E in jl('%s/badur/%d.json' % (DATA, n)):
            s, e = E['s'], E['e']
            it = item(s, e)
            it['u'] = it['u'] or E['u']
            if E['t'] not in it['b']:
                it['b'].append(E['t'])
            ph = phrase(s, e)
            for rid in ALL:
                if rid == 'qalun':
                    continue
                diff_aspects = [a for a in E['a'] if a['q'] >= 0 and gidx(a, rid) >= 0 and gidx(a, rid) != a['q']]
                if not diff_aspects:
                    continue
                rec = it['r'].get(rid)
                cond = any(rid in gg.get('cond', []) for a in E['a'] for gg in a['g'])
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
                if cond:
                    it['r'][rid]['cond'] = True
                if rid in E.get('k', []):
                    it['r'][rid]['khulf'] = True

        # ٢-ب) الأصول المعمَّمة (ميم الجمع، الهمز الساكن، ضم الهاء، المدّ)
        for u in jl('%s/usul/%d.json' % (DATA, n)):
            it = item(u['s'], u['e'])
            it['t'] = it['t'] or 'u'
            for b in u['b']:
                if b not in it['b']:
                    it['b'].append(b)
            for r in u['r']:
                if r['id'] in it['r']:
                    if r.get('n'):
                        it['r'][r['id']].setdefault('n', r['n'])
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
                it = items.setdefault((q, q), {'s': q, 'e': q, 't': None, 'u': False, 'r': {}, 'b': []})
                it['t'] = it['t'] or 'p'
                it['r'][rid] = {'x': x, 'f': f, 'ap': mate, 'dq': dq, 'dx': dx}
                have.setdefault(rid, set()).add(q)
                added += 1

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
    print('عناصر الخلاف الموحَّدة:', stats['items'], '| معمَّمة على نظائر:', added, '| فروق رسم محضٍ أُزيلت:', dropped)


if __name__ == '__main__':
    main()
