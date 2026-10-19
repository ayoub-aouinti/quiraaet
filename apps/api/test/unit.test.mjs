// اختباراتُ المنطق الخالص في الواجهة البرمجية. تعمل على dist بعد البناء:
//   npm run build -w @jamei/api && npm test -w @jamei/api
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { pageBackward, pageForward, PAGE_WORDS } from '../dist/mushaf/pagination.js';
import { sourceState } from '../dist/catalog/catalog.service.js';
import { normalizeArabic } from '../dist/common/arabic.js';

const sizes = (ns) => ns.map((n, i) => ({ ayah: i + 1, n }));

test('الصفحةُ تقف قبل أن تتجاوز حدَّ الكلمات', () => {
  const s = sizes([50, 50, 40, 30, 10]);
  assert.deepEqual(pageForward(s, 1), { from: 1, to: 3 });
  assert.deepEqual(pageForward(s, 4), { from: 4, to: 5 });
});

test('الآيةُ الطويلةُ وحدها صفحةٌ ولا تُقطَع', () => {
  const s = sizes([PAGE_WORDS + 40, 5]);
  assert.deepEqual(pageForward(s, 1), { from: 1, to: 1 });
});

test('الصفحةُ السابقةُ تنتهي قبل الحالية مباشرة', () => {
  const s = sizes([50, 50, 40, 30, 10]);
  assert.deepEqual(pageBackward(s, 4), { from: 1, to: 3 });
  assert.deepEqual(pageBackward(s, 2), { from: 1, to: 1 });
});

test('حالُ المصدر: المقترَحُ كلُّه لا يُسمّى مستورَداً', () => {
  assert.equal(sourceState(0, 0, 0, 0), 'pending');
  assert.equal(sourceState(10, 0, 10, 0), 'proposed');
  assert.equal(sourceState(10, 10, 0, 0), 'imported');
  assert.equal(sourceState(10, 0, 0, 10), 'verified');
  assert.equal(sourceState(10, 9, 1, 0), 'mixed');
});

test('التطبيعُ للبحث يُسقِط الضبطَ ويوحِّد الألف', () => {
  assert.equal(normalizeArabic('ٱلۡحَمۡدُ'), 'الحمد');
  assert.equal(normalizeArabic('  إِلَىٰ   '), 'الي');
});
