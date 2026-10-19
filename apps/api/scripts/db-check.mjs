#!/usr/bin/env node
// فحصٌ للقراءة وحدها: يتّصل بالخادم المعرَّف في DATABASE_URL (apps/api/.env)،
// ويسرد قواعدَه، ويذكر أيُّها فيه جداولُ الجامع وكم فيها من حكم.
//   npm run db:check
import { existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import pg from 'pg';

const envFile = fileURLToPath(new URL('../.env', import.meta.url));
if (existsSync(envFile)) process.loadEnvFile(envFile);
const url = process.env.DATABASE_URL;
if (!url) {
  console.error('DATABASE_URL غيرُ معرَّف في apps/api/.env.');
  process.exit(2);
}

const target = new URL(url);
const wanted = decodeURIComponent(target.pathname.replace(/^\//, '')) || '(بلا اسم)';
const maint = new URL(url);
maint.pathname = '/postgres';

const c = new pg.Client({ connectionString: maint.toString() });
try {
  await c.connect();
} catch (e) {
  console.error(`تعذَّر الاتصالُ بالخادم ${target.hostname}:${target.port || 5432}: ${e.message}`);
  process.exit(1);
}
const { rows } = await c.query(
  `SELECT datname FROM pg_database WHERE datallowconn AND NOT datistemplate ORDER BY datname`,
);
await c.end();

console.log(`الخادم: ${target.hostname}:${target.port || 5432} · المستخدم: ${decodeURIComponent(target.username)}`);
console.log(`القاعدةُ المطلوبة في DATABASE_URL: ${wanted}\n`);
for (const { datname } of rows) {
  const u = new URL(url);
  u.pathname = '/' + encodeURIComponent(datname);
  const d = new pg.Client({ connectionString: u.toString() });
  let info = '';
  try {
    await d.connect();
    const t = await d.query(`SELECT to_regclass('public.rulings') IS NOT NULL AS r,
                                    to_regclass('public.review_log') IS NOT NULL AS l`);
    if (t.rows[0].r) {
      const n = await d.query('SELECT count(*)::int AS n FROM rulings');
      info = `فيها جداولُ الجامع · ${n.rows[0].n} حكماً${t.rows[0].l ? ' · وسجلُّ المراجعة' : ' · بلا سجلِّ المراجعة'}`;
    } else {
      info = 'لا جداولَ للجامع فيها';
    }
  } catch (e) {
    info = `تعذَّر فتحُها: ${e.message}`;
  } finally {
    await d.end().catch(() => {});
  }
  console.log(`${datname === wanted ? '→' : ' '} ${datname} — ${info}`);
}
if (!rows.some((r) => r.datname === wanted)) {
  console.log(`\nلا قاعدةَ باسم «${wanted}» على هذا الخادم.`);
}
