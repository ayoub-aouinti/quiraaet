import fs from 'node:fs';

const read = file => JSON.parse(fs.readFileSync(file, 'utf8'));
const exists = file => fs.existsSync(file);
const issues = [];
const meta = read('app/data/meta.json');

for (let n = 1; n <= 114; n += 1) {
  const qFile = `app/data/qalun/${n}.json`;
  const readsFile = `app/data/reads/${n}.json`;
  for (const file of [qFile, readsFile, `app/data/khilaf/${n}.json`, `app/data/usul/${n}.json`]) {
    if (!exists(file)) issues.push(`fichier manquant: ${file}`);
  }
  if (!exists(qFile) || !exists(readsFile)) continue;

  const q = read(qFile);
  const reads = read(readsFile);
  const words = q.ayat.flatMap(([, ayah]) => ayah);
  const seqs = words.map(([seq]) => seq);
  const seqSet = new Set(seqs);
  if (seqSet.size !== seqs.length) issues.push(`séquences Qaloun dupliquées: sourate ${n}`);
  if (q.ayat.length !== meta.suras[n - 1]?.ayat) {
    issues.push(`nombre d'ayat incohérent: sourate ${n} (${q.ayat.length})`);
  }
  for (const entry of reads) {
    if (!Number.isInteger(entry.s) || !Number.isInteger(entry.e) || entry.s > entry.e) {
      issues.push(`intervalle invalide: sourate ${n}`);
      continue;
    }
    if (!seqSet.has(entry.s) || !seqSet.has(entry.e)) {
      issues.push(`intervalle hors texte: sourate ${n} (${entry.s}-${entry.e})`);
    }
    for (const reader of entry.r ?? []) {
      for (const key of ['dq', 'dx']) {
        if ((reader[key] ?? []).some(i => !Number.isInteger(i) || i < 0)) {
          issues.push(`${key} invalide: sourate ${n}, lecteur ${reader.id}`);
        }
      }
    }
  }
}

for (const riwaya of meta.riwayat) {
  if (!riwaya.mush) continue;
  for (let n = 1; n <= 114; n += 1) {
    const file = `app/data/riw/${riwaya.mush}/${n}.json`;
    if (!exists(file)) issues.push(`mushaf manquant: ${file}`);
  }
}

if (issues.length) {
  console.error(`Validation échouée (${issues.length} anomalie(s))`);
  console.error(issues.join('\n'));
  process.exitCode = 1;
} else {
  console.log('Validation réussie: 114 sourates, données Qaloun/lectures/riwāyāt cohérentes.');
}
