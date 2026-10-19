#!/usr/bin/env python3
"""تعرّفٌ ضوئي على متن المعجم، دفعةً دفعة.

تُرسَم الدفعة كلها بأمر واحد لـ pdftoppm لأن فتح الملف لكل صفحة على حدة
يكلّف أضعاف ما يكلّفه الرسم نفسه، ثم يُعرَّف على الصور على التوازي.
"""
import os, subprocess, tempfile, time
from concurrent.futures import ThreadPoolExecutor

PDF = 'books/mujam.pdf'
OUT = 'ocr/mujam'
DPI = 300
CHUNK = 30
WORKERS = 2

env = dict(os.environ, OMP_THREAD_LIMIT='1')


def todo(pages):
    return [p for p in pages
            if not (os.path.exists(f'{OUT}/{p:05d}.txt')
                    and os.path.getsize(f'{OUT}/{p:05d}.txt') > 0)]


def do_chunk(pages):
    lo, hi = pages[0], pages[-1]
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(['pdftoppm', '-r', str(DPI), '-f', str(lo), '-l', str(hi),
                        '-png', PDF, os.path.join(td, 'p')],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        width = len(str(hi))
        def one(p):
            img = None
            for w in (len(str(hi)), 4, 5, 6):
                c = os.path.join(td, f'p-{p:0{w}d}.png')
                if os.path.exists(c):
                    img = c
                    break
            if img is None:
                return
            r = subprocess.run(['tesseract', img, 'stdout', '-l', 'ara', '--psm', '6'],
                               capture_output=True, text=True, env=env)
            with open(f'{OUT}/{p:05d}.txt', 'w', encoding='utf-8') as f:
                f.write(r.stdout)
        with ThreadPoolExecutor(WORKERS) as ex:
            list(ex.map(one, pages))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    allp = list(range(30, 2433))
    t0 = time.time()
    done = 0
    for i in range(0, len(allp), CHUNK):
        chunk = todo(allp[i:i + CHUNK])
        if chunk:
            do_chunk(chunk)
        done += len(allp[i:i + CHUNK])
        print(f'{done}/{len(allp)}  {time.time()-t0:.0f}s', flush=True)
