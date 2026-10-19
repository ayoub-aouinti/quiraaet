import { useCallback, useState } from 'react';

/** حالٌ يُحفَظ في متصفِّح القارئ وحده (تفضيلاتُ العرض). يعمل وإن حُجب التخزين. */
export function useStored<T>(key: string, initial: T): [T, (v: T) => void] {
  const full = `jamei.${key}`;
  const [value, setValue] = useState<T>(() => {
    try {
      const raw = localStorage.getItem(full);
      return raw == null ? initial : (JSON.parse(raw) as T);
    } catch {
      return initial;
    }
  });
  const set = useCallback(
    (v: T) => {
      setValue(v);
      try {
        localStorage.setItem(full, JSON.stringify(v));
      } catch {
        /* التخزينُ محجوب */
      }
    },
    [full],
  );
  return [value, set];
}
