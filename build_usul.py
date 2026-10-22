#!/usr/bin/env python3
"""تعميمُ خلاف الأصول على كلمات قالون كلِّها: app/data/usul/<سورة>.json.

الأصولُ لا يذكرها الكتابُ عند كل موضع («ويقاس عليه»)، فتُطبَّق هنا بمحوِّلاتٍ تُنتج كلمةَ الراوي من كلمة قالون:

  صلة ميم الجمع   ابن وردان وابن جماز كالبزي (مصحفُه شاهدٌ): «لَكُمْ» ← «لَكُمُۥ» قبل متحرّك
  صلة هاء الضمير   البزي وقنبل (ابن كثير): هاءٌ بين ساكنٍ ومتحرّك بياء لفظية بعد الياء الساكنة وبواو بعد غيرها؛
                   يشهد لكلٍّ مصحفُه (علامة الصلة ۥ/ۦ بعد الهاء، وقالونُ لا يُثبتها)
  إبدال الهمز الساكن   ابن وردان وابن جماز كالسوسي (مصحفُه شاهدٌ) إلا «أنبئهم» و«ننبئهم»
  ضمّ هاء «عليهم وإليهم ولديهم»   حمزة (خلف وخلاد) ويعقوب (رويس وروح)؛ ولو ليعقوب كل هاء بعد ياء ساكنة
  مدّ المتصل   ورش وحمزة (خلف وخلاد) ٦ حركات، وغيرهم ٤ كقالون فلا خلاف (بتصحيح صاحب المشروع)
  مدّ المنفصل   ورش وحمزة ٦، شعبة وحفص ٤، ابن عامر والكسائي وخلف العاشر ٤؛ ولا يظهر في المصاحف.
  ورش   مدّ البدل ومدّ اللين وترقيق الراء (بقواعدها المشهورة على صورة الكلمة)
  السكت   خلف وخلاد عن حمزة: على لام التعريف وشيء، وخلف وحده (بخلف) على الساكن المفصول قبل الهمز

قاعدةُ القبول: حيث يتوفّر مصحفُ زميلٍ (البزي، السوسي) لا يُقبَل الموضعُ إلا إن طابق المحوَّل ما في مصحفه.
والبيانُ مقتطَعٌ حرفياً من مدخل القاعدة في الكتاب. ولا مَدّ في المصاحف فتحديدُ مواضعه من نصّ قالون بالنمط
(مدّ متصل: حرف مدٍّ ثم همزة في الكلمة؛ منفصل: كلمةٌ تنتهي بحرف مدٍّ ثم كلمةٌ أولها همزة).
"""
import json, os, re
from canon import canon, diff_idx, norm, silah_idx

DATA = 'app/data'
WAQF = re.compile('[ۖ-ۜ۞۩]')
HAMZA = 'ءأإؤئ'
MUSH = {'bazzi': 'bazzi', 'susi': 'susi', 'qunbul': 'qunbul', 'warsh': 'warsh'}


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
LAM = re.compile('^(?:(?:[وف][َِ]?)?(?:[بك][َِ]?)?ال|(?:[وف][َِ]?)?لِل)[ءأإؤئآ]')
# الهمزتان من كلمة (همزة الاستفهام وبعدها همزة): قالون يفصل بينهما بألفٍ (ٰ في رسمه) ولا ألفَ لورش
PAIR = re.compile('^[۞]?[وف]?[أء]َٰ')
PAIR_KASRA = {'أذا', 'أله', 'أنا', 'أنك'}
PAIR_DAMMA = {'أشهدوا', 'ألقي', 'أنزل', 'أونبئكم'}
PAIR_NOTE = {'fatha': 'وجهان: إبدال الهمزة الثانية ألفاً مع المدّ، أو تسهيلها بين بين من غير إدخال',
             'kasra': 'تسهيل الهمزة الثانية بين بين (بينها وبين الياء) من غير إدخال',
             'damma': 'تسهيل الهمزة الثانية بين بين (بينها وبين الواو) من غير إدخال'}


def pair_kind(raw):
    if not PAIR.match(raw):
        return None
    if 'ٰا۬' in raw:
        return 'fatha'
    if 'ٰئ' in raw:
        return 'kasra'
    L = re.sub('[^ء-ي]', '', raw)
    return 'kasra' if L in PAIR_KASRA else 'damma' if L in PAIR_DAMMA else None


SHAY = re.compile('^(?:[وفبلك][َِ]?)?شَي[ءئ]')


