#!/usr/bin/env python3
"""يُخرج بيانات التطبيق (app/data) وينسخ خطوط المجمع (app/fonts).

  meta.json            السور والروايات والقراء وخطوطها
  qalun/<n>.json       كلمات قالون لكل سورة (المرجع)
  riw/<id>/<n>.json    مصحف كل رواية، وكل كلمةٍ محاذاةً لقالون وتصنيفُ فرقها
  khilaf/<n>.json      مواضع الخلاف المربوطة بكلمات قالون

تصنيف الكلمة في مصحف الرواية: 0 كما في قالون، 1 ضبط (حركات/همزات) مرشَّح،
2 رسم، 3 زائدة لا مقابل لها. ولا يُنسَب فرقٌ إلى قارئ بعينه إلا من ملفات الخلاف.
"""
import glob, json, os, shutil, sys, time
from difflib import SequenceMatcher
from canon import norm, classify, diff_idx
from riwayat_text import riwaya_words, basmala
from link_khilaf import plain_names

OUT = 'app'
RIW = {
    'qalun':  ('قالون عن نافع',     'qalun'),
    'warsh':  ('ورش عن نافع',       'warsh'),
    'duri':   ('الدوري عن أبي عمرو', 'duri'),
    'susi':   ('السوسي عن أبي عمرو', 'susi'),
    'shuba':  ('شعبة عن عاصم',      'shuba'),
    'hafs':   ('حفص عن عاصم',       'hafs'),
    'bazzi':  ('البزي عن ابن كثير',  'bazzi'),
    'qunbul': ('قنبل عن ابن كثير',   'qunbul'),
}
# ملف الخلاف ← مجموعة القراء. المكرَّر والجزئي يُتجاهَل (انظر الأسباب في README).
GROUPS = [
    ('عاصم', 'كامل', 'asim', 'عاصم'),
    ('أبي عمرو', 'كامل', 'abu_amr', 'أبو عمرو البصري'),
    ('الكسائي', 'كامل', 'kisai', 'الكسائي'),
    ('حمزة', 'كامل', 'hamza', 'حمزة'),
    ('ابن عامر', 'كامل', 'ibn_amir', 'ابن عامر'),
    ('يعقوب', 'كامل', 'yaqub', 'يعقوب'),
    ('إسحاق وإدريس', 'كامل', 'khalaf10', 'خلف العاشر'),
]
SKIP_WORDS = ('دون إمالة', 'من سورة فصلت', 'رواية إسحاق مقارنة', 'مواضع إمالة')


def group_of(fname):
    if any(k in fname for k in SKIP_WORDS):
        return None
    for a, b, gid, gname in GROUPS:
        if a in fname and b in fname:
            return gid, gname
    return None


def dump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))


def by_sura_ayah(words):
    out = {}
    for w in words:
        out.setdefault(w['sura'], {}).setdefault(w['ayah'], []).append(w)
    return out


def is_same_by_bayan(name, bayan):
    """«كقالون» صريحةً في سطر القارئ: اتفاقٌ بنصّ المصدر لا استنتاج."""
    for line in bayan.split('\n'):
        l = line.strip()
        if l.startswith(name) and ':' in l:
            seg = l.split(':', 1)[1].strip()
            return seg.startswith('كقالون') or seg.startswith('مثل قالون')
    return False


def align(qw, ow):
    qn = [norm(w['text']) or w['text'] for w in qw]
    on = [norm(w['text']) or w['text'] for w in ow]
    sm = SequenceMatcher(None, qn, on, autojunk=False)
    res = [None] * len(ow)          # لكل كلمة في الرواية: (q_seq, kind, d)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        n = min(i2 - i1, j2 - j1) if tag != 'insert' and tag != 'delete' else 0
        for k in range(n):
            q, o = qw[i1 + k], ow[j1 + k]
            kind = classify(q['text'], o['text'])
            if kind == 'same':
                res[j1 + k] = (q['seq'], 0, None)
            else:
                _, d = diff_idx(q['text'], o['text'])
                res[j1 + k] = (q['seq'], 2 if kind == 'rasm' else 1, d)
        for k in range(n, j2 - j1):
            res[j1 + k] = (0, 3, None)
    return res


