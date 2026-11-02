export interface SuraMeta { n: number; name: string; ayat: number }
export interface RiwayaMeta {
  id: string; name: string; font: string; ref: boolean; bsm: string; reader: string; mush?: string;
}
export interface Reader { id: string; name: string }
export interface Group { id: string; name: string; readers: Reader[] }
export interface Meta {
  suras: SuraMeta[]; riwayat: RiwayaMeta[]; groups: Group[];
  fonts: { id: string; font: string }[]; stats: Record<string, Record<string, number>>;
}

export type QalunWord = [seq: number, text: string];
export interface QalunSura { n: number; name: string; ayat: [ayah: number, words: QalunWord[]][] }

/** Variante d'un راوٍ à un موضع (champs du pipeline ; `bk` n'est jamais servi). */
export interface Variant {
  id: string; x?: string; f?: string; n?: string;
  dq?: number[]; dx?: number[]; dqa?: number[]; dxa?: number[];
  same?: boolean; cond?: unknown; khulf?: boolean;
}
export interface ReadEntry { s: number; e: number; t: string; u: boolean; r: Variant[]; b?: string }

/** [نص, رقم كلمة قالون المقابلة, تصنيف الفرق (0-3), مواضع الحروف المخالفة] */
export type MushafWord = [text: string, q: number, k: number, diff?: number[]];
export interface MushafSura { n: number; ayat: [ayah: number, words: MushafWord[]][] }

export type Mode = 'q' | 'r';
export interface ViewState { sura: number; mode: Mode; riw: string; sel: Set<string> }
