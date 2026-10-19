#!/usr/bin/env python3
"""تعميمُ خلاف الأصول على كلمات قالون كلِّها: app/data/usul/<سورة>.json.

الأصولُ لا يذكرها الكتابُ عند كل موضع («ويقاس عليه»)، فتُطبَّق هنا بمحوِّلاتٍ تُنتج كلمةَ الراوي من كلمة قالون:

  صلة ميم الجمع   ابن وردان وابن جماز كالبزي (مصحفُه شاهدٌ): «لَكُمْ» ← «لَكُمُۥ» قبل متحرّك
  إبدال الهمز الساكن   ابن وردان وابن جماز كالسوسي (مصحفُه شاهدٌ) إلا «أنبئهم» و«ننبئهم»
  ضمّ هاء «عليهم وإليهم ولديهم»   حمزة (خلف وخلاد) ويعقوب (رويس وروح)؛ ولو ليعقوب كل هاء بعد ياء ساكنة
  مدّ المنفصل والمتصل   ورش وحمزة ٦، عاصم ٥، ابن عامر والكسائي وخلف العاشر ٤ (على المذهب الأول)؛ ولا يظهر في المصاحف.

قاعدةُ القبول: حيث يتوفّر مصحفُ زميلٍ (البزي، السوسي) لا يُقبَل الموضعُ إلا إن طابق المحوَّل ما في مصحفه.
والبيانُ مقتطَعٌ حرفياً من مدخل القاعدة في الكتاب. ولا مَدّ في المصاحف فتحديدُ مواضعه من نصّ قالون بالنمط
(مدّ متصل: حرف مدٍّ ثم همزة في الكلمة؛ منفصل: كلمةٌ تنتهي بحرف مدٍّ ثم كلمةٌ أولها همزة).
"""
import json, os, re
from canon import canon, diff_idx, norm

DATA = 'app/data'
WAQF = re.compile('[ۖ-ۜ۞۩]')
HAMZA = 'ءأإؤئ'
MUSH = {'bazzi': 'bazzi', 'susi': 'susi'}


def jl(p):
    return json.load(open(p, encoding='utf-8'))


def cstr(w):
    return ''.join(c for c, _ in canon(w))


def letters(phrase, x):
    dq, dx = diff_idx(phrase, x)
    if len(dq) > 0.6 * max(1, len(phrase.replace(' ', ''))):
        return [], []
    return dq, dx


def slice_between(text, start, end=None):
    i = text.index(start)
    j = text.index(end, i) if end else len(text)
    return text[i:j].strip()


def madd_str(w):
    """نصٌّ للكشف عن المدّ: الألف الخنجرية والواو والياء الصغيرتان حروفُ مدّ."""
    w = WAQF.sub('', w).replace('ٰ', 'ا').replace('ۥ', 'و').replace('ۦ', 'ي')
    return cstr(w)


MUTTASIL = re.compile('(?:َا|ُو|ِي)[%s]' % HAMZA)
MUNFASIL = re.compile('(?:َا|ُوا?|ِي)$')
HAMZ_START = re.compile('^[۞۞(]*[أإءؤئآ]')
MIM = re.compile('[هكت][ُِ]مْ?$')

# مقدار المدّ بالحركات على المذهب الأول (الداني): قالون ٣ والقصر في المنفصل
MADD = {'warsh': 6, 'khalaf_h': 6, 'khallad': 6, 'shuba': 5, 'hafs': 5,
        'hisham': 4, 'ibn_dhakwan': 4, 'abu_harith': 4, 'duri_k': 4, 'ishaq': 4, 'idris': 4}


