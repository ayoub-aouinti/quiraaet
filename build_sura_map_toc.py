#!/usr/bin/env python3
"""بناءُ خريطة السور من فهرس الكتاب في الشاملة، لا من علامات المستخرِجين.

فهرسُ الشاملة نصٌّ أصليٌّ لم يمرّ بنقلٍ ولا قراءةٍ آلية، فهو أوثقُ من أي
علامةٍ يكتبها مستخرِج. وإنما يُحتاج إلى حلِّ أسماءِ المؤلفين للسور، فإنهم
يسمّونها بأوائلها وبأسمائها القديمة: «المؤمن» غافر، و«سبح» الأعلى.

والضبطُ هنا ثلاثة: كلُّ عنوانٍ لا بدَّ أن يُحَلَّ إلى سورة، والسورُ لا بدّ
أن تجيء على ترتيب المصحف، والصفحاتُ لا بدّ أن تتزايد. فإن أخلَّ شيءٌ بهذا
وقف البناءُ ولم يُكتب شيء.
"""
import json, re, sys

# أسماءٌ يسمّي بها المتقدمون السورَ غيرَ أسمائها في المصاحف المعاصرة
ALIAS = {
    'ام القران': 1, 'فاتحة الكتاب': 1,
    'الملايكة': 35, 'المؤمن': 40, 'حم السجدة': 41, 'القتال': 47,
    'المنافقون': 63, 'المنافقين': 63, 'الرحيق': 83, 'المطففون': 83,
    'سبح': 87, 'الم نشرح': 94, 'الانشراح': 94, 'الشرح': 94,
    'البرية': 98, 'الهاكم': 102, 'الدين': 107, 'المسد': 111, 'تبت': 111,
    'اللهب': 111, 'الاخلاص': 112, 'التوحيد': 112, 'زلزلت': 99,
}
DROP = re.compile(r'^(سور[ةه]|سورتا)\s+|'
                  r'\s*(عليه السلام|عليها السلام|عليهم السلام|'
                  r'عليه الصلاة والسلام|عز وجل|ﷺ|﵇|﵍|﵈|﷿|\[.*?\])\s*')


def nrm(s):
    s = re.sub(r'[ً-ْٰۖ-ۭـ]', '', s)
    s = (s.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ٱ', 'ا')
          .replace('ى', 'ي').replace('ة', 'ه').replace('ؤ', 'و').replace('ئ', 'ي'))
    return re.sub(r'\s+', ' ', s).strip()


def main(words_json, toc_json, out_json):
    words = json.load(open(words_json, encoding='utf-8'))
    if isinstance(words, dict):
        words = words['words']
    names = {}
    for w in words:
        names.setdefault(nrm(w['sura_name']), w['sura'])
    # «ةه» في التسوية تُصيب أسماءً كـ«الواقعة»، فيُضاف الشكلُ الأصليُّ أيضاً
    for k, v in list(ALIAS.items()):
        names.setdefault(nrm(k), v)

    toc = json.load(open(toc_json, encoding='utf-8'))
    entries = toc['titles'] if isinstance(toc, dict) else toc

    out, unresolved, last_s, last_p = [], [], 0, 0
    for t in entries:
        raw = t['title_text']
        if not re.match(r'^\s*سور[ةه]|^\s*سورتا', raw):
            continue
        # «سورتا الفلق والناس» مدخلٌ لسورتين، تُؤخذ أولاهما وتُترك الثانية لموضعها
        name = DROP.sub('', raw).strip()
        name = re.split(r'\s+و(?=[الآأإ])', name)[0].strip()
        key = nrm(name)
        s = names.get(key)
        if s is None:
            s = names.get(key.replace('ه', 'ة'))
        if s is None:
            unresolved.append((raw, name))
            continue
        p = int(t['page_id'])
        # سورةٌ ترجع إلى الوراء أو صفحةٌ تنقص: خطأُ فهرسٍ أو عنوانٌ مكرَّر، يُطرح
        if s <= last_s or p < last_p:
            unresolved.append((raw, f'خارج الترتيب: سورة {s} ص {p}'))
            continue
        out.append([p, s])
        last_s, last_p = s, p

    if unresolved:
        print('عناوينُ لم تُحَلّ أو خرجت عن الترتيب:')
        for raw, why in unresolved:
            print('  -', raw[:70], '→', why)
    if len(out) < 100:
        sys.exit(f'خريطةٌ ناقصة: {len(out)} سورة فقط من ١١٤ — لا تُكتب.')

    json.dump({'starts': out}, open(out_json, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'حُفظ {out_json} — {len(out)} سورة، من ص{out[0][0]} إلى ص{out[-1][0]}')
    print('أولُها:', out[:3], '· آخرُها:', out[-3:])


if __name__ == '__main__':
    main(*sys.argv[1:4])
