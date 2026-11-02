import type { ReactNode } from 'react';

const AR = '٠١٢٣٤٥٦٧٨٩';
export const arNum = (n: number) => String(n).replace(/\d/g, d => AR[+d]);

/** تقسيم الكلمة إلى حرفٍ وعلاماته: [موضع البداية، النص] */
export function clusters(text: string): [number, string][] {
  const out: [number, string][] = [];
  for (const m of text.matchAll(/[^\p{M}]\p{M}*|\p{M}+/gu)) out.push([m.index!, m[0]]);
  return out;
}

/**
 * marks: موضع ← لون (يلوّن العنقود كلَّه)؛ exact: موضع ← لون (يلوّن الحرفَ المعيَّن وحده ولو كان علامةً).
 * rev: لون ← معرّف القارئ، ليُعرَف أيّ قارئٍ لُوِّن حرفُه عند الضغط.
 */
export function paint(text: string, marks?: Map<number, string>, exact?: Map<number, string>,
  rev?: Record<string, string>): ReactNode {
  if (!marks?.size && !exact?.size) return text;
  const out: ReactNode[] = [];
  let run = '';
  let key = 0;
  const flush = () => { if (run) { out.push(run); run = ''; } };
  const put = (str: string, col: string) => {
    flush();
    out.push(<i key={key++} style={{ color: col }} data-r={rev?.[col]}>{str}</i>);
  };
  for (const [idx, str] of clusters(text)) {
    let col: string | null = null;
    if (marks) for (let k = 0; k < str.length; k++) if (marks.has(idx + k)) { col = marks.get(idx + k)!; break; }
    if (!col && exact?.has(idx)) col = exact.get(idx)!;
    if (col) { put(str, col); continue; }
    const hit = exact ? [...str].map((_, k) => k).filter(k => k > 0 && exact.has(idx + k)) : [];
    if (!hit.length) { run += str; continue; }
    for (let k = 0; k < str.length; k++) {
      if (exact!.has(idx + k) && k > 0) put(str[k], exact!.get(idx + k)!); else run += str[k];
    }
  }
  flush();
  return out;
}

/** في مصحف الرواية الحرفُ المخالف يُبرَز بخطٍّ سفلي */
export function paintUnderline(text: string, set: Set<number>): ReactNode {
  const out: ReactNode[] = [];
  let run = '';
  let key = 0;
  const flush = () => { if (run) { out.push(run); run = ''; } };
  for (const [idx, str] of clusters(text)) {
    let hit = false;
    for (let k = 0; k < str.length; k++) if (set.has(idx + k)) hit = true;
    if (hit) {
      flush();
      out.push(<i key={key++} style={{ textDecoration: 'underline', textDecorationThickness: '.08em' }}>{str}</i>);
    } else run += str;
  }
  flush();
  return out;
}

export const searchKey = (value: string) =>
  value.toLocaleLowerCase().normalize('NFKD').replace(/\p{M}/gu, '').trim();

export const fontStyle = (id: string) => ({ fontFamily: `"f-${id}", serif` });
