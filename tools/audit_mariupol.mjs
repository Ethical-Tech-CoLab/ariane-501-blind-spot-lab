// Executes only the reviewed, immutable upstream sensitivity script; no live routing.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import vm from 'node:vm';

const revision = '47af9d5decd9502a1084cc5958c0ee5b0e175e05';
const url = `https://raw.githubusercontent.com/Ethical-Tech-CoLab/mariupol-evacuation-model/${revision}/docs/sensitivity.js`;
const sha256 = '5864d6fcb1ad814909361850e12af4338794da33e34fdb89b838fd5b03e205ce';
const response = await fetch(url, { signal: AbortSignal.timeout(30000) });
if (!response.ok) throw new Error(`Source retrieval failed: HTTP ${response.status}`);
const source = await response.text();
assert.equal(createHash('sha256').update(source).digest('hex'), sha256, 'Reviewed source changed');
const logs = [];
const extension = `
const auditVariants = [
  ['Published settings', base, 6],
  ['Intensity ceiling 4.8', {...base, bI:4.8}, 6],
  ['Deprivation ceiling 45', {...base, bD:45}, 6],
  ['Deprivation ceiling 90', {...base, bD:90}, 6],
  ['Exponent 2', base, 2],
  ['Exponent 4', base, 4],
  ['Intensity 4.8; deprivation 90; exponent 2', {...base,bI:4.8,bD:90}, 2],
];
JSON.stringify(auditVariants.map(([label,bounds,p]) => {
  const series = run(bounds,p);
  const crossings = Object.fromEntries([0.40,0.55,0.70].map(threshold => {
    const hit = series.find(row => row.sev >= threshold);
    return [threshold.toFixed(2), hit ? dayDate(hit.i).toISOString().slice(0,10) : null];
  }));
  const firstHigh = crossings['0.55'];
  const summary = summarise(label,bounds,p);
  return {label,bounds,p,crossings,
    daysFromFirstHighToApril30: firstHigh ? (Date.UTC(2022,3,30)-Date.parse(firstHigh))/86400000 : null,
    violenceDominantDays:summary.violDays, dominantCounts:summary.dom,
    meanSeverity:Number(summary.meanSev),
    march9Severity:Number(series[4].sev.toFixed(9)),
    march10Severity:Number(series[5].sev.toFixed(9)),
    highOrWorseDays:series.filter(row=>row.sev>=0.55).length};
}));
`;
const variants = JSON.parse(vm.runInNewContext(source + extension, {
  console: { log: (...items) => logs.push(items.join(' ')) },
}, { timeout: 5000 }));
assert.equal(variants[0].crossings['0.55'], '2022-03-10');
assert.equal(variants[0].crossings['0.70'], '2022-04-28');
assert.equal(variants[0].violenceDominantDays, 2);
assert.equal(variants[0].daysFromFirstHighToApril30, 51);
assert(variants[0].march9Severity < 0.55);
assert(variants[0].march10Severity >= 0.55);
assert.equal(variants.find(row => row.label === 'Exponent 2').crossings['0.55'], null);
assert.equal(variants.find(row => row.label === 'Exponent 2').crossings['0.70'], null);
const result = {
  reviewedRevision: revision, sourceUrl: url, sourceSha256: sha256,
  type: 'Deterministic reproduction of upstream retrospective scores, not evacuation advice',
  observationWindow: { start: '2022-03-05', end: '2022-05-20', days: 77 },
  variants, upstreamConsoleOutput: logs,
};
const output = fileURLToPath(new URL('../data/mariupol-audit.json', import.meta.url));
const json = `${JSON.stringify(result, null, 2)}\n`;
if (process.argv.includes('--check')) {
  assert.equal(await readFile(output, 'utf8'), json, 'Published audit does not reproduce');
  console.log('PASS: pinned Mariupol audit reproduces exactly.');
} else {
  await writeFile(output, json, 'utf8');
  console.table(variants.map(({ label, crossings, highOrWorseDays }) => ({
    label, high: crossings['0.55'], critical: crossings['0.70'], highOrWorseDays,
  })));
}
