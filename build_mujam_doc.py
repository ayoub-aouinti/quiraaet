#!/usr/bin/env python3
"""بناء نموذج المستند (JSON) لملف الوورد المختصر من المعجم.

كل ما في هذا الملف مأخوذ من المعجم نفسه أو من قاعدة المشروع، ولا يُضاف
شيء من خارجهما. وما لم يُقرأ صريحاً يُوسَم «لم يُعثر على تصريح».
"""
import json, re
from collections import OrderedDict, Counter

IDX = 'out/mujam_index.json'
OUT = 'out/mujam_doc.json'

CENT_NAME = {2: 'الثاني', 3: 'الثالث', 4: 'الرابع', 5: 'الخامس', 6: 'السادس',
             7: 'السابع', 8: 'الثامن', 9: 'التاسع', 10: 'العاشر',
             11: 'الحادي عشر', 12: 'الثاني عشر', 13: 'الثالث عشر',
             14: 'الرابع عشر', 15: 'الخامس عشر'}

STATE_ORDER = ['مطبوع', 'محقَّق', 'مخطوط', 'مفقود']


def state_label(e, bab):
    """عبارة الحال: أولُ تصريحٍ وُجد في نطاق المدخل، أو تبويبُ المؤلف حين يكون هو التصريح."""
    if bab and bab.startswith('الباب الثاني'):
        # موضوع الباب الثاني «الكتب المفقودة»، فالتبويب نفسه تصريحٌ بالحال
        return 'مفقود'
    return e.get('label') or 'لم يُعثر على تصريح'


TOPIC = re.compile(r'(وقف|وقوف|ابتدا|مقاطع|مباد|تمام|قطع|ائتناف|استئناف|كلا|ماءات|'
                   r'موصول|مفصول|مقطوع|قرآن|مصحف|تلاوة|تجويد|قراء|آي|سور)')
# ألفاظ الاشتراك في المؤلف تتصدّر الاسم أحياناً فتُسقط
CARRY_HEAD = re.compile(r'^(ل?كلاهما|ل?كلتاهما|لها|كلها|لأربعة|الأربعة|الثلاثة|'
                        r'ثلاثتها|جميعها|وجميعها)\s+')


def clean_title(t):
    t = re.sub(r'\s+', ' ', t).strip(' .،؛:-–')
    t = t.replace('»', '،').replace('«', '')
    t = re.sub(r'\s*[،.]\s*$', '', t)
    if not TOPIC.search(t) or len(t) < 8:
        return None            # شظيّة سطرٍ لا عنوان، أو عنوانٌ تعذّرت قراءته
    return t


def clean_author(a):
    if not a:
        return '—'
    a = re.sub(r'\s+', ' ', a).strip(' .،؛:-–|')
    a = CARRY_HEAD.sub('', a).strip()
    # اسمٌ لم يبقَ منه إلا حروفٌ متكررة ليس اسماً
    letters = set(re.findall(r'[ء-ي]', a))
    if len(letters) < 6 or len(a) < 6:
        return '—'
    return a


def main():
    d = json.load(open(IDX, encoding='utf-8'))
    ents = d['entries']

    # تقسيم المداخل على الأبواب والقرون
    bab1, bab2, bab4 = [], [], []
    for e in ents:
        b = e.get('bab') or ''
        (bab2 if b.startswith('الباب الثاني') else
         bab4 if b.startswith('الباب الرابع') else bab1).append(e)

    def row(e):
        t = clean_title(e['title'])
        return {
            'title': t or 'مدخلٌ تعذّرت قراءة عنوانه في النسخة المصوَّرة',
            'unreadable': t is None,
            'author': clean_author(e.get('author')),
            'attributed': bool(e.get('attributed')),
            'state': state_label(e, e.get('bab')),
            'page': e.get('body_page'),
            'evidence': (e.get('evidence') or [])[:1],
        }

    centuries = []
    for c in sorted(CENT_NAME):
        rows = [row(e) for e in bab1 if e.get('century') == c]
        if rows:
            centuries.append({'century': c, 'name': CENT_NAME[c], 'rows': rows})

    maat = [row(e) for e in bab1 if not e.get('century')]

    lost = []
    for c in (2, 3, 4):
        rows = [row(e) for e in bab2 if e.get('century') == c]
        if rows:
            lost.append({'century': c, 'name': CENT_NAME[c], 'rows': rows})
    lost_other = [row(e) for e in bab2 if not e.get('century')]

    kalla = [row(e) for e in bab4]

    stats = {
        'total_parsed': len(ents),
        'bab1': len(bab1), 'bab2': len(bab2), 'bab4': len(bab4),
        'with_state': sum(1 for e in ents if e.get('state')),
        'located': sum(1 for e in ents if e.get('body_page')),
        'by_century': {c: sum(1 for e in bab1 if e.get('century') == c)
                       for c in CENT_NAME},
    }

    doc = {
        'centuries': centuries, 'maat': maat, 'lost': lost,
        'lost_other': lost_other, 'kalla': kalla, 'stats': stats,
    }
    json.dump(doc, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('قرون:', len(centuries), '· صفوف:',
          sum(len(c['rows']) for c in centuries) + len(maat)
          + sum(len(l['rows']) for l in lost) + len(lost_other) + len(kalla))
    print(stats)


if __name__ == '__main__':
    main()
