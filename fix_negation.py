#!/usr/bin/env python3
"""إصلاحُ رموز النفي في ملفّات المحاذاة الجاهزة.

كان كلُّ نفيٍ يصير رمزَ «لا» — أي ممنوعاً — سواءٌ نفى الوقفَ نفسَه أو نفى
مرتبةً من مراتبه. و«ليس بتامّ» ليس منعاً: قال ابنُ الأخشيذ «﴿بسم الله﴾ حسنٌ
وليس بتمام»، ونقل الواحديُّ عن ابن الأنباري «الوقف هنا حسنٌ، وليس بتامٍّ ولا
كافٍ». فالوقفُ قائمٌ والمنفيُّ رتبتُه.

والمحاذاةُ نفسُها سليمةٌ لم يُطعَن فيها، فلا تُعاد: يُعاد حسابُ عمود symbol
وحدَه من لفظ الكتاب (term) وحقلِ النفي (negated)، بالقواعد الجديدة في
align_rulings.negation_of. وما عدا ذلك يُنقَل حرفاً بحرف.

    python3 fix_negation.py out/anbari_aligned.csv [...]

يكتب لكلِّ ملفٍّ نظيرَه بلاحقة .fixed.csv، ويطبع ما تغيَّر.
"""
import csv, sys
from collections import Counter

from align_rulings import negation_of, symbol_of


def fix(path):
    rows = list(csv.DictReader(open(path, encoding='utf-8-sig')))
    if not rows:
        return path, Counter()
    fields = list(rows[0].keys())
    changed = Counter()
    for r in rows:
        term = (r.get('term') or '').strip()
        neg = str(r.get('negated') or '').strip() in ('1', 'نعم', 'true', 'True')
        old = (r.get('symbol') or '').strip()
        new = negation_of(term, neg)
        if new is None:
            new = symbol_of(term)
        if new is None:          # لا يُفهَم: يُترك كما كان ولا يُخمَّن
            changed['تُرك بلا تفسير'] += 1
            continue
        if new == old:
            continue
        # الإصلاحُ مقصورٌ على بابه: ما كان نفياً فصار نفياً أدقَّ، وما قُرئ
        # إثباتاً وهو نفي. وما عدا ذلك يبقى كما حُوذي أولَ مرّة، فجدولُ
        # المراتب تغيَّر منذ ذلك الحين، وإعادةُ اشتقاقه كلِّه تغييرٌ لم يُؤذَن
        # فيه ولم يُراجَع — وقد ظهر منه ١٢ صفّاً في «و» وحدَها.
        if old == 'لا' or new.startswith('لا-'):
            changed[f'{old} ← {new}'] += 1
            r['symbol'] = new
        else:
            changed[f'تُرك بحاله: {old} (كان سيصير {new})'] += 1
    out = path.replace('.csv', '.fixed.csv')
    with open(out, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    return out, changed


if __name__ == '__main__':
    grand = Counter()
    for p in sys.argv[1:]:
        out, ch = fix(p)
        print(f'\n{p}')
        if not ch:
            print('  لا تغيير')
        for k, v in ch.most_common():
            print(f'  {k:18s} {v:5d}')
            grand[k] += v
    print('\n— الجملة —')
    for k, v in grand.most_common():
        print(f'  {k:18s} {v:5d}')
