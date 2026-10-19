// عميلُ الواجهة البرمجية، مشتركٌ بين الويب والجوال.
import type {
  AyatPage,
  Category,
  ReviewDecisionBody,
  ReviewQueue,
  Riwaya,
  Ruling,
  RulingCreateBody,
  RulingPatchBody,
  RiwayaText,
  SearchHit,
  Source,
  Stats,
  Sura,
  Term,
  TermPatch,
  WordDetail,
} from './types';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

export interface ClientOptions {
  /** أصلُ الواجهة البرمجية، مثل http://localhost:3000 — بلا /api. */
  baseUrl: string;
  /** رمزُ المراجِع، يُرسَل مع طلبات الكتابة وحدها. */
  getToken?: () => string | null | undefined;
}

type Query = Record<string, string | number | undefined | null>;

export function createClient(opts: ClientOptions) {
  const base = opts.baseUrl.replace(/\/+$/, '') + '/api';

  async function request<T>(method: string, path: string, query?: Query, body?: unknown): Promise<T> {
    const qs = query
      ? Object.entries(query)
          .filter(([, v]) => v !== undefined && v !== null && v !== '')
          .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`)
          .join('&')
      : '';
    const headers: Record<string, string> = { Accept: 'application/json' };
    if (body !== undefined) headers['Content-Type'] = 'application/json';
    if (method !== 'GET') {
      const token = opts.getToken?.();
      if (token) headers.Authorization = `Bearer ${token}`;
    }
    const res = await fetch(base + path + (qs ? `?${qs}` : ''), {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    if (!res.ok) {
      let msg = res.statusText;
      try {
        const j = (await res.json()) as { message?: string | string[] };
        if (j.message) msg = Array.isArray(j.message) ? j.message.join('، ') : j.message;
      } catch {
        /* الجسمُ ليس JSON */
      }
      throw new ApiError(res.status, msg);
    }
    return (await res.json()) as T;
  }

  return {
    categories: () => request<Category[]>('GET', '/categories'),
    sources: () => request<Source[]>('GET', '/sources'),
    suras: () => request<Sura[]>('GET', '/suras'),
    riwayat: () => request<Riwaya[]>('GET', '/riwayat'),
    stats: () => request<Stats>('GET', '/stats'),
    ayat: (sura: number, from?: number, to?: number) =>
      request<AyatPage>('GET', `/suras/${sura}/ayat`, { from, to }),
    word: (seq: number) => request<WordDetail>('GET', `/words/${seq}`),
    riwayaText: (riwaya: string, sura: number, from: number, to: number) =>
      request<RiwayaText>('GET', `/riwayat/${encodeURIComponent(riwaya)}/text`, { sura, from, to }),
    search: (q: string, limit = 50) => request<SearchHit[]>('GET', '/search', { q, limit }),
    terms: (source?: string) => request<Term[]>('GET', '/terms', { source }),
    patchTerm: (source: string, symbol: string, patch: TermPatch) =>
      request<Term>(
        'PATCH',
        `/terms/${encodeURIComponent(source)}/${encodeURIComponent(symbol)}`,
        undefined,
        patch,
      ),
    reviewQueue: (source?: string, limit = 20, after?: string) =>
      request<ReviewQueue>('GET', '/review/queue', { source, limit, after }),
    decide: (seq: number, source: string, body: ReviewDecisionBody) =>
      request<{ ok: true }>('POST', `/review/${seq}/${encodeURIComponent(source)}`, undefined, body),
    patchRuling: (seq: number, source: string, body: RulingPatchBody) =>
      request<Ruling>('PATCH', `/rulings/${seq}/${encodeURIComponent(source)}`, undefined, body),
    createRuling: (seq: number, body: RulingCreateBody) =>
      request<Ruling>('POST', `/rulings/${seq}`, undefined, body),
    checkToken: () => request<{ ok: true; actor: string }>('POST', '/auth/check'),
  };
}

export type JameiClient = ReturnType<typeof createClient>;
