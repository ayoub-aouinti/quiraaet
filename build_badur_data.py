#!/usr/bin/env python3
"""يدمج وسمَ مداخل «البدور الزاهرة» بمواضعها في قالون ويُخرج app/data/badur/<سورة>.json.

كل مدخل مُخرَج: {i معرّف، s,e كلمتا قالون الأولى والأخيرة، t نصُّ الكتاب حرفياً،
a جوانب الخلاف [{g:[{r:[رواة]|rest:true, snip}], q: رقم مجموعة قالون|-1}]،
k من ورد «بخلف عنه»، u غيرُ مؤكَّد}.

تحقُّقاتٌ آلية على ما يرجع به الوسم (قانون الأمانة): معرِّفاتٌ معروفة فقط؛ و`snip` يجب أن يكون
جزءاً حرفياً من النص وإلا حُذف؛ ولا يُقبَل جانبٌ بلا مجموعتين. وما فشل يُعلَّم `u` ولا يُخفى.
"""
import glob, json, os, re
from collections import Counter

ALL = ['qalun', 'warsh', 'bazzi', 'qunbul', 'duri_a', 'susi', 'hisham', 'ibn_dhakwan', 'shuba', 'hafs',
       'khalaf_h', 'khallad', 'abu_harith', 'duri_k', 'ibn_wardan', 'ibn_jammaz', 'ruways', 'rawh', 'ishaq', 'idris']
OUT = 'app/data/badur'
WS = re.compile(r'\s+')


def squash(s):
    return WS.sub(' ', s).strip()


def main():
    E = {}
    for l in open('out/badur_entries.jsonl', encoding='utf-8'):
        e = json.loads(l)
        E[e['id']] = e
    L = {}
    for l in open('out/badur_loc.jsonl', encoding='utf-8'):
        x = json.loads(l)
        L[x['id']] = x
    A = {}
    for f in sorted(glob.glob('out/badur_annot/chunk_*.json')):
        for r in json.load(open(f, encoding='utf-8')):
            A[r['id']] = r
    st = Counter()
    per = {}
    for eid, r in A.items():
        e, loc = E.get(eid), L.get(eid)
        if not e:
            st['معرّف مجهول'] += 1
            continue
        st['kind ' + str(r.get('kind'))] += 1
        if r.get('kind') != 'farsh':
            continue
        if not loc or not loc['loc']:
            st['فرش بلا موضع'] += 1
            continue
        text = squash(e['t'])
        asps, unsure = [], bool(r.get('unsure'))
        for a in r.get('aspects') or []:
            gs = []
            for g in a.get('groups') or []:
                rid = [x for x in (g.get('r') or []) if x in ALL]
                if len(rid) != len(g.get('r') or []):
                    unsure = True
                    st['معرّف راوٍ غير معروف'] += 1
                snip = g.get('snip')
                if snip and squash(snip) not in text:
                    snip = None
                    st['snip غير حرفي حُذف'] += 1
                if g.get('rest'):
                    gs.append({'rest': True, **({'snip': snip} if snip else {})})
                elif rid:
                    cond = [x for x in (g.get('cond') or []) if x in rid]
                    gs.append({'r': rid, **({'snip': snip} if snip else {}), **({'cond': cond} if cond else {})})
            if len(gs) == 1 and 'r' in gs[0]:
                gs.append({'rest': True, 'implicit': True})     # بقيةُ الرواة على الأصل
                st['باقٍ ضمني'] += 1
            if len(gs) < 2:
                st['جانب بلا مجموعتين'] += 1
                unsure = True
                if not gs:
                    continue
            named = {x for g in gs for x in g.get('r', [])}
            # مجموعة قالون: من ذُكر فيها، وإلا مجموعة «الباقين» إن وُجدت
            q = -1
            for i, g in enumerate(gs):
                if 'qalun' in g.get('r', []):
                    q = i
            if q < 0 and 'qalun' not in named:
                for i, g in enumerate(gs):
                    if g.get('rest'):
                        q = i
            # من ورد فيهم «بخلفٍ عنه» في هذا الجانب: يُحسَم بنصّ المصحف عند البناء (build_reads)
            akh = sorted({x for x in (a.get('khulf') or []) + (r.get('khulf') or []) if x in ALL})
            asps.append({'g': gs, 'q': q, **({'kh': akh} if akh else {})})
        if not asps:
            st['فرش بلا جوانب'] += 1
            continue
        khulf = [x for x in (r.get('khulf') or []) if x in ALL] if not r.get('aspects') else \
            sorted({x for a in r['aspects'] for x in (a.get('khulf') or []) if x in ALL})
        per.setdefault(loc['sura'], []).append(
            {'i': eid, 's': loc['loc'][0], 'e': loc['loc'][1], 't': e['t'], 'a': asps, 'k': khulf, 'u': unsure})
        st['مُخرَج'] += 1
    os.makedirs(OUT, exist_ok=True)
    for n in range(1, 115):
        arr = sorted(per.get(n, []), key=lambda x: x['s'])
        with open('%s/%d.json' % (OUT, n), 'w', encoding='utf-8') as f:
            json.dump(arr, f, ensure_ascii=False, separators=(',', ':'))
    # مداخلُ فرشٍ لم يُعثر على موضعها أو جوانبها: تُحفَظ ولا تُسقَط (قانون الأمانة)
    un = []
    for eid, r in A.items():
        if r.get('kind') == 'farsh' and (not L.get(eid) or not L[eid]['loc']):
            un.append({'i': eid, 'sura': E[eid]['sura'], 'w': E[eid]['w'], 't': E[eid]['t']})
    with open('app/data/badur_unlocated.json', 'w', encoding='utf-8') as f:
        json.dump(un, f, ensure_ascii=False, separators=(',', ':'))
    st['محفوظة بلا موضع'] = len(un)
    print(dict(st))


if __name__ == '__main__':
    main()
