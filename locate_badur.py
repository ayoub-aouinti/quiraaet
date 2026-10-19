#!/usr/bin/env python3
"""يحدّد موضع كل مدخل من «البدور الزاهرة» في كلمات قالون.

الكتاب يسير على ترتيب المصحف، فالمداخل (بعد إسقاط ما ليس فرشاً) تُحاذى على كلمات قالون
محاذاةً متصاعدة: لكل مدخل مواضعُ مرشَّحة داخل سورته (وأربع سورٍ تليها)، وتُختار سلسلةُ مواضع
غيرُ متناقصة تُعظِّم عددَ المداخل الموضوعة وتُقلِّل القفزات. وهذا يُبطل أثرَ الكلمة الكثيرة
التكرار التي تُضلِّل البحثَ الأولَ فتجرّ ما بعدها.

العبارة في الكتاب بالإملاء المعاصر («الصلاة») ونصُّ المجمع بالرسم العثماني («الصلوة»)،
فالمطابقة على هيكلٍ يُسقِط الألف والواو والياء بعد الحرف الأول.
المدخلات: out/badur_entries.jsonl ، واختياريّاً out/badur_annot/*.json لإسقاط غير الفرش.
المخرَج:  out/badur_loc.jsonl
"""
import glob, json, re, sys
from bisect import bisect_right
from collections import Counter, defaultdict
from normalize import norm
from riwayat_text import riwaya_words

BONUS = 30.0        # مكافأة وضع مدخل
LAMBDA = 0.005      # كلفة كل كلمة قفزة إلى الأمام
OTHER_SURA = 6.0    # كلفة وقوع الموضع في سورةٍ غير المقصودة (لكل سورة)
FIRST_LETTER = 12.0  # كلفة المطابقة بإهمال الحرف الأول
SKIP = 8.0          # كلفة إسقاط مدخلٍ من السلسلة
LOOK = 6            # أبعدُ سابقٍ يُنظَر إليه


FILLER = {'معا', 'حيث', 'وقع', 'وقعا', 'أتى', 'كيف', 'جاء'}   # قيودٌ على التعميم لا من اللفظ المقتبس


def skel(w):
    t = norm(w)
    return t[:1] + re.sub('[اويى]', '', t[1:]) if t else ''


def phrases(w):
    out = []
    for ph in re.split('[،,؛]', w):
        toks = [skel(x) for x in re.split(r'\s+', ph.strip()) if skel(x) and x not in FILLER]
        if toks:
            out.append(toks)
    return out


def load_kinds():
    kinds = {}
    for f in glob.glob('out/badur_annot/chunk_*.json'):
        try:
            for r in json.load(open(f, encoding='utf-8')):
                kinds[r['id']] = r.get('kind')
        except Exception:
            pass
    return kinds


def main():
    qf = sorted(glob.glob('sources/mushafs/qalun/*.doc'))[0]
    _, qw = riwaya_words(qf)
    keys = [skel(w['text']) for w in qw]
    index = defaultdict(list)             # أول هيكلٍ في العبارة ← مواضعه
    for i, k in enumerate(keys):
        index[k].append(i)
    index2 = defaultdict(list)            # الهيكل بلا حرفه الأول
    for i, k in enumerate(keys):
        if len(k) > 2:
            index2[k[1:]].append(i)
    start, end = {}, {}
    for i, w in enumerate(qw):
        start.setdefault(w['sura'], i)
        end[w['sura']] = i + 1
    E = [json.loads(l) for l in open('out/badur_entries.jsonl', encoding='utf-8')]
    kinds = load_kinds()
    use_kinds = bool(kinds)

    # --- المرشَّحات
    cands = {}
    for e in E:
        if use_kinds and kinds.get(e['id']) != 'farsh':
            continue
        ph = phrases(e['w'])
        if not ph:
            continue
        first, n = ph[0], len(ph[0])
        s0 = e['sura']
        lo, hi = start[s0], end[min(114, s0 + 4)]
        cs = []
        for i in index.get(first[0], []):
            if lo <= i < hi and keys[i:i + n] == first:
                cs.append((i, OTHER_SURA * (qw[i]['sura'] - s0 if qw[i]['sura'] >= s0 else 3)))
        if not cs and len(first[0]) > 2:
            # الحرف الأول قد يتغيّر بين القراءتين (تتذكرون/يتذكرون): مطابقةٌ احتياطية بكلفة أعلى
            tail = first[0][1:]
            for i in index2.get(tail, []):
                if lo <= i < hi and [keys[i + j][1:] if j == 0 else keys[i + j] for j in range(n)] == [tail] + first[1:]:
                    cs.append((i, FIRST_LETTER + OTHER_SURA * (qw[i]['sura'] - s0 if qw[i]['sura'] >= s0 else 3)))
        if cs:
            cands[e['id']] = cs
    order = [e['id'] for e in E if e['id'] in cands]

    # --- البرمجة الديناميكية: dp[t] = [(pos, score, (prev_t, prev_k))]
    dp = []
    for t, eid in enumerate(order):
        row = []
        for pos, pen in cands[eid]:
            best = (BONUS - pen, None)                      # بداية سلسلة
            for d in range(1, LOOK + 1):
                u = t - d
                if u < 0:
                    break
                prev = dp[u]
                # أفضل سابقٍ موضعُه <= pos : max(score + LAMBDA*q) - LAMBDA*pos
                for k, (q, sc, _) in enumerate(prev):
                    if q <= pos:
                        v = sc - LAMBDA * (pos - q) - SKIP * (d - 1) + BONUS - pen
                        if v > best[0]:
                            best = (v, (u, k))
            row.append((pos, best[0], best[1]))
        dp.append(row)
    # أفضل نهاية
    chosen = {}
    if dp:
        t = len(dp) - 1
        # أفضل حالةٍ بين آخر LOOK مداخل
        bt, bk, bv = None, None, -1e18
        for u in range(max(0, len(dp) - LOOK), len(dp)):
            for k, (q, sc, _) in enumerate(dp[u]):
                v = sc - SKIP * (len(dp) - 1 - u)
                if v > bv:
                    bt, bk, bv = u, k, v
        while bt is not None:
            chosen[order[bt]] = dp[bt][bk][0]
            nxt = dp[bt][bk][2]
            bt, bk = nxt if nxt else (None, None)

    st, out = Counter(), []
    for e in E:
        pos = chosen.get(e['id'])
        if pos is None:
            st['بلا موضع'] += 1
            out.append({'id': e['id'], 'loc': None})
            continue
        n = len(phrases(e['w'])[0])
        a, b = qw[pos], qw[pos + n - 1]
        st['موضع'] += 1
        out.append({'id': e['id'], 'loc': [a['seq'], b['seq']], 'sura': a['sura'], 'ayah': a['ayah'],
                    'q': ' '.join(w['text'] for w in qw[pos:pos + n])})
    with open('out/badur_loc.jsonl', 'w', encoding='utf-8') as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(dict(st), '| بتصفية الفرش' if use_kinds else '| بلا تصفية (لا وسم بعد)')


if __name__ == '__main__':
    main()
