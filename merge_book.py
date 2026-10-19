#!/usr/bin/env python3
"""إدخال أحكام كتابٍ مستخرَجة في قاعدة المشروع — صيغةٌ عامّة.

هذه صورةٌ معمَّمة من merge_nahhas.py، تصلح لكل كتابٍ تُستخرج أحكامُه على
صيغة align_rulings.py. والقواعدُ هي هي:

* الكتبُ تسوق في الموضع الواحد أقوالاً لغير واحد، فيُقدَّم قولُ صاحب الكتاب
  إن صُرّح به، وتُحفظ بقيةُ الأقوال بأسماء قائليها في الحاشية، ولا يُلفَّق
  منها حكمٌ مركَّب.
* كلُّ ما يدخل هنا status='proposed' لا 'imported'، لأنه استخراجٌ آليّ لم
  يُراجَع بعدُ، وقاعدةُ المشروع ألّا يُعرض المقترَحُ معروضَ المحقَّق.
* المصطلحُ الأصليُّ يُحفظ في raw كما ورد، ولا يُستبدل بالتصنيف العام.

الاستعمال:
    python3 merge_book.py out/waqf.db <source_id> <csv> [csv ...]
وبياناتُ المصدر تُقرأ من books.json.
"""
import csv, json, sqlite3, sys
from collections import defaultdict, Counter

CAT = {'ت': ('tam', 0), 'ك': ('kafi', 0), 'ح': ('hasan', 0),
       'ص': ('jaiz', 1), 'ق': ('mamnu', 1), 'لا': ('mamnu', 0),
       'سن': ('tam', 1), 'آ': ('jaiz', 1), 'ج': ('jaiz', 0),
       'مف': ('jaiz', 1), 'ب': ('jaiz', 1), 'لز': ('tam', 1), 'شت': ('kafi', 1), 'و': ('jaiz', 1),
       # مراتبُ السجاوندي الخاصّة. والفئةُ العامّة هنا للّونِ وحدَه ومقرونةٌ
       # بـapprox، فإن مراتبَه ليست مراتبَ الجمهور: «المطلق» عنده ما حسُن
       # القطعُ عليه والابتداءُ بما بعده، و«المرخَّص لضرورة» رخصةٌ لطول الكلام
       # لا استحساناً للوقف.
       # وهذه الفئاتُ منقولةٌ عن terms.json بعينها، لا مستنبطةٌ من جديد: في
       # القاعدة ٣٥٠٩ مواضعَ بـ(ط) قُرئت كفايةً تقريبية، فلو قُرئت هنا تماماً
       # لاختلف تفسيرُ الحرف الواحد باختلاف الطريق الذي دخل منه.
       'مط': ('kafi', 1), 'مجو': ('jaiz', 1), 'مرخ': ('jaiz', 1),
       'قيل': ('jaiz', 1),
       # نفيُ مرتبةٍ بعينها: الوقفُ قائمٌ والمنفيُّ رتبتُه، فلا فئةَ عامّةً
       # له ولا لون. ولو حُمِل على mamnu لانقلب «حسنٌ لا تامّ» إلى «لا تقف».
       'لا-ت': (None, 0), 'لا-ك': (None, 0), 'لا-ح': (None, 0),
       'لا-ص': (None, 0), 'لا-ر': (None, 0)}
TERM = {'ت': 'تامّ', 'ك': 'كافٍ', 'ح': 'حسن', 'ص': 'صالح',
        'ق': 'قبيح', 'لا': 'ليس بوقف', 'سن': 'وقف سنّة',
        'آ': 'رأس آية', 'ج': 'جائز', 'مف': 'مفهوم',
        'ب': 'وقف البيان', 'لز': 'وقف لازم', 'شت': 'شبه التام',
        'و': 'موضع قطع',
        # بألفاظ terms.json نفسِها، لئلا يكون للشيء الواحد اسمان في الملف
        'مط': 'مطلق', 'مجو': 'مجوَّز لوجه', 'مرخ': 'مرخَّص ضرورةً',
        'قيل': 'قيل إنه وقف',
        'لا-ت': 'ليس بتامّ', 'لا-ك': 'ليس بكافٍ', 'لا-ح': 'ليس بحسن',
        'لا-ص': 'ليس بصالح', 'لا-ر': 'نفيُ مرتبةٍ لم تتبيَّن'}
# نفيُ مرتبةٍ لم يتبيَّن أيَّ مرتبةٍ نفى: يدخل معلَّماً، ولا يُخمَّن
NEEDS_REVIEW = {'لا-ر': 'نفيُ مرتبةٍ لم تتبيَّن — يُراجَع لفظُ الكتاب'}
TERM['لز'] = 'لازم'
RANK = {'عالية': 3, 'متوسطة': 2, 'تحتاج مراجعة': 1}


def load(path):
    out = []
    for r in csv.DictReader(open(path, encoding='utf-8-sig')):
        sym = (r.get('symbol') or '').strip()
        if sym not in CAT:
            continue
        out.append({
            'seq': int(r['seq']), 'symbol': sym,
            'raw': (r.get('term') or '').strip(),
            'sayer': (r.get('sayer') or '').strip(),
            'conf': r.get('conf') or 'متوسطة',
            'page': r.get('page'),
            'reason': (r.get('reason') or '').strip(),
            'ayah_book': (r.get('ayah_book') or '').strip(),
        })
    return out


