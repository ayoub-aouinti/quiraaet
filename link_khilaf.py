#!/usr/bin/env python3
"""يبني كلمات قالون من نصّ المجمع، ثم يربط مواضع الخلاف بها.

المرجع قالون. لكل كلمة: (seq, sura, ayah, wpos, text) بنصّ المجمع بعينه.
ربط الموضع: رقم الآية إحداثيٌّ أول، ثم تطابق لفظ قالون المنقول في ملف
الخلاف مع كلمات الآية. ما لم يتطابق يبقى `unlinked` ولا يُخمَّن.
"""
import json, re, sys
from collections import Counter
from riwayat_text import riwaya_words
from normalize import norm
from canon import norm as cnorm   # يوحّد اصطلاحات الخط المغربي قبل التجريد

DOC = 'sources/mushafs/qalun/UthmanicQaloon1 Ver08.doc'
HEAD = re.compile(r'سُورَةُ\s+(.+?)(?=بِسْمِ)')
DIGITS = re.compile(r'^[٠-٩]+$')
WAQF = re.compile('[ۖ-ۜ۞۩]')   # علامات الوقف والسجدة
AR2 = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')


def key(w):
    """مفتاح مقارنة اللفظ بعينه دون علامات الوقف ودون أرقام الآي."""
    return WAQF.sub('', w).replace('ـ', '')


def plain_names():
    """أسماء السور بترتيبها من عناوين ملفات الخلاف (فقرات «سورة X»)."""
    import docx, glob
    f = sorted(glob.glob('sources/khilaf/*عاصم*كامل*'))[0]
    out = [p.text.strip()[5:].strip() for p in docx.Document(f).paragraphs if p.text.strip().startswith('سورة ')]
    assert len(out) == 114, len(out)
    return out


def qalun_words():
    return riwaya_words(DOC)


def sura_index(suras):
    return {norm(re.sub(r'^ال', '', s)): i + 1 for i, s in enumerate(suras)} | \
           {norm(s): i + 1 for i, s in enumerate(suras)}


def main():
    suras, words = qalun_words()
    print(len(suras), 'سورة ·', len(words), 'كلمة')
    ayat = Counter((w['sura'], w['ayah']) for w in words)
    print('آيات:', len(ayat))
    idx = sura_index(plain_names())
    by_ayah = {}
    for w in words:
        by_ayah.setdefault((w['sura'], w['ayah']), []).append(w)

    khilaf = json.load(open('out/khilaf.json', encoding='utf-8'))
    stats, linked, unlinked = Counter(), [], []
    for fname, doc in khilaf.items():
        for rec in doc['records']:
            sn = idx.get(norm(re.sub(r'^ال', '', rec['sura'] or ''))) or idx.get(norm(rec['sura'] or ''))
            toks = [key(t) for t in rec['qalun'].split()]
            ntoks = [cnorm(t) for t in toks]
            found = []
            for a in rec['ayat']:
                hit = None
                # الدرجات: exact (لفظ المجمع بعينه) ثم rasm (حروف الرسم) في الآية نفسها،
                # ثم shifted: أقرب آية في ±٣ لاختلاف العدّ بين حفص وقالون
                for tier, delta in (('exact', 0), ('rasm', 0), ('shifted', 1), ('shifted', 2), ('shifted', 3)):
                    cands = []
                    for da in ((0,) if delta == 0 else (-delta, delta)):
                        ws = by_ayah.get((sn, a + da), [])
                        if tier == 'exact':
                            ks, tt = [key(w['text']) for w in ws], toks
                        else:
                            ks, tt = [cnorm(key(w['text'])) for w in ws], ntoks
                        for i in range(len(ks) - len(tt) + 1):
                            if ks[i:i + len(tt)] == tt:
                                cands.append((a + da, ws[i]['seq'], ws[i + len(tt) - 1]['seq'], tier, a))
                    if len(cands) == 1:
                        hit = cands[0]
                        break
                    if len(cands) > 1:        # أكثر من موضع بالمسافة نفسها: لا يُخمَّن
                        stats['ambiguous'] += 1
                        break
                if hit:
                    found.append(hit)
                    stats['tier_' + hit[3]] += 1
            if sn is None:
                stats['sura?'] += 1
            if found:
                stats['linked'] += 1
                linked.append({'file': fname, 'sura': sn, 'qalun': rec['qalun'], 'links': found,
                               'readings': rec['readings'], 'bayan': rec['bayan']})
            else:
                stats['unlinked'] += 1
                unlinked.append({'file': fname, 'sura': rec['sura'], 'ayat': rec['ayat'], 'qalun': rec['qalun']})
    print(dict(stats))
    json.dump({'suras': suras, 'words': words}, open('out/qalun_words.json', 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump({'linked': linked, 'unlinked': unlinked}, open('out/khilaf_linked.json', 'w', encoding='utf-8'), ensure_ascii=False)


if __name__ == '__main__':
    main()
