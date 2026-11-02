import type { CSSProperties, ReactNode } from 'react';
import { fontStyle, paint, paintUnderline } from './paint';
import type { Group, Meta, MushafSura, QalunSura, ReadEntry, RiwayaMeta, Variant } from './types';

export const PALETTE = ['#d55e00', '#0072b2', '#009e73', '#cc79a7', '#e69f00', '#56b4e9', '#7a3e9d',
  '#b2182b', '#4d9221', '#8c6d31', '#1b7a8c', '#c51b8a', '#6a51a3', '#636363', '#1f9d8b', '#a65628',
  '#377eb8', '#984ea3', '#999999'];

export interface Colors { color: Record<string, string>; rev: Record<string, string> }

/** لون لكل قارئ (بالترتيب، دون قالون)، وخريطةٌ عكسية لون ← قارئ */
export function assignColors(groups: Group[]): Colors {
  const color: Record<string, string> = {}, rev: Record<string, string> = {};
  let ci = 0;
  for (const g of groups) for (const r of g.readers) {
    if (r.id === 'qalun') continue;
    color[r.id] = PALETTE[ci++ % PALETTE.length];
    rev[color[r.id]] = r.id;
  }
  return { color, rev };
}

export type Target =
  | { mode: 'q'; seq: number }
  | { mode: 'r'; q: number; k: number; text: string; font: string };

export interface WordVM {
  key: string; plain: string; cls: string; style?: CSSProperties; node: ReactNode; target: Target;
  q?: number; seq?: number;
}
export interface AyahVM { no: number; words: WordVM[] }

export type Cover = Map<number, { e: ReadEntry; off: number }[]>;

/** لكل كلمة: العناصر التي تغطّيها والإزاحة داخل العبارة */
export function buildCover(reads: ReadEntry[], qtext: Map<number, string>): Cover {
  const cover: Cover = new Map();
  for (const e of reads) {
    let off = 0;
    for (let s = e.s; s <= e.e; s++) {
      if (!cover.has(s)) cover.set(s, []);
      cover.get(s)!.push({ e, off });
      off += (qtext.get(s) || '').length + 1;
    }
  }
  return cover;
}

export const riwOf = (meta: Meta, readerId: string) => meta.riwayat.find(r => r.reader === readerId);

export function nameOf(meta: Meta, id: string): string {
  for (const g of meta.groups) for (const r of g.readers) if (r.id === id) {
    const w = g.name.split(' ');    // «ابن كثير» و«أبو عمرو» كلمتان؛ وسائرها كلمة
    return r.name + ' (' + (w[0] === 'ابن' || w[0] === 'أبو' ? w[0] + ' ' + w[1] : w[0]) + ')';
  }
  return id;
}

/** نصُّ التقييد بحسب الحالة المذكورة في الملاحظة */
export function condText(r: Variant): string {
  const n = r.n || '', w = /وقف/.test(n), v = /وصل/.test(n);
  return w && !v ? 'مقيَّد وقفًا' : v && !w ? 'مقيَّد وصلًا' : 'مقيَّد (في بعض الأحوال)';
}

/* ---------- وجه «قالون ومقابلة القراءات» ---------- */
export function buildQ(qd: QalunSura, cover: Cover, sel: Set<string>, c: Colors): AyahVM[] {
  return qd.ayat.map(([no, words]) => ({
    no,
    words: words.map(([seq, text]) => {
      const marks = new Map<number, string>(), exact = new Map<number, string>();
      const cols: string[] = [];
      for (const { e, off } of cover.get(seq) || []) {
        for (const r of e.r) {
          if (!sel.has(r.id) || r.same) continue;
          const col = c.color[r.id];
          if (!cols.includes(col)) cols.push(col);
          for (const i of r.dq || []) { const k = i - off; if (k >= 0 && k < text.length && !marks.has(k)) marks.set(k, col); }
          for (const i of r.dqa || []) { const k = i - off; if (k >= 0 && k < text.length) exact.set(k, col); }
        }
      }
      let style: CSSProperties | undefined;
      if (cols.length) {
        const stops = cols.map((col, i) => `${col} ${i * 100 / cols.length}% ${(i + 1) * 100 / cols.length}%`);
        style = { backgroundImage: `linear-gradient(to left,${stops.join(',')})` };
      }
      return {
        key: String(seq), plain: text, cls: 'w' + (cols.length ? ' diff' : ''), style, seq,
        node: paint(text, marks, exact, c.rev), target: { mode: 'q', seq } as Target,
      };
    }),
  }));
}

/* ---------- مصحف الرواية: نصُّه كما في ملف المجمع، وما يخالف قالون ملوَّن ---------- */
export function buildR(rd: MushafSura, riw: RiwayaMeta): AyahVM[] {
  return rd.ayat.map(([no, words]) => ({
    no,
    words: words.map(([text, q, k, d], i) => ({
      key: `${no}-${i}`, plain: text, cls: 'w' + (k ? ' k' + k : ''), q,
      node: d ? paintUnderline(text, new Set(d)) : text,
      target: { mode: 'r', q, k, text, font: riw.mush! } as Target,
    })),
  }));
}

/* ---------- لمن لا مصحف له: مصحف قالون وقد استُبدلت كلمةُ كل موضعِ خلافٍ بكلمة قراءته (≈ حيث قُرِّبت) ---------- */
export function buildX(qd: QalunSura, reads: ReadEntry[], rid: string): AyahVM[] {
  const rep = new Map<number, Variant>(), skip = new Set<number>(), mark = new Set<number>();
  for (const e of reads) {
    const r = e.r.find(x => x.id === rid);
    if (!r || r.same) continue;
    if (e.s !== e.e && [...Array(e.e - e.s + 1).keys()].some(i => rep.has(e.s + i) || skip.has(e.s + i))) continue;
    if (rep.has(e.s) || mark.has(e.s)) continue;
    if (r.x) {
      rep.set(e.s, r);
      for (let s = e.s + 1; s <= e.e; s++) skip.add(s);
    } else for (let s = e.s; s <= e.e; s++) mark.add(s);
  }
  return qd.ayat.map(([no, words]) => ({
    no,
    words: words.filter(([seq]) => !skip.has(seq)).map(([seq, text]) => {
      const p = rep.get(seq);
      if (p) {
        const font = p.f || 'hafs';
        return {
          key: String(seq), plain: text, cls: 'w k1', q: seq, style: fontStyle(font),
          node: p.dx ? paintUnderline(p.x!, new Set(p.dx)) : p.x!,
          target: { mode: 'r', q: seq, k: 1, text: p.x!, font } as Target,
        };
      }
      const nt = mark.has(seq);
      return {
        key: String(seq), plain: text, cls: 'w' + (nt ? ' k1 nt' : ''), q: seq, node: text,
        target: { mode: 'r', q: seq, k: nt ? 1 : 0, text, font: 'qalun' } as Target,
      };
    }),
  }));
}
