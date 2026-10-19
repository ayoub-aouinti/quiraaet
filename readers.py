#!/usr/bin/env python3
"""قراءة نصّ الكتاب من وورد أو بي دي إف أو نصّ عادي.

للـ PDF ثلاث حالات:
  - فيه طبقة نص  -> يُستخرج مباشرة (أسرع وأدقّ)
  - مصوّر        -> تعرّف ضوئي بالعربية
  - مختلط        -> يُفحص كل صفحة على حدة
"""
import os, re, subprocess, tempfile

MIN_CHARS_PER_PAGE = 120      # أقل من ذلك يُعدّ صفحة مصوّرة

# معلومات آخر قراءة: تُستعمل لخفض درجة الثقة حين يتدخّل التعرّف الضوئي
LAST = {'ocr_pages': 0, 'pages': 0, 'source': None}


def last_read_info():
    return dict(LAST)

# محارف التحكّم ثنائية الاتجاه التي يحشرها مستخرِجو بي دي إف
BIDI = re.compile(r'[‎‏‪-‮⁦-⁩­]')


def strip_bidi(t):
    return BIDI.sub('', t)


def read_txt(path):
    LAST.update(ocr_pages=0, pages=0, source='txt')
    for enc in ('utf-8', 'utf-8-sig', 'cp1256', 'utf-16'):
        try:
            return open(path, encoding=enc).read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    return open(path, encoding='utf-8', errors='replace').read()


def read_docx(path):
    LAST.update(ocr_pages=0, pages=0, source='docx')
    import docx
    d = docx.Document(path)
    parts = [p.text for p in d.paragraphs]
    for t in d.tables:                     # بعض الكتب تضع الأحكام في جداول
        for row in t.rows:
            parts.append(' | '.join(c.text.strip() for c in row.cells))
    return '\n\n'.join(x for x in parts if x.strip())


def _ocr_page(pdf_path, page_no, dpi=300, lang='ara'):
    import pytesseract
    from PIL import Image
    with tempfile.TemporaryDirectory() as td:
        base = os.path.join(td, 'p')
        subprocess.run(['pdftoppm', '-r', str(dpi), '-f', str(page_no), '-l', str(page_no),
                        '-png', pdf_path, base], check=True, capture_output=True)
        imgs = sorted(f for f in os.listdir(td) if f.endswith('.png'))
        if not imgs:
            return ''
        return pytesseract.image_to_string(Image.open(os.path.join(td, imgs[0])),
                                           lang=lang, config='--psm 6')


def _pdftotext_page(path, page_no):
    """pdftotext يعيد العربية بالترتيب المنطقي، بخلاف أكثر المكتبات."""
    try:
        r = subprocess.run(['pdftotext', '-enc', 'UTF-8', '-f', str(page_no),
                            '-l', str(page_no), path, '-'],
                           capture_output=True, timeout=60)
        return r.stdout.decode('utf-8', 'replace')
    except Exception:
        return ''


def read_pdf(path, ocr=True, lang='ara', progress=None):
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        n = len(pdf.pages)
    LAST.update(ocr_pages=0, pages=n, source='pdf')
    out, ocr_pages = [], []
    for i in range(1, n + 1):
        t = strip_bidi(_pdftotext_page(path, i)).strip()
        if len(t) < MIN_CHARS_PER_PAGE and ocr:
            ocr_pages.append(i)
            t = strip_bidi(_ocr_page(path, i, lang=lang)).strip()
        out.append(t)
        if progress and i % 20 == 0:
            progress(i, n)
    LAST['ocr_pages'] = len(ocr_pages)
    if ocr_pages:
        print(f'  تعرّف ضوئي على {len(ocr_pages)} صفحة من أصل {n}')
    return '\n\n'.join(out)


def read(path, **kw):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.docx':
        return read_docx(path)
    if ext == '.pdf':
        return read_pdf(path, **kw)
    if ext in ('.txt', '.md', ''):
        return read_txt(path)
    if ext == '.doc':
        raise SystemExit('صيغة .doc القديمة غير مدعومة — احفظ الملف بصيغة .docx أولاً')
    raise SystemExit(f'صيغة غير مدعومة: {ext}')


def fix_bracket_order(text):
    """إصلاح انعكاس قوسي الآية في مخرجات بي دي إف.

    يُخرج المستخرِج السطر بالترتيب البصري أحياناً، فيصير:
        .{الآية}﴾ {الحكم} ﴿
    بدل الترتيب المنطقي:
        ﴿{الآية}﴾ {الحكم}.
    فيُعاد ترتيب السطر حين يسبق القوسُ الخاتم القوسَ الفاتح.
    """
    out = []
    for ln in text.split('\n'):
        c, o = ln.find('﴾'), ln.find('﴿')
        if c != -1 and (o == -1 or o > c):
            quote = ln[:c].lstrip(' .،؛:-—')
            rest = ln[c + 1:]
            o2 = rest.find('﴿')
            ruling = rest[:o2] if o2 != -1 else rest
            if quote.strip():
                ln = f'﴿{quote.strip()}﴾ {ruling.strip()}'
        out.append(ln)
    return '\n'.join(out)


def clean(text):
    """تنظيف خفيف: توحيد الأسطر، وحذف أرقام الصفحات المنعزلة والهوامش المتكررة."""
    text = text.replace('\r\n', '\n').replace(' ', ' ')
    text = re.sub(r'[ \t]+', ' ', text)
    lines = []
    for ln in text.split('\n'):
        s = ln.strip()
        if re.fullmatch(r'[\d٠-٩\s\-—_\.]{0,12}', s):   # رقم صفحة أو سطر فارغ
            lines.append('')
            continue
        lines.append(s)
    return fix_bracket_order(re.sub(r'\n{3,}', '\n\n', '\n'.join(lines)))


if __name__ == '__main__':
    import sys
    t = clean(read(sys.argv[1]))
    print(f'طول النص: {len(t)} حرفاً، {t.count(chr(10))} سطراً')
    print(t[:1200])
