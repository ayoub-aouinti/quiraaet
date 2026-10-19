import { createClient } from '@jamei/shared';

const TOKEN_KEY = 'jamei.reviewer';

/** رمزُ المراجِع في الجلسة وحدها؛ يزول بإغلاق النافذة. */
export const reviewerToken = {
  get(): string | null {
    try {
      return sessionStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set(v: string | null) {
    try {
      if (v) sessionStorage.setItem(TOKEN_KEY, v);
      else sessionStorage.removeItem(TOKEN_KEY);
    } catch {
      /* التخزينُ محجوب */
    }
  },
};

// فارغٌ = الأصلُ نفسُه (والوكيلُ في التطوير يُمرِّر /api).
export const api = createClient({
  baseUrl: import.meta.env.VITE_API_URL ?? '',
  getToken: reviewerToken.get,
});
