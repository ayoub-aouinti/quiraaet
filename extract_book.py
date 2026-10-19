#!/usr/bin/env python3
"""استخراج مواضع الوقف من كتاب وقف ومحاذاتها على فهرس الكلمات.

المدخل: الكتاب بصيغة docx أو pdf أو txt + ملف إعداد للكتاب.
المخرج: مواضع مقترحة بثلاث درجات ثقة، وقائمة مراجعة لما لم يُحسم.

لا يُدخَل أي اقتراح في قاعدة البيانات إلا بعد اعتماد المراجع المتخصص.
"""
import json, re, csv, sys, os
from locator import Locator
from normalize import norm
import readers

SURA_HEAD = re.compile(r'(?:^|\n)\s*(?:باب\s+)?(?:ذكر\s+)?سورة\s+([^\n،،\.]{2,30})')
# اقتباس قرآني بين قوسي تنصيص. القوسان يَرِدان منعكسين في مخرجات بي دي إف
# بسبب الاتجاه ثنائي النص، فيقبل النمط الترتيبين معاً.
BRACKET = '﴿﴾«»'
QUOTE_RE = re.compile(r'[' + BRACKET + r']\s*([^' + BRACKET + r']{2,200}?)\s*[' + BRACKET + r']')


def load_cfg(path):
    return json.load(open(path, encoding='utf-8'))


def sura_number(name, suras):
    n = norm(name)
    for num, sn in suras.items():
        if norm(sn) == n or n in norm(sn) or norm(sn) in n:
            return num
    return None


