#!/usr/bin/env python3
"""تخزين صفحات كتابٍ من الشاملة في ملف JSONL محلي.

يقرأ من المدخل القياسي ناتجَ shamela_get_pages_range / get_book_section كما هو
(JSON فيه مفتاح pages)، فيضيف صفحاته إلى out/shamela/<book_id>.jsonl، ولا
يكرّر صفحةً خُزّنت قبلُ. الغرض أن يبقى المتن على القرص ليُعالَج بالبرامج.
"""
import json, os, sys

OUT = 'out/shamela'


def main(book_id):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, f'{book_id}.jsonl')
    seen = set()
    if os.path.exists(path):
        for line in open(path, encoding='utf-8'):
            try:
                seen.add(json.loads(line)['page_id'])
            except Exception:
                pass
    data = json.load(sys.stdin)
    added = 0
    with open(path, 'a', encoding='utf-8') as f:
        for p in data.get('pages', []):
            if p['page_id'] in seen:
                continue
            rec = {'page_id': p['page_id'],
                   'printed_page': p.get('printed_page'),
                   'part': p.get('part'),
                   'body': p.get('body', '')}
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
            seen.add(p['page_id'])
            added += 1
    pages = sorted(seen)
    print(f'{book_id}: أُضيفت {added} · المجموع {len(pages)} · '
          f'من {pages[0] if pages else "-"} إلى {pages[-1] if pages else "-"}')


if __name__ == '__main__':
    main(sys.argv[1])
