import Constants from 'expo-constants';
import { Platform } from 'react-native';
import { createClient } from '@jamei/shared';

/**
 * أصلُ الواجهة البرمجية. EXPO_PUBLIC_API_URL يُقدَّم إن عُرِّف. وإلّا ففي
 * التطوير يُؤخَذ عنوانُ الجهاز الذي يُشغِّل Metro، فيصل الهاتفُ إلى الخادم
 * على الشبكة نفسها دون ضبط.
 */
function apiBase(): string {
  const env = process.env.EXPO_PUBLIC_API_URL;
  if (env) return env;
  const host = Constants.expoConfig?.hostUri?.split(':')[0];
  if (host) return `http://${host}:3000`;
  return Platform.OS === 'android' ? 'http://10.0.2.2:3000' : 'http://localhost:3000';
}

export const API_BASE = apiBase();
export const api = createClient({ baseUrl: API_BASE });