def sakin_end(c, raw):
    """ساكنٌ آخر الكلمة غيرُ مدّ (يدخل التنوين واللين)"""
    if not c or 'ٰ' in raw[-2:]:           # ألفٌ خنجرية: مدٌّ لا سكون
        return False
    if c[-1] in 'ًٌٍ':
        return True
    if c[-1] in 'اىَُِّ':
        return False
    return not (c[-1] == 'و' and c[-2:-1] == 'ُ' or c[-1] == 'ي' and c[-2:-1] == 'ِ')


MIM = re.compile('[هكت][ُِ]مْ?$')

# مقدار المدّ بالحركات (المنفصل؛ والمتصل ٦ لورش وحمزة وراوييه فقط): قالون القصر في المنفصل
MADD = {'warsh': 6, 'khalaf_h': 6, 'khallad': 6, 'shuba': 5, 'hafs': 5,
        'hisham': 4, 'ibn_dhakwan': 4, 'abu_harith': 4, 'duri_k': 4, 'ishaq': 4, 'idris': 4}


# ---- أحكام ورش: مدّ البدل ومدّ اللين وترقيق الراء (على صورة قالون في المصحف) ----
FATH, DAMM, KASR, SUK = set('ًَٗ'), set('ٌُٞ'), set('ٍِٖ'), set('ْۡ')
HEAVY = set('خصضطظغق')
ALLMARKS = set('ٰۣٓٔۢۥۦۧۨ۟۠ۤ') | FATH | DAMM | KASR | SUK | {'ّ'}


def toks(raw):
    """حروفُ الكلمة بعلاماتها وموضع كل حرفٍ في النص الأصلي: [حرف، علامات، موضع]"""
    T = []
    for i, ch in enumerate(raw):
        if WAQF.match(ch):
            continue
        if ch in ALLMARKS or 'ً' <= ch <= 'ٟ':
            if T:
                T[-1][1].add(ch)
        elif ch != 'ـ':
            T.append([ch, set(), i])
    return T


def has_badal(raw):
    """همزةٌ بعدها حرفُ مدٍّ من جنس حركتها في الكلمة نفسها (غير مشدَّد ولا بعده ساكن)"""
    s = WAQF.sub('', raw)
    s = re.sub('([%s])ٓ' % HAMZA, r'\1َا', s)
    for m in re.finditer('([%s])([َُِ])([اوىيٰۥۦ])' % HAMZA, s):
        v, l = m.group(2), m.group(3)
        if (v == 'َ' and l in 'اٰ') or (v == 'ُ' and l in 'وۥ') or (v == 'ِ' and l in 'يىۦ'):
            rest = s[m.end():]
            if rest[:1] == 'ّ':
                continue
            if v == 'ُ' and re.match('^[ْ۟۠]*لَ', rest):   # أولئك وأولاء وأولات: الواو زائدة لا مدّ
                continue
            rest = re.sub('^[ْٰ۟۠]+', '', rest)
            if len(rest) >= 2 and rest[1] in 'ّْ':
                continue
            return True
    return False


LIN = re.compile('َ[يو][%s]' % HAMZA)


def tarqiq_idx(raw):
    """مواضع الراء المرقَّقة لورش: مفتوحةً أو مضمومةً بعد كسرٍ أو ياءٍ ساكنة أو ساكنٍ غير مستعلٍ بعد كسر.
    والراء الساكنة بعد كسرٍ لا يليها مستعلٍ مرقَّقةٌ عند الجميع فليست خلافاً (بتصحيح صاحب المشروع)"""
    T, out = toks(raw), []
    for i, (c, m, pos) in enumerate(T):
        if c != 'ر' or i == 0:
            continue
        p, pm, _ = T[i - 1]
        if p == 'ٱ':
            continue
        if m & (FATH | DAMM) and not m & KASR:
            if pm & KASR:
                out.append(pos)
            elif p in 'يے' and not pm & (FATH | DAMM | KASR | {'ّ'}):
                out.append(pos)
            elif i >= 2 and pm & SUK and p not in HEAVY and T[i - 2][1] & KASR and p not in 'يے':
                out.append(pos)
    return out


def taghliz_idx(raw):
    """مواضع اللام المغلَّظة لورش: لامٌ مفتوحة بعد صادٍ أو طاءٍ أو ظاءٍ مفتوحة أو ساكنةٍ بعد فتح"""
    T, out = toks(raw), []
    for i, (c, m, pos) in enumerate(T):
        if c != 'ل' or i == 0 or not m & FATH or m & (KASR | DAMM):
            continue
        p, pm, _ = T[i - 1]
        if p not in 'صطظ':
            continue
        if pm & FATH and not pm & (KASR | DAMM) or (pm & SUK and i >= 2 and T[i - 2][1] & FATH):
            out.append(pos)
    return out


