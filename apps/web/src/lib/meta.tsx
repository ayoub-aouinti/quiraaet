import { createContext, useContext, useMemo, type ReactNode } from 'react';
import type { Category, Riwaya, Source, Sura } from '@jamei/shared';
import { api } from './api';
import { useAsync } from './useAsync';

/** ما يُحمَّل مرّةً ويُحتاج في كلِّ صفحة: الفئاتُ والمصادرُ والسورُ والروايات. */
export interface Meta {
  categories: Record<string, Category>;
  categoryList: Category[];
  sources: Source[];
  sourceById: Record<string, Source>;
  suras: Sura[];
  riwayat: Riwaya[];
  reloadSources: () => void;
}

const Ctx = createContext<Meta | null>(null);

export function MetaProvider({ children }: { children: ReactNode }) {
  const cats = useAsync(() => api.categories(), []);
  const srcs = useAsync(() => api.sources(), []);
  const suras = useAsync(() => api.suras(), []);
  const riw = useAsync(() => api.riwayat(), []);

  const value = useMemo<Meta | null>(() => {
    if (!cats.data || !srcs.data || !suras.data || !riw.data) return null;
    return {
      categories: Object.fromEntries(cats.data.map((c) => [c.id, c])),
      categoryList: cats.data,
      sources: srcs.data,
      sourceById: Object.fromEntries(srcs.data.map((s) => [s.id, s])),
      suras: suras.data,
      riwayat: riw.data,
      reloadSources: srcs.reload,
    };
  }, [cats.data, srcs.data, suras.data, riw.data, srcs.reload]);

  const error = cats.error ?? srcs.error ?? suras.error ?? riw.error;
  if (error) {
    return (
      <div className="boot">
        <p className="boot-title">تعذَّر الاتصالُ بالواجهة البرمجية</p>
        <p className="muted">{error.message}</p>
        <p className="muted small">تحقَّق أنّ الخادم يعمل (npm run api) وأنّ DATABASE_URL صحيح.</p>
        <button
          type="button"
          className="btn primary"
          onClick={() => {
            cats.reload();
            srcs.reload();
            suras.reload();
            riw.reload();
          }}
        >
          أعِد المحاولة
        </button>
      </div>
    );
  }
  if (!value) return <div className="boot muted">يُحمَّل الجامع…</div>;
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useMeta(): Meta {
  const m = useContext(Ctx);
  if (!m) throw new Error('useMeta خارج MetaProvider');
  return m;
}
