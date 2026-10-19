#!/usr/bin/env node
// التطوير: tsc يُترجِم عند كلِّ حفظ، وnode يُعيد التشغيل عند تغيُّر dist.
// بديلٌ عن «nest start --watch» لأنّ أدوات @nestjs/cli تطلب Node 22.
import { spawn } from 'node:child_process';
import { existsSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const tsc = createRequire(import.meta.url).resolve('typescript/bin/tsc');
const opts = { cwd: root, stdio: 'inherit' };

const build = spawn(process.execPath, [tsc, '-p', 'tsconfig.build.json', '--watch', '--preserveWatchOutput'], opts);

let server;
const start = () => {
  if (!existsSync(join(root, 'dist', 'main.js'))) return setTimeout(start, 500);
  server = spawn(process.execPath, ['--enable-source-maps', '--watch-path=dist', 'dist/main.js'], opts);
};
start();

const stop = () => {
  build.kill();
  server?.kill();
  process.exit(0);
};
process.on('SIGINT', stop);
process.on('SIGTERM', stop);
