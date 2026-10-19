#!/usr/bin/env python3
"""OCR صفحات مُحدَّدة من ملف PDF ممسوح ضوئياً، بالعربية.

الاستعمال:
    python3 ocr_pdf.py <pdf> <out_dir> <pages>   حيث pages مثل 1-20 أو 5,9,13
النتيجة: ملف نصّي لكل صفحة باسم رقمها، يُعاد استعماله إن وُجد.
"""
import os, re, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor

DPI = 300


def parse_pages(spec):
    out = []
    for part in spec.split(','):
        part = part.strip()
        if '-' in part:
            a, b = part.split('-')
            out += list(range(int(a), int(b) + 1))
        elif part:
            out.append(int(part))
    return out


def ocr_one(pdf, out_dir, pg, psm=6):
    dst = os.path.join(out_dir, f'{pg:05d}.txt')
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        return pg, 'cached'
    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, 'p')
        subprocess.run(['pdftoppm', '-r', str(DPI), '-f', str(pg), '-l', str(pg),
                        '-png', pdf, base], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        imgs = sorted(f for f in os.listdir(td) if f.endswith('.png'))
        if not imgs:
            return pg, 'no-image'
        img = os.path.join(td, imgs[0])
        r = subprocess.run(['tesseract', img, 'stdout', '-l', 'ara',
                            '--psm', str(psm)],
                           capture_output=True, text=True)
        txt = r.stdout
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(txt)
    return pg, f'{len(txt)} حرفاً'


def run(pdf, out_dir, pages, workers=8, psm=6):
    os.makedirs(out_dir, exist_ok=True)
    with ThreadPoolExecutor(workers) as ex:
        res = list(ex.map(lambda p: ocr_one(pdf, out_dir, p, psm), pages))
    return res


def text(out_dir, pg):
    p = os.path.join(out_dir, f'{pg:05d}.txt')
    return open(p, encoding='utf-8').read() if os.path.exists(p) else ''


if __name__ == '__main__':
    pdf, out_dir, spec = sys.argv[1], sys.argv[2], sys.argv[3]
    psm = int(sys.argv[4]) if len(sys.argv) > 4 else 6
    pages = parse_pages(spec)
    for pg, st in run(pdf, out_dir, pages, psm=psm):
        print(pg, st)
