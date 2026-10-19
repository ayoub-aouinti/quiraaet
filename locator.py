#!/usr/bin/env python3
"""محدِّد المواضع: يحوّل أي عبارة قرآنية مقتبسة إلى موقعها في فهرس الكلمات.

يُبنى فهرس مقلوب على تتابعات الكلمات المطبّعة، فيُعاد لكل عبارة:
  - موضع واحد  -> يقين
  - عدة مواضع -> يحتاج سياقاً (رقم السورة أو الآية) لترجيح أحدها
  - لا موضع    -> العبارة محرّفة أو خارج النص
"""
import json, re
from collections import defaultdict
from normalize import norm, tokens


class Locator:
    NGRAM = 3

    def __init__(self, words_indexed):
        self.w = json.load(open(words_indexed, encoding='utf-8'))
        self.n = [x['n'] for x in self.w]
        self.idx = defaultdict(list)
        for i in range(len(self.n) - self.NGRAM + 1):
            self.idx[' '.join(self.n[i:i + self.NGRAM])].append(i)
        self.uni = defaultdict(list)
        for i, t in enumerate(self.n):
            self.uni[t].append(i)

    @staticmethod
    def _loose(t):
        """إسقاط الألف، لأن الرسم العثماني يحذفها حيث يثبتها الرسم الإملائي.

        «القيامة» في المصحف «القيمه»، و«طغيانهم» «طغينهم». فالكتبُ المطبوعة
        تنقل الآية بالإملائي والفهرسُ بالعثماني، فلا يلتقيان إلا بهذا.
        """
        return t.replace('ا', '') or t

    def _build_loose(self):
        if hasattr(self, 'lidx'):
            return
        self.ln = [self._loose(t) for t in self.n]
        self.lidx = defaultdict(list)
        for i in range(len(self.ln) - self.NGRAM + 1):
            self.lidx[' '.join(self.ln[i:i + self.NGRAM])].append(i)
        self.luni = defaultdict(list)
        for i, t in enumerate(self.ln):
            self.luni[t].append(i)

    def match_seq_loose(self, seq):
        """مطابقةٌ متساهلة في الألف، تُستعمل حين تُخفق المطابقة الحرفية."""
        if not seq:
            return []
        self._build_loose()
        ls = [self._loose(t) for t in seq]
        if len(ls) >= self.NGRAM:
            cands = self.lidx.get(' '.join(ls[:self.NGRAM]), [])
        else:
            cands = self.luni.get(ls[0], [])
        return [c for c in cands if self.ln[c:c + len(ls)] == ls]

    @staticmethod
    def _skel(t):
        """الهيكلُ الصامت: إسقاطُ حروف المدّ الثلاثة ا و ي.

        الرسمُ العثماني يكتب طائفةً من الكلمات بالواو حيث يكتبها الإملائيُّ
        بالألف: «الصلاة» فيه «الصلوة»، و«الزكاة» «الزكوة»، و«الحياة»
        «الحيوة»، و«الربا» «الربوا». وهذه لا يبلغها إسقاطُ الألف وحدَه،
        وإنما يجمعها إسقاطُ حروف المدّ كلِّها.

        وهذا تساهلٌ شديدٌ يُقارب بين كلماتٍ متباعدة، فلا يُستعمل إلا في
        تتابعِ كلمتين فأكثر، ولا يُقبل منه إلا ما تفرَّد في سورته.
        """
        return re.sub(r'[اوي]', '', t) or t

    def _build_skel(self):
        if hasattr(self, 'sidx'):
            return
        self.sn = [self._skel(t) for t in self.n]
        self.sidx = defaultdict(list)
        for i in range(len(self.sn) - self.NGRAM + 1):
            self.sidx[' '.join(self.sn[i:i + self.NGRAM])].append(i)
        self.suni = defaultdict(list)
        for i, t in enumerate(self.sn):
            self.suni[t].append(i)

    def match_seq_skel(self, seq):
        """مطابقةُ الهيكل الصامت. لكلمتين فأكثر فقط؛ وما دونهما يُرَدّ فارغاً."""
        if not seq or len(seq) < 2:
            return []
        self._build_skel()
        ss = [self._skel(t) for t in seq]
        if len(ss) >= self.NGRAM:
            cands = self.sidx.get(' '.join(ss[:self.NGRAM]), [])
        else:
            cands = self.suni.get(ss[0], [])
        return [c for c in cands if self.sn[c:c + len(ss)] == ss]

    def match_seq(self, seq):
        """مواضع تتابع من الكلمات المطبّعة، أياً كان طوله."""
        if not seq:
            return []
        if len(seq) >= self.NGRAM:
            cands = self.idx.get(' '.join(seq[:self.NGRAM]), [])
        else:
            cands = self.uni.get(seq[0], [])
        return [c for c in cands if self.n[c:c + len(seq)] == seq]

    def match_before(self, toks, i, max_len=9, sura=None):
        """أطول تتابع قرآني ينتهي عند الكلمة i-1 (أي يسبق المصطلح مباشرة).

        هذا هو وضع الكتب التي تُدمج فيها الآية في الشرح بلا أقواس، وفيها
        يأتي الحكم عقب الكلمة الموقوف عليها: «للمتقين تام»، «لا ريب تام».
        يُبدأ بأطول تتابع ممكن لأنه أقلّ التباساً، ثم يُقصَّر عند التعذّر.
        """
        best = None
        for L in range(min(max_len, i), 0, -1):
            seq = toks[i - L:i]
            hits = self.match_seq(seq)
            if not hits:
                continue
            ins = [h for h in hits if sura is None or self.w[h]['sura'] == sura]
            use = ins or hits
            cand = {'len': L, 'hits': use, 'in_sura': bool(ins), 'total': len(hits)}
            if len(use) == 1:
                return cand                     # محسوم: خذه فوراً
            if best is None:
                best = cand
        return best

    def seq_position(self, hit, length):
        last = self.w[min(hit + length - 1, len(self.w) - 1)]
        return {'start_seq': self.w[hit]['seq'], 'end_seq': last['seq'],
                'sura': last['sura'], 'sura_name': last['sura_name'],
                'ayah': last['ayah'], 'stop_word': last['text'], 'matched': length}

    def scan_runs(self, text, min_words=3):
        """يكشف الاقتباسات القرآنية في نصّ حرّ بلا اعتماد على قوسي الآية.

        يلزم هذا الوضع في الكتب المصوّرة، لأن التعرّف الضوئي لا يميّز ﴿ ﴾،
        وفي الكتب التي لا تستعمل أقواساً أصلاً. يُمسح النصّ كلمةً كلمة،
        ويُؤخذ كل تتابع يطابق القرآن طوله min_words فأكثر.
        يعيد لكل اقتباس: نصّه، وموضع نهايته في النصّ الأصلي، ومرشحيه.
        """
        toks, spans = [], []
        for m in re.finditer(r'\S+', text):
            t = norm(m.group())
            if t:
                toks.append(t)
                spans.append((m.start(), m.end()))

        runs, i = [], 0
        while i < len(toks) - min_words + 1:
            if min_words >= self.NGRAM:
                cands = self.idx.get(' '.join(toks[i:i + self.NGRAM]))
            else:                       # تتابع أقصر من النوافذ: ابدأ بالكلمة
                cands = self.uni.get(toks[i])
            if not cands:
                i += 1
                continue
            base = min(self.NGRAM, min_words)
            best, best_at = base, []
            for c in cands:                      # مدّ المطابقة إلى أقصاها
                k = base
                if toks[i:i + k] != self.n[c:c + k]:
                    continue
                while (i + k < len(toks) and c + k < len(self.n)
                       and toks[i + k] == self.n[c + k]):
                    k += 1
                if k > best:
                    best, best_at = k, [c]
                elif k == best:
                    best_at.append(c)
            if best >= min_words and best_at:
                runs.append({
                    'text': text[spans[i][0]:spans[i + best - 1][1]],
                    'end_char': spans[i + best - 1][1],
                    'start_char': spans[i][0],
                    'words': best,
                    'cands': best_at,
                })
                i += best
            else:
                i += 1
        return runs

    def run_position(self, run, sura=None):
        """يحوّل تتابعاً مكشوفاً إلى موضع، مع حالة الثقة."""
        if not run['cands']:
            return {'status': 'not_found', 'pos': None, 'n': 0}
        c = [x for x in run['cands']
             if sura is None or self.w[x]['sura'] == sura]
        if not c:
            c = run['cands']
        out = []
        for s in c:
            last = self.w[min(s + run['words'] - 1, len(self.w) - 1)]
            out.append({'start_seq': self.w[s]['seq'], 'end_seq': last['seq'],
                        'sura': last['sura'], 'sura_name': last['sura_name'],
                        'ayah': last['ayah'], 'stop_word': last['text'],
                        'matched': run['words']})
        if len(out) == 1:
            return {'status': 'unique', 'pos': out[0], 'n': 1}
        return {'status': 'ambiguous', 'pos': out[0], 'n': len(out), 'all': out[:8]}

    def find(self, phrase, sura=None, ayah=None):
        """يعيد قائمة المواضع المرشّحة لعبارة. كل مرشّح: بداية ونهاية وموقع."""
        q = tokens(phrase)
        if not q:
            return []
        if len(q) >= self.NGRAM:
            cands = self.idx.get(' '.join(q[:self.NGRAM]), [])
        else:
            cands = self.uni.get(q[0], [])
        hits = []
        for c in cands:
            if self.n[c:c + len(q)] == q:
                hits.append(c)
        if not hits:                       # تساهل: طابق أطول بادئة ممكنة
            for k in range(len(q) - 1, self.NGRAM - 1, -1):
                for c in self.idx.get(' '.join(q[:self.NGRAM]), []):
                    if self.n[c:c + k] == q[:k]:
                        hits.append(c)
                if hits:
                    break
        out = []
        for h in hits:
            last = self.w[min(h + len(q) - 1, len(self.w) - 1)]
            first = self.w[h]
            if sura and first['sura'] != sura:
                continue
            if ayah and first['ayah'] != ayah:
                continue
            out.append({
                'start_seq': first['seq'], 'end_seq': last['seq'],
                'sura': last['sura'], 'sura_name': last['sura_name'],
                'ayah': last['ayah'],
                'stop_word': last['text'],      # الكلمة التي يقع الوقف بعدها
                'matched': len(q),
            })
        return out

    def locate(self, phrase, sura=None, ayah=None):
        """نتيجة واحدة مع درجة الثقة."""
        c = self.find(phrase, sura, ayah)
        if len(c) == 1:
            return {'status': 'unique', 'pos': c[0], 'n': 1}
        if not c:
            return {'status': 'not_found', 'pos': None, 'n': 0}
        return {'status': 'ambiguous', 'pos': c[0], 'n': len(c), 'all': c[:8]}


if __name__ == '__main__':
    import sys
    L = Locator(sys.argv[1])
    for p in sys.argv[2:]:
        r = L.locate(p)
        print(p, '->', r['status'], r['n'],
              (f"{r['pos']['sura_name']} {r['pos']['sura']}:{r['pos']['ayah']} "
               f"بعد «{r['pos']['stop_word']}»") if r['pos'] else '')