def main(db, source_id, *csvs):
    meta = json.load(open('books.json', encoding='utf-8'))[source_id]
    owner = tuple(meta['owner'])

    rows = []
    for p in csvs:
        rows += load(p)
    byseq = defaultdict(list)
    for r in rows:
        byseq[r['seq']].append(r)

    # حدودُ النسخة المعتمدة: النسخةُ الناقصة لا تُنسب إليها أحكامٌ فيما لم
    # تبلغه، فما وقع خارج مداها خطأُ مطابقةٍ يُسقَط ولا يُثبَت على المؤلف.
    out_of_scope = 0
    if 'suras' in meta:
        lo, hi = meta['suras']
        words = json.load(open('out/words_indexed.json', encoding='utf-8'))
        if isinstance(words, dict):
            words = words['words']
        sura_of_seq = {x['seq']: x['sura'] for x in words}
        for seq in list(byseq):
            s = sura_of_seq.get(seq)
            if s is None or not (lo <= s <= hi):
                out_of_scope += len(byseq.pop(seq))

    # في كتبٍ كـ«المكتفى» و«علل الوقوف» لا يُصرّح المؤلف باسمه، وإنما يَسوق
    # حكمَه مجرَّداً ثم يَعزو ما خالفه إلى أصحابه. فالمجرَّدُ من العزو هو قولُه،
    # وهذا عكسُ عادة غيره، فيُنصَّ عليه في books.json ولا يُحمَل على الظنّ.
    own_unattr = bool(meta.get('owner_unattributed'))

    recs = []
    for seq, items in byseq.items():
        if own_unattr:
            own = [x for x in items if not x['sayer'] or x['sayer'] == '-']
        else:
            own = [x for x in items if any(o in x['sayer'] for o in owner)] if owner else []
        pool = sorted(own or items, key=lambda x: -RANK.get(x['conf'], 1))
        best = pool[0]
        alt_syms = sorted({x['symbol'] for x in items if x['symbol'] != best['symbol']})
        # العلّةُ أولاً: هي لبُّ الكتاب في نحو «علل الوقوف» و«المرشد»، وهي
        # بلفظ المؤلف فلا تُلخَّص. ثم أقوالُ القائلين، ثم الإحالةُ على الصفحة
        # ورقمِ الآية — ورقمُ الآية إحداثيٌّ ثانٍ يُراجَع به الموضعُ في الكتاب.
        seen, note = set(), []
        for x in items:
            if x['reason'] and x['reason'] not in seen:
                seen.add(x['reason'])
                note.append(f"العلّة: {x['reason']}")
        for x in items:
            s = f"{x['sayer'] or 'غير منسوب'}: {x['raw']}"
            if s not in seen:
                seen.add(s)
                note.append(s)
        cat, approx = CAT[best['symbol']]
        recs.append((
            seq, source_id, best['raw'], best['symbol'], TERM[best['symbol']],
            cat, approx,
            '/'.join(alt_syms) or None,
            '/'.join(TERM[s] for s in alt_syms) or None,
            ' · '.join(note[:6]) + (
                (f" — ص{best['page']}" if best['page'] else '')
                + (f"/آية {best['ayah_book']}" if best['ayah_book'] else '')),
            NEEDS_REVIEW.get(best['symbol']), 'proposed', best['conf'],
            ('قولُ صاحب الكتاب' if own else 'لم يُصرَّح بقائله في الموضع'),
        ))

    con = sqlite3.connect(db)
    con.execute('DELETE FROM rulings WHERE source=?', (source_id,))
    con.executemany('''INSERT OR REPLACE INTO rulings
        (seq,source,raw,symbol,term,category,approx,alt_symbol,alt_term,note,
         review,status,confidence,context) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', recs)
    cols = {r[1] for r in con.execute('PRAGMA table_info(sources)')}
    if 'id' in cols:
        con.execute('INSERT OR IGNORE INTO sources (id,name) VALUES (?,?)',
                    (source_id, meta['name']))
        sets = ['name=?', 'has_text=1']
        vals = [meta['name']]
        for k, c in (('author', 'author'), ('died', 'died'), ('edition', 'edition')):
            if k in meta and c in cols:
                sets.append(f'{c}=?')
                vals.append(meta[k])
        if 'kind' in cols:
            sets.append("kind='book'")
        con.execute(f"UPDATE sources SET {', '.join(sets)} WHERE id=?",
                    (*vals, source_id))
    con.commit()
    print(f"{source_id} — {meta['name']}")
    print('مداخل خام:', len(rows), '· مواضع فريدة:', len(recs))
    if out_of_scope:
        print('مسقَطٌ خارج مدى النسخة:', out_of_scope)
    print('المرتبة:', Counter(r[3] for r in recs))
    print('الثقة:', Counter(r[12] for r in recs))
    print('فيها خلاف بين الأقوال:', sum(1 for r in recs if r[7]))
    print('منسوبة لصاحب الكتاب:', sum(1 for r in recs if r[13] == 'قولُ صاحب الكتاب'))


if __name__ == '__main__':
    main(*sys.argv[1:])
