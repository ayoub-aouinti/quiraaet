#!/usr/bin/env python3
"""قراءة نصّ ملف Word الثنائي القديم (.doc) دون Word أو LibreOffice.

يقرأ جدول القطع (piece table) من تدفّق الجداول ويفكّ كل قطعة بترميزها.
يكفي لنصوص المجمع: فقراتٌ نصّية بلا جداول معقّدة. الفقرة تنتهي بـ \\r.
"""
import struct, sys
import olefile


def read_doc(path):
    ole = olefile.OleFileIO(path)
    wd = ole.openstream('WordDocument').read()
    flags = struct.unpack_from('<H', wd, 0x0A)[0]
    tbl = ole.openstream('1Table' if flags & 0x0200 else '0Table').read()
    fc_clx, lcb_clx = struct.unpack_from('<II', wd, 0x01A2)
    clx = tbl[fc_clx:fc_clx + lcb_clx]
    i = 0
    while clx[i] == 1:                       # Prc: يُتجاوَز
        i += 3 + struct.unpack_from('<H', clx, i + 1)[0]
    assert clx[i] == 2, 'لا PlcPcd'
    n = struct.unpack_from('<I', clx, i + 1)[0]
    plc = clx[i + 5:i + 5 + n]
    count = (n - 4) // 12
    cps = struct.unpack_from('<%dI' % (count + 1), plc, 0)
    out = []
    for k in range(count):
        fc = struct.unpack_from('<I', plc, 4 * (count + 1) + 8 * k + 2)[0]
        length = cps[k + 1] - cps[k]
        if fc & 0x40000000:                  # مضغوط: cp1252
            off = (fc & 0x3FFFFFFF) // 2
            out.append(wd[off:off + length].decode('cp1252', 'replace'))
        else:
            out.append(wd[fc:fc + 2 * length].decode('utf-16-le', 'replace'))
    return ''.join(out)


if __name__ == '__main__':
    t = read_doc(sys.argv[1])
    sys.stdout.reconfigure(encoding='utf-8')
    print(len(t))
    print(t[:int(sys.argv[2]) if len(sys.argv) > 2 else 600])
