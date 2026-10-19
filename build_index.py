#!/usr/bin/env python3
"""بناء فهرس السور والآيات لملف الوقف بمحاذاته على نص مرجعي بالرسم العثماني."""
import json, sys
from difflib import SequenceMatcher
from normalize import norm


def load_reference(path):
    """كل كلمة مع سورتها وآيتها وموضعها داخل الآية."""
    data = json.load(open(path, encoding='utf-8'))
    out = []
    for s in data:
        for v in s['verses']:
            for i, w in enumerate(v['text'].split(), start=1):
                out.append({
                    'sura': s['id'], 'sura_name': s['name'],
                    'ayah': v['id'], 'wpos': i, 'text': w, 'n': norm(w),
                })
    return out


def load_sheet(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True)
    ws = wb['مقارنة مذاهب الوقف']
    rows = []
    for r in ws.iter_rows(min_row=5, max_row=77442, values_only=True):
        seq, word = r[0], r[1]
        if not isinstance(seq, int) or not word:
            continue
        rows.append({
            'seq': seq, 'text': str(word).strip(), 'n': norm(str(word)),
            'letters': r[2],
            'dani': (str(r[5]).strip() if r[5] and str(r[5]).strip() else None),
            'saj': (str(r[6]).strip() if r[6] and str(r[6]).strip() else None),
        })
    return rows


def align(sheet, ref):
    """محاذاة تسلسل الكلمات: المطابق يأخذ موقعه، وغير المطابق يُعلَّم للمراجعة."""
    a = [x['n'] for x in sheet]
    b = [x['n'] for x in ref]
    sm = SequenceMatcher(None, a, b, autojunk=False)
    matched = 0
    gaps = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                r = ref[j1 + k]
                s = sheet[i1 + k]
                s.update(sura=r['sura'], sura_name=r['sura_name'],
                         ayah=r['ayah'], wpos=r['wpos'], ref_text=r['text'], conf='exact')
            matched += i2 - i1
        else:
            gaps.append({'tag': tag, 'sheet_from': i1, 'sheet_to': i2,
                         'ref_from': j1, 'ref_to': j2,
                         'sheet_words': [sheet[i]['text'] for i in range(i1, min(i2, i1 + 8))],
                         'ref_words': [ref[j]['text'] for j in range(j1, min(j2, j1 + 8))],
                         'sheet_seq': sheet[i1]['seq'] if i1 < len(sheet) else None})
    return matched, gaps


def fill_gaps(sheet, ref, gaps):
    """ملء الفجوات بالاستكمال من الجوار حين يكون العدد متساوياً، وإلا تُترك للمراجعة."""
    filled = 0
    for g in gaps:
        i1, i2, j1, j2 = g['sheet_from'], g['sheet_to'], g['ref_from'], g['ref_to']
        if (i2 - i1) == (j2 - j1) and (i2 - i1) > 0:
            for k in range(i2 - i1):
                r, s = ref[j1 + k], sheet[i1 + k]
                s.update(sura=r['sura'], sura_name=r['sura_name'],
                         ayah=r['ayah'], wpos=r['wpos'], ref_text=r['text'], conf='replace')
            filled += i2 - i1
            g['resolved'] = 'replace-1to1'
        else:
            anchor = ref[min(j1, len(ref) - 1)] if j1 < len(ref) else ref[-1]
            for i in range(i1, i2):
                sheet[i].update(sura=anchor['sura'], sura_name=anchor['sura_name'],
                                ayah=anchor['ayah'], wpos=None, ref_text=None, conf='approx')
            g['resolved'] = 'approx-anchor'
    return filled


def main(xlsx, quran_json, outdir):
    ref = load_reference(quran_json)
    sheet = load_sheet(xlsx)
    print(f'كلمات المرجع: {len(ref)}   كلمات الملف: {len(sheet)}')
    matched, gaps = align(sheet, ref)
    filled = fill_gaps(sheet, ref, gaps)
    exact = sum(1 for s in sheet if s.get('conf') == 'exact')
    repl = sum(1 for s in sheet if s.get('conf') == 'replace')
    approx = sum(1 for s in sheet if s.get('conf') == 'approx')
    print(f'مطابقة تامة: {exact}  استبدال ١:١: {repl}  تقريبية: {approx}  فجوات: {len(gaps)}')
    json.dump(sheet, open(f'{outdir}/words_indexed.json', 'w', encoding='utf-8'),
              ensure_ascii=False)
    json.dump(gaps, open(f'{outdir}/alignment_gaps.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    return sheet, gaps


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
