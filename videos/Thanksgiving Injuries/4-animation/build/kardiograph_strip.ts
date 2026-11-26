/*
 * kardiograph_strip.ts: the holiday-heart rhythm strip, from Kardiograph's own engine (repo medzcool/kardiograph).
 * Lead II: atrial fibrillation (the engine's "afib" preset: irregularly irregular RR about 110/min, no P waves,
 * fibrillatory baseline), then conversion to sinus rhythm after a short pause. The two recordings are joined on
 * the baseline after a T wave, so every complex on the strip is the engine's own.
 *
 * Run after timeline.py (it reads ev.s6 from timeline.json), with the kardiograph clone beside motion-graphics:
 *   node --experimental-strip-types kardiograph_strip.ts [path to kardiograph]
 * Writes ../remotion/src/data/strip.json: { hz, mv[], qrs[{t, kind}], splice, mmPerS, mmPerMv }, t in seconds
 * from the moment the write head starts (ev.s6.write).
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const kg = resolve(process.argv[2] ?? join(here, "../../../../../kardiograph"));
const imp = (f: string) => import(pathToFileURL(join(kg, "src/core", f)).href);
const { synthesizeCalibrated } = await imp("calibrate.ts");
const { PRESETS, applyPreset } = await imp("presets.ts");

const tl = JSON.parse(readFileSync(join(here, "../remotion/src/data/timeline.json"), "utf8"));
const s6 = tl.ev.s6;
const convert = s6.convert - s6.write; // where the last AF beat should have ended
const total = s6.stripEnd - s6.write;

const AF_SEED = 7, SINUS_SEED = 3;
const afP = { ...applyPreset(PRESETS.find((p: any) => p.id === "afib")), durationS: Math.max(10, Math.ceil(convert + 4)) };
const snP = { ...applyPreset(PRESETS.find((p: any) => p.id === "normal")), heartRateBpm: 78, durationS: Math.max(10, Math.ceil(total - convert + 4)) };
const af = synthesizeCalibrated(afP, AF_SEED);
const sn = synthesizeCalibrated(snP, SINUS_SEED);
const fs: number = af.signal.sampleRateHz;
const afII: Float32Array = af.signal.leads.II, snII: Float32Array = sn.signal.leads.II;
const afQ: number[] = af.signal.beatOnsets.map((i: number) => i / fs);
const snQ: number[] = sn.signal.beatOnsets.map((i: number) => i / fs);

// last AF beat: the last one whose QT has finished by `convert`
const qt = afP.qtMs / 1000;
const lastAf = afQ.filter((q) => q + qt + 0.06 <= convert).pop()!;
const cut = lastAf + qt + 0.06; // on the baseline, just after its T wave
// sinus picks up 0.5 s before a P wave (a short pause as the sinus node recovers)
const k = snQ.findIndex((q) => q - snP.prMs / 1000 - 0.5 > 0.2);
const snFrom = snQ[k]! - snP.prMs / 1000 - 0.5;
const n = Math.round(total * fs);
const mv = new Array<number>(n);
const iCut = Math.round(cut * fs), fade = Math.round(0.04 * fs), ramp = Math.round(0.2 * fs);
for (let i = 0; i < n; i++) {
  const a = afII[i] ?? 0;
  const j = Math.round(snFrom * fs) + (i - iCut);
  const s = j >= 0 ? snII[j] ?? 0 : 0;
  const w = Math.max(0, Math.min(1, (i - iCut) / fade)); // 40 ms crossfade on the baseline
  mv[i] = +(((1 - w) * a + w * s) * Math.min(1, i / ramp)).toFixed(4);
}
const qrs = [
  ...afQ.filter((q) => q <= lastAf + 1e-6).map((t) => ({ t: +t.toFixed(3), kind: "af" })),
  ...snQ.slice(k).map((q) => q - snFrom + cut).filter((t) => t < total).map((t) => ({ t: +t.toFixed(3), kind: "sinus" })),
];
const out = {
  note: "Lead II from Kardiograph's engine (afib preset, then normal sinus at 78/min), joined on the baseline. Made by build/kardiograph_strip.ts.",
  hz: fs, mmPerS: 25, mmPerMv: 10, splice: +cut.toFixed(3), afSeed: AF_SEED, sinusSeed: SINUS_SEED,
  afRateBpm: Math.round(af.measurements.heartRateBpm), sinusRateBpm: Math.round(sn.measurements.heartRateBpm),
  qrs, mv,
};
writeFileSync(join(here, "../remotion/src/data/strip.json"), JSON.stringify(out));
const rr = qrs.slice(1).map((q, i) => +(q.t - qrs[i]!.t).toFixed(2));
console.log(`strip ${total.toFixed(2)} s at ${fs} Hz; AF ${out.afRateBpm}/min until ${cut.toFixed(2)} s, sinus ${out.sinusRateBpm}/min; RR ${rr.join(" ")}`);
console.log(`peak ${Math.max(...mv).toFixed(2)} mV, trough ${Math.min(...mv).toFixed(2)} mV`);
