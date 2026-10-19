#!/usr/bin/env python3
"""تعرّف ضوئي على رسالة ابن الغزال، دفعةً دفعة.

الصفحة مطبوعة بعمودٍ واحد، فـ psm 3 يكفي ويضبط الترتيب.
"""
import os, subprocess, tempfile, time
from concurrent.futures import ThreadPoolExecutor

PDF, OUT, DPI, CHUNK, WORKERS = 'books/ghazzal.pdf', 'ocr/ghazzal', 300, 30, 2
env = dict(os.environ, OMP_THREAD_LIMIT='1')


def todo(pages):
    return [p for p in pages
            if not (os.path.exists(f'{OUT}/{p:05d}.txt')
                    and os.path.getsize(f'{OUT}/{p:05d}.txt') > 0)]


def do_chunk(pages):
    lo, hi = pages[0], pages[-1]
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(['pdftoppm', '-r', str(DPI), '-f', str(lo), '-l', str(hi),
                        '-png', PDF, os.path.join(td, 'p')], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        def one(p):
            img = None
            for w in (len(str(hi)), 3, 4, 5):
                c = os.path.join(td, f'p-{p:0{w}d}.png')
                if os.path.exists(c):
                    img = c
                    break
            if img is None:
                return
            r = subprocess.run(['tesseract', img, 'stdout', '-l', 'ara', '--psm', '3'],
                               capture_output=True, text=True, env=env)
            open(f'{OUT}/{p:05d}.txt', 'w', encoding='utf-8').write(r.stdout)
        with ThreadPoolExecutor(WORKERS) as ex:
            list(ex.map(one, pages))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    allp = list(range(1, 496))
    t0 = time.time()
    for i in range(0, len(allp), CHUNK):
        ch = todo(allp[i:i + CHUNK])
        if ch:
            do_chunk(ch)
        print(f'{min(i+CHUNK,len(allp))}/{len(allp)}  {time.time()-t0:.0f}s', flush=True)
