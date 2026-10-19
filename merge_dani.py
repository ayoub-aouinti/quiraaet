#!/usr/bin/env python3
"""إدخالُ «المكتفى» للدانيِّ نصّاً، ومقابلتُه بالجدول المستورَد شاهدَين.

في القاعدة قبل هذا جدولٌ مستورَدٌ من ملف الإكسل الأول: ٤٧٣٩ موضعاً برموزٍ
مجرَّدة (ك، ت، أك، أت) بلا لفظِ المؤلف ولا علّته ولا عزوه. وهذا الاستخراجُ
نصُّ الكتاب نفسِه من الشاملة.

وهما شاهدان مستقلّان على كتابٍ واحد، فلا يُطرَح أحدُهما للآخر، وإنما
يُقابَلان:

* ما اتفقا فيه فقد تعدَّد شاهدُه، فيُرفَع إلى الثقة العالية ويُعلَّم باتفاقهما.
* ما اختلفا فيه يُثبَت الاختلافُ بنصِّ الرمزَين ولا يُرجَّح، ويُحال على
  المراجعة. فالتعارضُ بين شاهدَين خبرٌ ينفع الباحث، وطمسُه بترجيحٍ آليٍّ
  إتلافٌ له.
* ما انفرد به الاستخراجُ يدخل مقترَحاً كغيره.
* ما انفرد به الجدولُ المستورَد يبقى كما هو، ولا يُحذَف لأن الاستخراجَ لم
  يبلغه: فالاستخراجُ يُسقِط ما لا يطابق المصحف، والإسقاطُ ليس نفياً.

والرمزُ المستورَد يُقرأ على ما في الملف: ك كافٍ، ت تامّ، أك أكفى (وهي
كفايةٌ)، أت أتمّ (وهو تمام)، ح حسن، ص صالح. و«ك/ت» قولان في الموضع.
"""
import csv, json, sqlite3, sys
from collections import defaultdict, Counter

# قراءةُ رموز الجدول المستورَد. وهي رموزُ ناسخِ الملف لا رموزَ الداني،
# فتُقرأ على ظاهرها ولا يُزاد عليها.
XL = {'ك': {'ك'}, 'ت': {'ت'}, 'ح': {'ح'}, 'ص': {'ص'},
      'أك': {'ك'}, 'اك': {'ك'}, 'أت': {'ت'}, 'ات': {'ت'},
      'ك/ت': {'ك', 'ت'}, 'ت/ك': {'ت', 'ك'}, 'ت/ح': {'ت', 'ح'},
      'ح/ت': {'ح', 'ت'}, 'ك/ح': {'ك', 'ح'}, 'التمام': {'ت'}}
RANK = {'عالية': 3, 'متوسطة': 2, 'تحتاج مراجعة': 1}

# الجدولان من merge_book لا نسخةٌ منهما، فنسختان تتفرّقان بعد حين
from merge_book import CAT, TERM


def main(db, csv_path):
    meta = json.load(open('books.json', encoding='utf-8'))['dani']
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row

    # الشاهدُ الأول: الجدولُ المستورَد
    old = {}
    for r in con.execute("SELECT seq, raw, symbol, review FROM rulings WHERE source='dani'"):
        old[r['seq']] = {'raw': (r['raw'] or '').strip(), 'symbol': r['symbol'],
                         'review': r['review']}

    # الشاهدُ الثاني: نصُّ الكتاب
    rows = defaultdict(list)
    for r in csv.DictReader(open(csv_path, encoding='utf-8-sig')):
        sym = (r.get('symbol') or '').strip()
        if sym not in CAT:
            continue
        rows[int(r['seq'])].append({
            'symbol': sym, 'raw': (r.get('term') or '').strip(),
            'sayer': (r.get('sayer') or '').strip(),
            'conf': r.get('conf') or 'متوسطة', 'page': r.get('page'),
        })

    recs, tally = [], Counter()
    for seq, items in rows.items():
        # قولُ الدانيِّ هو المجرَّدُ من العزو، وما عُزي فلغيره
        own = [x for x in items if not x['sayer'] or x['sayer'] == '-']
        pool = sorted(own or items, key=lambda x: -RANK.get(x['conf'], 1))
        best = pool[0]
        alt = sorted({x['symbol'] for x in items if x['symbol'] != best['symbol']})

        seen, note = set(), []
        for x in items:
            s = f"{x['sayer'] or 'غير منسوب'}: {x['raw']}"
            if s not in seen:
                seen.add(s)
                note.append(s)
        note = note[:6]
        if best['page']:
            note.append(f"ص{best['page']}")

        conf, corrob = best['conf'], None
        o = old.get(seq)
        if o:
            want = XL.get(o['raw'])
            if want is None:
                corrob = f"الجدول المستورَد: «{o['raw']}» — رمزٌ لم يُفهَم"
                tally['رمزٌ مستورَدٌ لم يُفهَم'] += 1
            elif best['symbol'] in want:
                corrob = f"وافقه الجدول المستورَد («{o['raw']}»)"
                conf = 'عالية'            # شاهدان مستقلّان اتفقا
                tally['اتفق الشاهدان'] += 1
            else:
                corrob = (f"خالفه الجدول المستورَد: فيه «{o['raw']}» "
                          f"وفي الكتاب «{best['raw']}» — يُراجَع")
                conf = 'تحتاج مراجعة'      # تعارضٌ لا يُرجَّح آلياً
                tally['اختلف الشاهدان'] += 1
        else:
            tally['انفرد به الاستخراج'] += 1
        if corrob:
            note.append(corrob)

        cat, approx = CAT[best['symbol']]
        recs.append((seq, 'dani', best['raw'], best['symbol'], TERM[best['symbol']],
                     cat, approx,
                     '/'.join(alt) or None,
                     '/'.join(TERM[s] for s in alt) or None,
                     ' · '.join(note),
                     ('تعارضَ الشاهدان' if conf == 'تحتاج مراجعة' and corrob
                      and 'خالفه' in corrob else None),
                     'proposed', conf,
                     ('قولُ صاحب الكتاب' if own else 'لم يُصرَّح بقائله في الموضع')))

    kept = [s for s in old if s not in rows]
    tally['بقي من الجدول وحده'] = len(kept)

    # الجدولُ المستورَد يبقى لما لم يبلغه الاستخراج، ويُحذَف ما استُبدل به
    con.executemany('DELETE FROM rulings WHERE source=? AND seq=?',
                    [('dani', s) for s in rows])
    con.executemany('''INSERT OR REPLACE INTO rulings
        (seq,source,raw,symbol,term,category,approx,alt_symbol,alt_term,note,
         review,status,confidence,context) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', recs)
    con.execute("UPDATE sources SET has_text=1, edition=?, author=?, died=? WHERE id='dani'",
                (meta['edition'], meta['author'], meta['died']))
    con.commit()

    total = con.execute("SELECT COUNT(*) FROM rulings WHERE source='dani'").fetchone()[0]
    print('المكتفى في الوقف والابتدا — أبو عمرو الداني')
    print('  مواضعُ النصّ المستخرَج:', len(recs), '· وبقي من الجدول وحده:', len(kept))
    print('  مجموعُ مواضع الداني الآن:', total)
    for k, v in tally.most_common():
        print(f'  {k}: {v}')
    print('  المرتبة:', Counter(r[3] for r in recs).most_common())
    print('  الثقة:', Counter(r[12] for r in recs).most_common())
    print('  فيها عزوٌ لغير المؤلف:', sum(1 for r in recs if r[7]))


if __name__ == '__main__':
    main(*sys.argv[1:3])
