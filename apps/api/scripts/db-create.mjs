#!/usr/bin/env node
// يُنشئ القاعدةَ المسمّاة في DATABASE_URL إن لم تكن موجودة، ولا يمسّ غيرَها.
//   npm run db:create
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
const name = decodeURIComponent(new URL(url).pathname.replace(/^\//, ''));
if (!/^[A-Za-z_][A-Za-z0-9_]{0,62}$/.test(name)) {
  console.error(`اسمُ القاعدة «${name}» غيرُ صالح هنا. استعمل حروفاً لاتينية وأرقاماً و_.`);
  process.exit(2);
}
const maint = new URL(url);
maint.pathname = '/postgres';
const c = new pg.Client({ connectionString: maint.toString() });
await c.connect();
try {
  const r = await c.query('SELECT 1 FROM pg_database WHERE datname = $1', [name]);
  if (r.rowCount) {
    console.log(`القاعدةُ «${name}» موجودةٌ من قبل، فلم يُنشأ شيء.`);
  } else {
    await c.query(`CREATE DATABASE "${name}" ENCODING 'UTF8' TEMPLATE template0`);
    console.log(`أُنشئت القاعدةُ «${name}».`);
  }
} finally {
  await c.end();
}
