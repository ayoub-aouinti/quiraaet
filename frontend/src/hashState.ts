import { useCallback, useEffect, useState } from 'react';
import type { Meta, Mode, ViewState } from './types';

/* الحالة في الرابط: #s=<سورة>&m=q|r&w=<رواية>&r=<قراء>&o=<كلمة> (العقد نفسه كالتطبيق السابق) */

export function store(k: string, v: string) { try { localStorage.setItem(k, v); } catch { /* التخزين قد يكون ممنوعاً */ } }
export function load(k: string): string | null { try { return localStorage.getItem(k); } catch { return null; } }

export interface Parsed { state: ViewState; open: number; noScroll: boolean }

export function parseHash(meta: Meta, prev?: ViewState): Parsed {
  const raw = location.hash.slice(1) || load('iqraa') || '';
  const p = new URLSearchParams(raw);
  let sura = prev?.sura ?? 1;
  let mode: Mode = 'q';
  let riw = 'warsh';
  const s = +(p.get('s') ?? 0);
  if (s >= 1 && s <= 114) sura = s;
  if (p.get('m') === 'r') mode = 'r';
  const w = p.get('w');
  if (w && w !== 'qalun' && meta.riwayat.some(r => r.reader === w)) riw = w;
  const known = new Set(meta.groups.flatMap(g => g.readers.map(r => r.id)));
  const sel = new Set((p.get('r') ?? '').split('|').filter(x => known.has(x) && x !== 'qalun'));
  return { state: { sura, mode, riw, sel }, open: +(p.get('o') ?? 0) || 0, noScroll: p.get('ns') === '1' };
}

function writeHash(st: ViewState) {
  const p = new URLSearchParams({ s: String(st.sura), m: st.mode, w: st.riw, r: [...st.sel].join('|') });
  history.replaceState(null, '', '#' + p.toString());
  store('iqraa', p.toString());
}

export function useHashState(meta: Meta) {
  const [parsed, setParsed] = useState<Parsed>(() => parseHash(meta));
  const [open, setOpen] = useState(parsed.open);

  const update = useCallback((patch: Partial<ViewState>) => {
    setParsed(prev => {
      const state = { ...prev.state, ...patch };
      writeHash(state);
      return { ...prev, state };
    });
    setOpen(0);
  }, []);

  useEffect(() => {
    const onHash = () => { const n = parseHash(meta); setParsed(n); setOpen(n.open); };
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, [meta]);

  return { state: parsed.state, update, open, clearOpen: () => setOpen(0), noScroll: parsed.noScroll };
}
