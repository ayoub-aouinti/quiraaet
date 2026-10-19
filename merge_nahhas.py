#!/usr/bin/env python3
"""إدخال أحكام «القطع والائتناف» في قاعدة المشروع.

الكتابُ يسوق في الموضع الواحد أقوالاً لغير واحد، فلا يصحّ تسجيلها حكماً
واحداً مبهماً. فيُقدَّم قولُ صاحب الكتاب (أبي جعفر النحّاس) إن صرّح به،
وتُحفظ بقية الأقوال بأسماء قائليها في الحاشية، ولا يُلفَّق منها حكمٌ مركَّب.

وكلُّ ما يدخل هنا status='proposed' لا 'imported'، لأنه استخراجٌ آليّ لم
يُراجَع بعدُ، وقاعدةُ المشروع ألّا يُعرض المقترَح معروضَ المحقَّق.
"""
import csv, sqlite3, sys
from collections import defaultdict, Counter

SOURCE = 'nahhas'
CAT = {'ت': ('tam', 0), 'ك': ('kafi', 0), 'ح': ('hasan', 0),
       'ص': ('jaiz', 1), 'لا': ('mamnu', 0), 'و': ('jaiz', 1),
       # نفيُ مرتبةٍ بعينها لا نفيُ وقف: «ليس بقطعٍ كافٍ» عند النحاس وقفٌ
       # قائمٌ دون الكفاية، لا منعاً. فلا فئةَ عامّةً له ولا لون.
       'لا-ت': (None, 0), 'لا-ك': (None, 0), 'لا-ح': (None, 0),
       'لا-ص': (None, 0), 'لا-ر': (None, 0)}
TERM = {'ت': 'تامّ', 'ك': 'كافٍ', 'ح': 'حسن', 'ص': 'صالح',
        'لا': 'ليس بوقف', 'و': 'موضع قطع',
        'لا-ت': 'ليس بتامّ', 'لا-ك': 'ليس بكافٍ', 'لا-ح': 'ليس بحسن',
        'لا-ص': 'ليس بصالح', 'لا-ر': 'نفيُ مرتبةٍ لم تتبيَّن'}
NEEDS_REVIEW = {'لا-ر': 'نفيُ مرتبةٍ لم تتبيَّن — يُراجَع لفظُ الكتاب'}
RANK = {'عالية': 3, 'متوسطة': 2, 'تحتاج مراجعة': 1}
OWNER = ('أبو جعفر', 'ابو جعفر', 'النحاس', 'أبي جعفر')


def load(path, method):
    out = []
    for r in csv.DictReader(open(path, encoding='utf-8-sig')):
        sym = r.get('symbol') or ''
        if sym not in CAT:
            continue
        out.append({
            'seq': int(r['seq']), 'symbol': sym,
            'raw': (r.get('term') or '').strip(),
            'sayer': (r.get('sayer') or '').strip(),
            'conf': r.get('conf') or 'متوسطة',
            'page': r.get('page'), 'method': method,
        })
    return out


def main(db, *pairs):
    rows = []
    for i in range(0, len(pairs), 2):
        rows += load(pairs[i], pairs[i + 1])
    byseq = defaultdict(list)
    for r in rows:
        byseq[r['seq']].append(r)

    recs = []
    for seq, items in byseq.items():
        own = [x for x in items if any(o in x['sayer'] for o in OWNER)]
        pool = own or items
        pool = sorted(pool, key=lambda x: -RANK.get(x['conf'], 1))
        best = pool[0]
        others = [x for x in items if x['symbol'] != best['symbol']]
        alt_syms = sorted({x['symbol'] for x in others})
        says = []
        for x in items:
            who = x['sayer'] or 'غير منسوب'
            says.append(f"{who}: {x['raw']}")
        seen, note = set(), []
        for s in says:
            if s not in seen:
                seen.add(s)
                note.append(s)
        cat, approx = CAT[best['symbol']]
        recs.append((
            seq, SOURCE, best['raw'], best['symbol'], TERM[best['symbol']],
            cat, approx,
            '/'.join(alt_syms) or None,
            '/'.join(TERM[s] for s in alt_syms) or None,
            ' · '.join(note[:6]) + (f" — ص{best['page']}" if best['page'] else ''),
            NEEDS_REVIEW.get(best['symbol']), 'proposed', best['conf'],
            ('قولُ صاحب الكتاب' if own else 'لم يُصرَّح بقائله في الموضع'),
        ))

    con = sqlite3.connect(db)
    con.execute('DELETE FROM rulings WHERE source=?', (SOURCE,))
    con.executemany('''INSERT OR REPLACE INTO rulings
        (seq,source,raw,symbol,term,category,approx,alt_symbol,alt_term,note,
         review,status,confidence,context) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', recs)
    con.execute("UPDATE sources SET has_text=1, name=?, author=?, died=? WHERE id=?",
                ('القطع والائتناف', 'أبو جعفر النحاس', '338هـ', SOURCE))
    con.commit()
    print('مداخل خام:', len(rows), '· مواضع فريدة:', len(recs))
    print('المرتبة:', Counter(r[3] for r in recs))
    print('الثقة:', Counter(r[12] for r in recs))
    print('فيها خلاف بين الأقوال:', sum(1 for r in recs if r[7]))
    print('منسوبة لصاحب الكتاب:', sum(1 for r in recs if r[13] == 'قولُ صاحب الكتاب'))


if __name__ == '__main__':
    main(*sys.argv[1:])
