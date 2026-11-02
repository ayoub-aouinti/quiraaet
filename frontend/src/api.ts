import type { MushafSura, Meta, QalunSura, ReadEntry } from './types';

const cache = new Map<string, Promise<unknown>>();

function getJSON<T>(path: string): Promise<T> {
  let p = cache.get(path) as Promise<T> | undefined;
  if (!p) {
    p = fetch(path).then(r => {
      if (!r.ok) throw new Error(`${path} (${r.status})`);
      return r.json() as Promise<T>;
    }).catch(err => {
      cache.delete(path); // une erreur réseau ne doit pas empêcher une nouvelle tentative
      throw err;
    });
    cache.set(path, p);
  }
  return p;
}

export const fetchMeta = () => getJSON<Meta>('/api/meta/');
export const fetchQalun = (n: number) => getJSON<QalunSura>(`/api/suras/${n}/qalun/`);
export const fetchReads = (n: number) => getJSON<ReadEntry[]>(`/api/suras/${n}/reads/`);
export const fetchMushaf = (mushaf: string, n: number) => getJSON<MushafSura>(`/api/mushafs/${mushaf}/${n}/`);