# الحروف المقطَّعة في أوائل السور: عددُ كلماتها من أول السورة (وفي الشورى «حم» و«عسق»)
FAW = {2: 1, 3: 1, 7: 1, 10: 1, 11: 1, 12: 1, 13: 1, 14: 1, 15: 1, 19: 1, 20: 1, 26: 1, 27: 1, 28: 1, 29: 1,
       30: 1, 31: 1, 32: 1, 36: 1, 38: 1, 40: 1, 41: 1, 42: 2, 43: 1, 44: 1, 45: 1, 46: 1, 50: 1, 68: 1}


def main():
    E = {}
    for l in open('out/badur_entries.jsonl', encoding='utf-8'):
        e = json.loads(l)
        E[e['id']] = e
    b_silat = slice_between(E['b0045']['t'], '" عليهم "')
    b_ibdal = E['b0049']['t']
    b_madd = slice_between(E['b0051']['t'], '" بما أنزل "')
    b_hakina = E['b0048']['t'].split('"', 2)[2].strip()
    RULES = {'silat': b_silat, 'ibdal': b_ibdal, 'madd': b_madd, 'hakina': b_hakina}      # تُخزَّن مرةً واحدة ويُحال إليها
    b_silat, b_ibdal, b_madd, b_hakina = '@silat', '@ibdal', '@madd', '@hakina'

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
    st = {'silat': 0, 'ibdal': 0, 'ha': 0, 'muttasil': 0, 'munfasil': 0, 'madd': 0, 'sakt_lam': 0, 'sakt_shay': 0, 'sakt_sep': 0, 'badal': 0, 'lin': 0, 'tarqiq': 0, 'taghliz': 0, 'faw': 0, 'hakina': 0}

    def add(w, recs, bayan, key):
        st[key] += 1
        per.setdefault(w['sura'], {}).setdefault(w['seq'], {'s': w['seq'], 'e': w['seq'], 't': 'u', 'r': {}, 'b': []})
        it = per[w['sura']][w['seq']]
        for rid, rec in recs.items():
            ex = it['r'].get(rid)
            if ex is not None:
                if rec.get('n') and rec['n'] not in ex.get('n', ''):
                    ex['n'] = (ex.get('n', '') + ' / ' + rec['n']).strip(' /')
                if rec.get('x'):
                    if not ex.get('x'):
                        ex.update({k: rec[k] for k in ('x', 'f', 'dq', 'dx')})
                    elif ex['x'] == rec['x']:
                        for k in ('dq', 'dx'):
                            ex[k] = sorted(set(ex[k]) | set(rec[k]))
            else:
                it['r'][rid] = rec
        if bayan and bayan not in it['b']:
            it['b'].append(bayan)

    faw = set()
    for n, k in FAW.items():
        faw.update([w['seq'] for w in Q if w['sura'] == n][:k])
    for i, w in enumerate(Q):
        if w['seq'] in faw:
            # أبو جعفر براوييه: السكت على كل حرفٍ منها؛ ولا خلاف لابن كثير فيها (فلا يُطبَّق عليها غيرُ ذلك)
            n_ = 'السكت على كل حرف من الحروف المقطَّعة'
            add(w, {'ibn_wardan': {'n': n_}, 'ibn_jammaz': {'n': n_}}, None, 'faw')
            continue
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

        # ١-ب) صلة هاء الضمير لابن كثير: هاءٌ بعد ساكنٍ وقبل متحرّك. يشهد لها مصحفُ كلٍّ من البزي وقنبل
        #      (علامة الصلة بعد الهاء ولا مقابلَ لها في قالون). وما وُجدت علامتُه خارجَ هذا الضابط لا يُعمَّم هنا.
        nx_ = Q[i + 1] if i + 1 < len(Q) and Q[i + 1]['sura'] == w['sura'] else None
        T_ = toks(raw)
        if nx_ and len(T_) >= 2 and T_[-1][0] == 'ه' and not re.match('^[۞(]*[اٱ]', WAQF.sub('', nx_['text']).strip()):
            pm = T_[-2][1]
            if 'ٰ' in pm or pm & SUK or not pm & (FATH | DAMM | KASR):
                recs = {}
                for rid in ('bazzi', 'qunbul'):
                    x = mw[rid].get(w['seq'])
                    da, db = silah_idx(w['text'], x) if x else ([], [])
                    if da:
                        ya = 'ۦ' in x[db[-1]:db[-1] + 1]
                        dq, dx = letters(w['text'], x)
                        recs[rid] = {'x': x, 'f': rid, 'dq': sorted(set(dq) | set(da)), 'dx': sorted(set(dx) | set(db)),
                                     'n': 'صلة هاء الضمير ' + ('بياء لفظية' if ya else 'بواو لفظية')}
                if recs:
                    add(w, recs, b_hakina, 'hakina')

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
        #    المتصل: ورش وحمزة (خلف وخلاد) ٦ حركات، وغيرهم ٤ كقالون فلا خلاف (بتصحيح صاحب المشروع)
        mc = madd_str(raw)
        pk = pair_kind(raw)
        muttasil = MUTTASIL.search(mc) is not None and not pk     # ألفُ الفصل بين الهمزتين ليست مدّاً متصلاً لغير قالون
        munfasil = bool(nxt) and MUNFASIL.search(mc) is not None and HAMZ_START.match(nxt['text']) is not None
        if muttasil or munfasil:
            recs = {}
            for rid, k in MADD.items():
                what = []
                if muttasil and k == 6:
                    what.append('مدٌّ متصل ٦ حركات (وقالون ٤)')
                if munfasil:
                    # المنفصل عند عاصم (شعبة وحفص) أربع حركات (المذهب الثاني): تصحيحٌ من صاحب المشروع
                    what.append('مدٌّ منفصل %d حركات' % (4 if rid in ('shuba', 'hafs') else k))
                if what:
                    recs[rid] = {'n': ' و'.join(what)}
            if muttasil:
                st['muttasil'] += 1
            if munfasil:
                st['munfasil'] += 1
            if recs:
                add(w, recs, b_madd, 'madd')

        # ٥) السكت لحمزة وراوييه: خلف يسكت قولاً واحداً على لام التعريف وشيء وبخلافٍ على الساكن المفصول،
        #    وخلاد بخلافٍ على لام التعريف وشيء، ولا سكت له على المفصول
        if LAM.search(c):
            add(w, {'khalaf_h': {'n': 'السكت على لام التعريف قبل الهمز وصلاً'},
                    'khallad': {'n': 'السكت على لام التعريف قبل الهمز وصلاً، وله تركُه'}}, None, 'sakt_lam')
        elif SHAY.search(c):
            add(w, {'khalaf_h': {'n': 'السكت على «شيء» وصلاً'},
                    'khallad': {'n': 'السكت على «شيء» وصلاً، وله تركُه'}}, None, 'sakt_shay')
        elif nxt and HAMZ_START.match(nxt['text']) and sakin_end(c, raw):
            add(w, {'khalaf_h': {'n': 'السكت على الساكن المفصول قبل الهمز وصلاً، وله تركُه'}}, None, 'sakt_sep')

        # ٦) ورش: مدّ البدل (٢ أو ٤ أو ٦) ومدّ اللين قبل الهمز (٤ أو ٦) وترقيق الراء
        if pk:
            # باب الهمزتين من كلمة (ورش): لا مدّ بدلٍ ولا مدّ متصل؛ بل إبدالٌ أو تسهيلٌ بلا إدخال (بتصحيح صاحب المشروع)
            wx = mw['warsh'].get(w['seq'])
            rec = {'n': PAIR_NOTE[pk]}
            if wx:
                fx = next((k for k, c in enumerate(wx) if c in 'أءا'), 0)
                rec.update({'x': wx, 'f': 'warsh', 'dq': [w['text'].index('ٰ')], 'dx': [fx]})
            add(w, {'warsh': rec}, None, 'badal')
        elif has_badal(raw):
            add(w, {'warsh': {'n': 'مدّ البدل: قصر أو توسط أو إشباع (٢ أو ٤ أو ٦)'}}, None, 'badal')
        if LIN.search(c):
            add(w, {'warsh': {'n': 'مدّ اللين قبل الهمز: توسط أو إشباع (٤ أو ٦)'}}, None, 'lin')
        ix = tarqiq_idx(w['text'])
        if ix:
            add(w, {'warsh': {'n': 'ترقيق الراء', 'x': w['text'], 'f': 'qalun', 'dq': ix, 'dx': ix}}, None, 'tarqiq')
        ix = taghliz_idx(w['text'])
        if ix:
            add(w, {'warsh': {'n': 'تغليظ اللام', 'x': w['text'], 'f': 'qalun', 'dq': ix, 'dx': ix}}, None, 'taghliz')

    os.makedirs(DATA + '/usul', exist_ok=True)
    for n in range(1, 115):
        arr = []
        for k in sorted(per.get(n, {})):
            it = per[n][k]
            arr.append({'s': it['s'], 'e': it['e'], 't': 'u', 'bk': it['b'],
                        'r': [{'id': rid, **rec} for rid, rec in it['r'].items()]})
        with open('%s/usul/%d.json' % (DATA, n), 'w', encoding='utf-8') as f:
            json.dump(arr, f, ensure_ascii=False, separators=(',', ':'))
    with open(DATA + '/rules.json', 'w', encoding='utf-8') as f:
        json.dump(RULES, f, ensure_ascii=False)
    print(st)


if __name__ == '__main__':
    main()