def main():
    E = {}
    for l in open('out/badur_entries.jsonl', encoding='utf-8'):
        e = json.loads(l)
        E[e['id']] = e
    b_silat = slice_between(E['b0045']['t'], '" عليهم "')
    b_ibdal = E['b0049']['t']
    b_madd = slice_between(E['b0051']['t'], '" بما أنزل "')
    RULES = {'silat': b_silat, 'ibdal': b_ibdal, 'madd': b_madd}      # تُخزَّن مرةً واحدة ويُحال إليها
    b_silat, b_ibdal, b_madd = '@silat', '@ibdal', '@madd'

    # كلمات قالون بتسلسلها العام
    Q = []
    for n in range(1, 115):
        for ay, ws in jl('%s/qalun/%d.json' % (DATA, n))['ayat']:
            for s, t in ws:
                Q.append({'seq': s, 'text': t, 'sura': n, 'ayah': ay})
    mw = {}
    for rid in set(MUSH.values()):
        m = {}
        for n in range(1, 115):
            for _, ws in jl('%s/riw/%s/%d.json' % (DATA, rid, n))['ayat']:
                for w in ws:
                    if w[1] and w[1] not in m:
                        m[w[1]] = w[0]
        mw[rid] = m

    per = {}
    st = {'silat': 0, 'ibdal': 0, 'ha': 0, 'muttasil': 0, 'munfasil': 0}

    def add(w, recs, bayan, key):
        st[key] += 1
        per.setdefault(w['sura'], {}).setdefault(w['seq'], {'s': w['seq'], 'e': w['seq'], 't': 'u', 'r': {}, 'b': []})
        it = per[w['sura']][w['seq']]
        for rid, rec in recs.items():
            it['r'].setdefault(rid, rec)
        if bayan not in it['b']:
            it['b'].append(bayan)

    for i, w in enumerate(Q):
        raw = WAQF.sub('', w['text']).strip()
        nxt = Q[i + 1] if i + 1 < len(Q) and Q[i + 1]['ayah'] == w['ayah'] and Q[i + 1]['sura'] == w['sura'] else None
        c = cstr(raw)

        # ١) صلة ميم الجمع: يشهد لها مصحفُ البزي
        if nxt and MIM.search(raw) is not None or (nxt and re.search('[هكت][ُِ]م$', c)):
            bz = mw['bazzi'].get(w['seq'])
            if bz and cstr(WAQF.sub('', bz)) == c + 'ُ' and nxt['text'][:1] != 'ٱ':
                dq, dx = letters(w['text'], bz)
                rec = {'x': bz, 'f': 'bazzi', 'dq': dq, 'dx': dx, 'n': 'صلة ميم الجمع بواو'}
                add(w, {'ibn_wardan': dict(rec), 'ibn_jammaz': dict(rec)}, b_silat, 'silat')

        # ٢) إبدال الهمز الساكن (فاءً أو عيناً أو لاماً): يشهد له مصحفُ السوسي
        m = re.search('([َُِ])([%s])(?![ًٌٍَُِ])' % HAMZA, c)
        if m and norm(raw) not in ('انبيهم', 'ننبيهم'):
            su = mw['susi'].get(w['seq'])
            letter = {'َ': 'ا', 'ُ': 'و', 'ِ': 'ي'}[m.group(1)]
            pred = c[:m.start(2)] + letter + c[m.end(2):]
            if su and cstr(WAQF.sub('', su)) == pred:
                dq, dx = letters(w['text'], su)
                rec = {'x': su, 'f': 'susi', 'dq': dq, 'dx': dx, 'n': 'إبدال الهمز الساكن'}
                add(w, {'ibn_wardan': dict(rec), 'ibn_jammaz': dict(rec)}, b_ibdal, 'ibdal')

        # ٣) ضمّ الهاء: عليهم وإليهم ولديهم لحمزة ويعقوب، وكل هاءٍ بعد ياءٍ ساكنةٍ ليعقوب
        mh = re.search('(ي)(ه)(ِ)(م)', c)
        if mh:
            is3 = re.search('(?:عَلَ|إِلَ|لَدَ)يهِم', c)
            idx = raw.find('هِ')
            if idx >= 0:
                x = raw[:idx] + 'هُ' + raw[idx + 2:]
                dq, dx = letters(w['text'], x)
                rec = {'x': x, 'f': 'qalun', 'dq': dq, 'dx': dx, 'n': 'ضمّ الهاء وصلاً ووقفاً'}
                recs = {'ruways': dict(rec), 'rawh': dict(rec)}
                if is3:
                    recs.update({'khalaf_h': dict(rec), 'khallad': dict(rec)})
                add(w, recs, b_silat, 'ha')

        # ٤) المدّ المتصل والمنفصل (لا يظهر في المصاحف)
        mc = madd_str(raw)
        muttasil = MUTTASIL.search(mc) is not None
        munfasil = bool(nxt) and MUNFASIL.search(mc) is not None and HAMZ_START.match(nxt['text']) is not None
        if muttasil or munfasil:
            recs = {}
            for rid, k in MADD.items():
                what = []
                if muttasil:
                    what.append('مدٌّ متصل %d حركات' % k)
                if munfasil:
                    what.append('مدٌّ منفصل %d حركات' % k)
                recs[rid] = {'n': ' و'.join(what)}
            if muttasil:
                st['muttasil'] += 1
            if munfasil:
                st['munfasil'] += 1
            # يُعدّان في عدّادٍ واحد للتقرير؛ العنصر واحدٌ لكل كلمة
            per.setdefault(w['sura'], {}).setdefault(w['seq'], {'s': w['seq'], 'e': w['seq'], 't': 'u', 'r': {}, 'b': []})
            it = per[w['sura']][w['seq']]
            for rid, rec in recs.items():
                if rid in it['r']:
                    it['r'][rid]['n'] = (it['r'][rid].get('n', '') + ' / ' + rec['n']).strip(' /')
                else:
                    it['r'][rid] = rec
            if b_madd not in it['b']:
                it['b'].append(b_madd)

    os.makedirs(DATA + '/usul', exist_ok=True)
    for n in range(1, 115):
        arr = []
        for k in sorted(per.get(n, {})):
            it = per[n][k]
            arr.append({'s': it['s'], 'e': it['e'], 't': 'u', 'b': it['b'],
                        'r': [{'id': rid, **rec} for rid, rec in it['r'].items()]})
        with open('%s/usul/%d.json' % (DATA, n), 'w', encoding='utf-8') as f:
            json.dump(arr, f, ensure_ascii=False, separators=(',', ':'))
    with open(DATA + '/rules.json', 'w', encoding='utf-8') as f:
        json.dump(RULES, f, ensure_ascii=False)
    print(st)


if __name__ == '__main__':
    main()
