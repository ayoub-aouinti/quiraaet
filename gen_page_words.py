#!/usr/bin/env python3
"""تحديث أحكام صفحة المصحف المعروضة في التصميم من قاعدة البيانات.

نصوصُ الروايات في الملف تبقى كما هي، وإنما تُعاد بناءُ أحكامِها لتشمل
المصادر المستجدَّة. ويُحفظ في كل حكمٍ مصطلحُ مصدره بلفظه، والفئةُ العامة
للّون، وحالُه (محقَّق أم مقترَح) لئلا يُعرض المقترَحُ معروضَ المحقَّق.
"""
import json, sqlite3

PATH = 'out/page_words.json'
d = json.load(open(PATH, encoding='utf-8'))
seqs = sorted({w['s'] for w in d['pagew']['hafs'] if w.get('s')})

con = sqlite3.connect('out/waqf.db')
con.row_factory = sqlite3.Row
rul = {}
qs = ','.join('?' * len(seqs))
for r in con.execute(f'''SELECT seq, source, symbol, raw, term, category, approx, status
                         FROM rulings WHERE seq IN ({qs})''', seqs):
    rul.setdefault(str(r['seq']), {})[r['source']] = {
        's': r['symbol'], 't': (r['raw'] or '').strip() or r['term'],
        'c': r['category'], 'a': bool(r['approx']), 'st': r['status'],
    }
d['rul'] = rul
json.dump(d, open(PATH, 'w', encoding='utf-8'), ensure_ascii=False)
print('كلمات الصفحة:', len(seqs), '· مواضع فيها حكم:', len(rul),
      '· مصادر:', sorted({s for v in rul.values() for s in v}))