def main(only=None):
    t0 = time.time()
    names = plain_names()
    words = {}
    for rid, (_, d) in RIW.items():
        f = sorted(glob.glob('sources/mushafs/%s/*.doc' % d))[0]
        _, words[rid] = riwaya_words(f)
        print(rid, len(words[rid]), 'كلمة', '%.0fs' % (time.time() - t0), flush=True)

    # --- خطوط المجمع
    os.makedirs(OUT + '/fonts', exist_ok=True)
    fonts = {}
    for rid, (_, d) in RIW.items():
        src = sorted(glob.glob('sources/mushafs/%s/*.ttf' % d) + glob.glob('sources/mushafs/%s/*.otf' % d))[0]
        fonts[rid] = rid + os.path.splitext(src)[1]
        shutil.copy(src, OUT + '/fonts/' + fonts[rid])

    # --- قالون
    qw = words['qalun']
    qs = by_sura_ayah(qw)
    ayat_count = []
    for n in range(1, 115):
        ays = qs[n]
        ayat_count.append(len(ays))
        dump('%s/data/qalun/%d.json' % (OUT, n),
             {'n': n, 'name': names[n - 1],
              'ayat': [[a, [[w['seq'], w['text']] for w in ays[a]]] for a in sorted(ays)]})

    # --- مصحف كل رواية مقابل قالون
    stats = {}
    for rid in RIW:
        if rid == 'qalun' or (only and rid not in only):
            continue
        res = align(qw, words[rid])
        ow = words[rid]
        c = {0: 0, 1: 0, 2: 0, 3: 0}
        for r in res:
            c[r[1]] += 1
        stats[rid] = c
        os_ = by_sura_ayah(ow)
        idx = {id(w): i for i, w in enumerate(ow)}
        for n in range(1, 115):
            ays = os_.get(n, {})
            rows = []
            for a in sorted(ays):
                ws = []
                for w in ays[a]:
                    q, k, d = res[idx[id(w)]]
                    ws.append([w['text'], q, k] + ([d] if d else []))
                rows.append([a, ws])
            dump('%s/data/riw/%s/%d.json' % (OUT, rid, n), {'n': n, 'ayat': rows})
        print(rid, 'محاذاة', c, '%.0fs' % (time.time() - t0), flush=True)

    # --- الخلاف
    kh = json.load(open('out/khilaf_linked.json', encoding='utf-8'))['linked']
    wby = {w['seq']: w for w in qw}
    per, groups, seen = {}, {}, set()
    for r in kh:
        g = group_of(r['file'])
        if not g:
            continue
        gid, gname = g
        for (ay, s, e, tier, req) in r['links'][:1]:
            key = (gid, s, e, r['qalun'])
            if key in seen:
                continue
            seen.add(key)
            phrase = ' '.join(wby[i]['text'] for i in range(s, e + 1))
            rs = []
            for name, txt in r['readings'].items():
                name = name or gname      # عمودٌ بلا اسمٍ في الملف (خلف العاشر): يُسمّى باسم القراءة
                rid = '%s:%s' % (gid, name)
                groups.setdefault(gid, {'id': gid, 'name': gname, 'readers': {}})['readers'][rid] = name
                same = is_same_by_bayan(name, r['bayan'])
                dq, dx = ([], [])
                if not same:
                    dq, dx = diff_idx(phrase, txt)
                    # فرقٌ يعمّ أكثر الكلمة معناه اختلافُ ترميز لا تمييز حروف: لا تلوين حرفي
                    if len(dq) > 0.6 * max(1, len(phrase.replace(' ', ''))):
                        dq, dx = [], []
                rs.append({'id': rid, 'n': name, 'x': txt, 'same': same, 'dq': dq, 'dx': dx})
            sura = r['sura']
            per.setdefault(sura, []).append({'s': s, 'e': e, 'g': gid, 't': tier, 'r': rs, 'b': r['bayan'],
                                             'a': req})
    for n in range(1, 115):
        dump('%s/data/khilaf/%d.json' % (OUT, n), sorted(per.get(n, []), key=lambda x: x['s']))
    print('خلاف:', sum(len(v) for v in per.values()), 'إدخالاً', '%.0fs' % (time.time() - t0), flush=True)

    try:
        old_stats = json.load(open(OUT + '/data/meta.json', encoding='utf-8')).get('stats', {})
    except OSError:
        old_stats = {}
    meta = {
        'suras': [{'n': i + 1, 'name': names[i], 'ayat': ayat_count[i]} for i in range(114)],
        'riwayat': [{'id': rid, 'name': RIW[rid][0], 'font': fonts[rid], 'ref': rid == 'qalun',
                     'bsm': basmala(sorted(glob.glob('sources/mushafs/%s/*.doc' % RIW[rid][1]))[0])} for rid in RIW],
        'groups': [{'id': g['id'], 'name': g['name'],
                    'readers': [{'id': k, 'name': v} for k, v in g['readers'].items()]} for g in groups.values()],
        'stats': {k: {str(a): b for a, b in v.items()} for k, v in stats.items()} or old_stats,
    }
    dump(OUT + '/data/meta.json', meta)
    print('تم', '%.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main(sys.argv[1:] or None)
