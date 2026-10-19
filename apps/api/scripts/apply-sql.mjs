#!/usr/bin/env node
// يُطبِّق ملفَّ SQL على القاعدة المعرَّفة في DATABASE_URL (من apps/api/.env).
//   node apps/api/scripts/apply-sql.mjs db/app_schema.sql
import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import pg from 'pg';

const envFile = fileURLToPath(new URL('../.env', import.meta.url));
if (existsSync(envFile)) process.loadEnvFile(envFile);

const file = process.argv[2];
if (!file) {
  console.error('الاستعمال: apply-sql.mjs <ملف.sql>');
  process.exit(2);
}

const url = process.env.DATABASE_URL;
if (!url) {
  console.error('DATABASE_URL غيرُ معرَّف. انسخ apps/api/.env.example إلى apps/api/.env واملأه.');
  process.exit(2);
}
if (/\/\/USER:PASSWORD@/.test(url)) {
  console.error(
    [
      'DATABASE_URL في apps/api/.env ما زال مثالَ .env.example (USER:PASSWORD).',
      'ضع مستخدمَ Postgres وكلمةَ سرِّه واسمَ القاعدة، مثلاً:',
      '  DATABASE_URL=postgresql://postgres:كلمة_السر@localhost:5432/jamei',
      'وإن كان في كلمة السرّ @ أو # أو % أو / أو : فرمِّزها (@ ← %40، # ← %23، % ← %25).',
    ].join('\n'),
  );
  process.exit(2);
}

const client = new pg.Client({ connectionString: url });
try {
  await client.connect();
} catch (e) {
  const where = (() => {
    try {
      const u = new URL(url);
      return `${decodeURIComponent(u.username)}@${u.hostname}:${u.port || 5432}${u.pathname}`;
    } catch {
      return '(DATABASE_URL غيرُ مقروء)';
    }
  })();
  const hints = {
    '28P01': 'كلمةُ السرّ أو اسمُ المستخدم خطأ. وإن كان في كلمة السرّ رموزٌ خاصّة فرمِّزها في الرابط.',
    '3D000': 'القاعدةُ غيرُ موجودة. أنشئها أوّلاً (createdb jamei) ثم انقل إليها بـ db/migrate.py.',
    ECONNREFUSED: 'لا خادمَ Postgres على هذا العنوان والمنفذ. تحقَّق أنّ الخدمة تعمل.',
  };
  console.error(`تعذَّر الاتصالُ بـ ${where}`);
  console.error(hints[e.code] ?? e.message);
  process.exit(1);
}

try {
  await client.query(readFileSync(file, 'utf8'));
  console.log(`طُبِّق ${file}`);
} catch (e) {
  if (e.code === '42P01' || e.code === '3F000') {
    console.error('جداولُ المشروع غيرُ موجودة في هذه القاعدة. انقل البياناتِ أوّلاً بـ db/migrate.py.');
  } else {
    console.error(e.message);
  }
  process.exitCode = 1;
} finally {
  await client.end();
}