def extract(text, cfg, loc, suras, ocr=False):
    """يمرّ على النصّ فقرةً فقرة متتبّعاً السورة الجارية."""
    # المصطلحات تُطابَق بعد تجريدها من الضبط، لأن موضع التنوين يختلف بين
    # المطبوع والمستخرَج («كافٍ» تُستخرج أحياناً «كاٍف»).
    terms = cfg['terms']                      # {"تام": "ت", "كاف": "ك", ...}
    tmap = {}
    for k, v in terms.items():
        tmap.setdefault(' '.join(norm(x) for x in k.split()), (k, v))
    keys = sorted(tmap, key=len, reverse=True)
    # حدود الكلمات محفوظة، وإلا التُقط المصطلح من التقاء كلمتين لا من كلمة
    term_re = re.compile(r'(?:^|\s)(' + '|'.join(map(re.escape, keys)) + r')(?:\s|$)')

    def find_term(tail):
        # يُقطع البحث عند أول سطر جديد أو اقتباس تالٍ، فالحكم يلي آيته مباشرة
        cut = len(tail)
        for ch in ('\n', '﴿', '﴾', '«', '»'):
            p = tail.find(ch)
            if p != -1:
                cut = min(cut, p)
        flat = ' '.join(norm(x) for x in tail[:cut].split())
        m = term_re.search(' ' + flat + ' ')
        if not m:
            return None
        orig, sym = tmap[m.group(1)]
        return orig, sym, m.start()

    # مسح متتابع على النصّ كلّه: تُلتقط رؤوس السور والاقتباسات بمواقعها،
    # فتُنسب كل آية إلى آخر رأس سورة سبقها. هذا لا يتوقّف على تقسيم الفقرات،
    # وهو يختلف بين وورد وبي دي إف والتعرّف الضوئي.
    heads = []
    for h in SURA_HEAD.finditer(text):
        num = sura_number(h.group(1), suras)
        if num:
            heads.append((h.start(), num, h.group(1).strip()))

    def sura_at(pos):
        cur = (None, None)
        for start, num, name in heads:
            if start < pos:
                cur = (num, name)
            else:
                break
        return cur

    # وضعان: الأقواس حين يميّزها النصّ، وإلا المسح المباشر على فهرس القرآن.
    # يُجرَّب الأول، فإن لم يُثمر كفايةً يُعاد المسح بالثاني تلقائياً.
    def by_brackets():
        got = []
        for m in QUOTE_RE.finditer(text):
            q = m.group(1)
            if q.strip():
                got.append({'quote': q, 'at': m.start(), 'end': m.end(), 'run': None})
        return got

    def by_scan():
        # الحدّ ٢ كلمة، فكثير من مواضع الوقف قصير («هدى للمتقين»).
        # التتابعات القصيرة الملتبسة تُصفّى لاحقاً بحالتها لا بطولها.
        # الحدّ ٣ كلمات: ما دونه يلتبس بكلام الكتاب نفسه («ليس من»، «ولا من»)
        # فيُنتج مواضع كاذبة. الاقتباسات الأقصر تفوت هذا الوضع، وهي تُستدرك
        # يدوياً أو بوضع الأقواس حين يميّزها النصّ.
        return [{'quote': r['text'], 'at': r['start_char'], 'end': r['end_char'], 'run': r}
                for r in loc.scan_runs(text, min_words=3)]

    spots = by_brackets()
    mode = 'الأقواس'
    if len(spots) < max(3, len(loc.scan_runs(text, min_words=4)) // 2):
        spots = by_scan()
        mode = 'المسح المباشر'
    print(f'  وضع الكشف: {mode} — {len(spots)} اقتباساً')

    out = []
    for sp in spots:
        quote = sp['quote']
        tail = text[sp['end']:sp['end'] + 120]       # الحكم يأتي بعد الاقتباس عادةً
        tm = find_term(tail)
        if not tm:
            continue
        term_text, term_sym, _ = tm
        cur_sura, cur_name = sura_at(sp['at'])
        if sp['run']:
            r = loc.run_position(sp['run'], sura=cur_sura)
        else:
            r = loc.locate(quote, sura=cur_sura)
            if r['status'] == 'not_found' and cur_sura:
                r = loc.locate(quote)                 # أعِد المحاولة بلا قيد السورة
        rec = {
            'الاقتباس': quote[:80],
            'المصطلح': term_text,
            'الرمز': term_sym,
            'السورة في الكتاب': cur_name or '',
            'الحالة': r['status'],
            'عدد المرشحين': r['n'],
        }
        if r['pos']:
            p = r['pos']
            rec.update({'seq': p['end_seq'], 'الموضع': f"{p['sura_name']} {p['sura']}:{p['ayah']}",
                        'الوقف بعد': p['stop_word']})
        else:
            rec.update({'seq': None, 'الموضع': '', 'الوقف بعد': ''})
        conf = ('عالية' if r['status'] == 'unique' and cur_sura
                else 'متوسطة' if r['status'] == 'unique'
                else 'تحتاج مراجعة')
        # التعرّف الضوئي قد يبتر التتابع فيعطي كلمة وقف سابقة لموضعها،
        # فلا يُرفع أي ناتج منه إلى الثقة العالية مهما بدا محسوماً.
        if ocr and conf == 'عالية':
            conf = 'متوسطة'
        rec['الثقة'] = conf
        rec['ملاحظة'] = ('ناتج تعرّف ضوئي — تأكّد من كلمة الوقف' if ocr else '')
        out.append(rec)
    return out


def main(book_txt, cfg_path, words_indexed, outdir):
    cfg = load_cfg(cfg_path)
    loc = Locator(words_indexed)
    suras = {w['sura']: w['sura_name'] for w in loc.w}
    print(f'قراءة {os.path.basename(book_txt)} ...')
    text = readers.clean(readers.read(book_txt))

    info = readers.last_read_info()
    rows = extract(text, cfg, loc, suras, ocr=info['ocr_pages'] > 0)
    high = [r for r in rows if r['الثقة'] == 'عالية']
    rest = [r for r in rows if r['الثقة'] != 'عالية']

    base = os.path.join(outdir, cfg['id'])
    for name, data in (('_proposed.csv', high), ('_review.csv', rest)):
        if not data:
            continue
        with open(base + name, 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(data)

    print(f"{cfg['name']}: استُخرج {len(rows)} موضعاً")
    print(f"  ثقة عالية (محسومة بالسورة): {len(high)}  ->  {cfg['id']}_proposed.csv")
    print(f"  تحتاج مراجعة: {len(rest)}  ->  {cfg['id']}_review.csv")
    return rows


if __name__ == '__main__':
    main(*sys.argv[1:5])
