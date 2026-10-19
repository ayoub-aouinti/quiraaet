#!/usr/bin/env python3
"""دمجُ نصِّ كتابٍ مع جدولٍ مستورَدٍ لنفس المصدر، شاهدَين لا بديلَين.

يُستعمل حيث يكون في القاعدة جدولٌ قديمٌ برموزٍ مجرَّدة، ويُستخرَج نصُّ
الكتاب من الشاملة. والقاعدةُ ألّا يُطرَح أحدُهما للآخر:

* ما اتفقا فيه تعدَّد شاهدُه، فيُرفَع إلى الثقة العالية ويُعلَّم باتفاقهما.
* ما اختلفا فيه يُثبَت فيه القولان بنصِّهما ولا يُرجَّح، ويُحال على المراجعة.
* ما انفرد به الاستخراجُ يدخل مقترَحاً.
* ما انفرد به الجدولُ يبقى كما هو ولا يُحذَف: إسقاطُ المحاذاة ليس نفياً.

وتُحفظ العلّةُ بلفظ المؤلف في الحاشية، فهي في كتابٍ كـ«علل الوقوف» أنفسُ
من الرمز نفسِه.

الاستعمال:
    python3 merge_witness.py out/waqf.db <source_id> <aligned.csv>
وجدولُ قراءة رموز الملف المستورَد يُقرأ من xl_symbols.json.
"""
import csv, json, sqlite3, sys
from collections import defaultdict, Counter
from merge_book import CAT, TERM, NEEDS_REVIEW

RANK = {'عالية': 3, 'متوسطة': 2, 'تحتاج مراجعة': 1}


def main(db, source_id, csv_path):
    meta = json.load(open('books.json', encoding='utf-8'))[source_id]
    xl = json.load(open('xl_symbols.json', encoding='utf-8'))
    tab = xl.get(source_id, {})
    XL = {k: set(v) for k, v in tab.get('map', {}).items()}
    own_unattr = bool(meta.get('owner_unattributed'))
    owner = tuple(meta.get('owner', ()))

    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    old = {r['seq']: (r['raw'] or '').strip() for r in
           con.execute('SELECT seq, raw FROM rulings WHERE source=?', (source_id,))}

    rows = defaultdict(list)
    for r in csv.DictReader(open(csv_path, encoding='utf-8-sig')):
        sym = (r.get('symbol') or '').strip()
        if sym not in CAT:
            continue
        rows[int(r['seq'])].append({
            'symbol': sym, 'raw': (r.get('term') or '').strip(),
            'sayer': (r.get('sayer') or '').strip(),
            'conf': r.get('conf') or 'متوسطة', 'page': r.get('page'),
            'reason': (r.get('reason') or '').strip(),
            'ayah_book': (r.get('ayah_book') or '').strip(),
        })

    recs, tally = [], Counter()
    for seq, items in rows.items():
        if own_unattr:
            own = [x for x in items if not x['sayer'] or x['sayer'] == '-']
        else:
            own = [x for x in items if any(o in x['sayer'] for o in owner)] if owner else []
        pool = sorted(own or items, key=lambda x: -RANK.get(x['conf'], 1))
        best = pool[0]
        alt = sorted({x['symbol'] for x in items if x['symbol'] != best['symbol']})

        note, seen = [], set()
        # العلّةُ أولاً، فهي المقصودُ من الكتاب
        for x in items:
            if x['reason'] and x['reason'] not in seen:
                seen.add(x['reason'])
                note.append(f"العلّة: {x['reason']}")
        for x in items:
            if x['sayer'] and x['sayer'] != '-':
                s = f"{x['sayer']}: {x['raw']}"
                if s not in seen:
                    seen.add(s)
                    note.append(s)
        note = note[:6]
        ref = f"ص{best['page']}" + (f"/آية {best['ayah_book']}" if best['ayah_book'] else '')
        note.append(ref)

        conf, corrob, clash = best['conf'], None, False
        o = old.get(seq)
        if o is not None:
            want = XL.get(o)
            if want is None:
                corrob = f"الجدول المستورَد: «{o}» — رمزٌ لم يُفهَم"
                tally['رمزٌ مستورَدٌ لم يُفهَم'] += 1
            elif best['symbol'] in want:
                corrob = f"وافقه الجدول المستورَد («{o}»)"
                conf = 'عالية'
                tally['اتفق الشاهدان'] += 1
            else:
                corrob = (f"خالفه الجدول المستورَد: فيه «{o}» وفي الكتاب "
                          f"«{best['raw']}» — يُراجَع")
                conf, clash = 'تحتاج مراجعة', True
                tally['اختلف الشاهدان'] += 1
        else:
            tally['انفرد به الاستخراج'] += 1
        if corrob:
            note.append(corrob)

        cat, approx = CAT[best['symbol']]
        recs.append((seq, source_id, best['raw'], best['symbol'], TERM[best['symbol']],
                     cat, approx,
                     '/'.join(alt) or None,
                     '/'.join(TERM[s] for s in alt) or None,
                     ' · '.join(note),
                     'تعارضَ الشاهدان' if clash
                     else NEEDS_REVIEW.get(best['symbol']),
                     'proposed', conf,
                     ('قولُ صاحب الكتاب' if own else 'لم يُصرَّح بقائله في الموضع')))

    kept = [s for s in old if s not in rows]
    tally['بقي من الجدول وحده'] = len(kept)

    con.executemany('DELETE FROM rulings WHERE source=? AND seq=?',
                    [(source_id, s) for s in rows])
    con.executemany('''INSERT OR REPLACE INTO rulings
        (seq,source,raw,symbol,term,category,approx,alt_symbol,alt_term,note,
         review,status,confidence,context) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', recs)
    sets, vals = ['has_text=1'], []
    for k, c in (('author', 'author'), ('died', 'died'), ('edition', 'edition')):
        if k in meta:
            sets.append(f'{c}=?')
            vals.append(meta[k])
    con.execute(f"UPDATE sources SET {', '.join(sets)} WHERE id=?", (*vals, source_id))
    con.commit()

    total = con.execute('SELECT COUNT(*) FROM rulings WHERE source=?',
                        (source_id,)).fetchone()[0]
    nreason = sum(1 for r in recs if 'العلّة:' in (r[9] or ''))
    print(f"{source_id} — {meta['name']}")
    print('  مواضعُ النصّ:', len(recs), '· بقي من الجدول وحده:', len(kept),
          '· المجموع الآن:', total)
    for k, v in tally.most_common():
        print(f'  {k}: {v}')
    print('  فيها علّةٌ بلفظ المؤلف:', nreason)
    print('  المرتبة:', Counter(r[3] for r in recs).most_common())
    print('  الثقة:', Counter(r[12] for r in recs).most_common())
    if tab.get('_ملاحظة'):
        print('  تنبيه:', tab['_ملاحظة'])


if __name__ == '__main__':
    main(*sys.argv[1:4])
