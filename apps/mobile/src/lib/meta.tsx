import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import { ActivityIndicator, Pressable, Text, View } from 'react-native';
import type { Category, Riwaya, Source, Sura } from '@jamei/shared';
import { API_BASE, api } from './api';
import { useAsync } from './useAsync';
import { styles } from '../theme';

export interface Meta {
  categories: Record<string, Category>;
  categoryList: Category[];
  sources: Source[];
  sourceById: Record<string, Source>;
  suras: Sura[];
  riwayat: Riwaya[];
  /** المصادرُ المُطفأة في هذه الجلسة. */
  hidden: Set<string>;
  toggleSource: (id: string) => void;
  setAllHidden: (hide: boolean) => void;
}

const Ctx = createContext<Meta | null>(null);

export function MetaProvider({ children }: { children: ReactNode }) {
  const cats = useAsync(() => api.categories(), []);
  const srcs = useAsync(() => api.sources(), []);
  const suras = useAsync(() => api.suras(), []);
  const riw = useAsync(() => api.riwayat(), []);
  const [hidden, setHidden] = useState<Set<string>>(new Set());

  const value = useMemo<Meta | null>(() => {
    if (!cats.data || !srcs.data || !suras.data || !riw.data) return null;
    return {
      categories: Object.fromEntries(cats.data.map((c) => [c.id, c])),
      categoryList: cats.data,
      sources: srcs.data,
      sourceById: Object.fromEntries(srcs.data.map((s) => [s.id, s])),
      suras: suras.data,
      riwayat: riw.data,
      hidden,
      toggleSource: (id) =>
        setHidden((h) => {
          const n = new Set(h);
          if (n.has(id)) n.delete(id);
          else n.add(id);
          return n;
        }),
      setAllHidden: (hide) => setHidden(hide ? new Set(srcs.data!.map((s) => s.id)) : new Set()),
    };
  }, [cats.data, srcs.data, suras.data, riw.data, hidden]);

  const error = cats.error ?? srcs.error ?? suras.error ?? riw.error;
  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.h2}>تعذَّر الاتصالُ بالخادم</Text>
        <Text style={[styles.muted, styles.centerText]}>{error.message}</Text>
        <Text style={[styles.small, styles.muted, styles.centerText]}>{API_BASE}</Text>
        <Pressable
          style={styles.btn}
          onPress={() => {
            cats.reload();
            srcs.reload();
            suras.reload();
            riw.reload();
          }}
        >
          <Text style={styles.btnText}>أعِد المحاولة</Text>
        </Pressable>
      </View>
    );
  }
  if (!value) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
        <Text style={styles.muted}>يُحمَّل الجامع…</Text>
      </View>
    );
  }
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useMeta(): Meta {
  const m = useContext(Ctx);
  if (!m) throw new Error('useMeta خارج MetaProvider');
  return m;
}
