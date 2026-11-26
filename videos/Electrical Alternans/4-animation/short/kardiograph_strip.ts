/*
 * kardiograph_strip.ts: the short's rhythm strip, from Kardiograph's own engine (repo medzcool/kardiograph).
 * Lead V5, sinus tachycardia at 120/min (the engine's "tachy" preset at 120, no RR variation, no noise).
 * The engine has no electrical alternans, so two recordings are made that differ only in QRS voltage (full, and
 * half: q, R and S amplitudes x 0.5) and joined beat by beat on the baseline between T and P: even beats full,
 * odd beats half, until the "steady" beat of src/data/timeline.json, after which every beat is full. Every complex
 * on the strip is the engine's own.
 *
 *   node --experimental-strip-types kardiograph_strip.ts [path to a kardiograph clone]
 * Writes src/data/strip.json: { hz, mv[], rPeakS, lead, mmPerS, mmPerMv }. Sample i is at i / hz seconds; the R
 * peak of beat k is at rPeakS + k * 0.5 s. The picture shifts it so beat k lands on the timeline's beat k.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const kg = resolve(process.argv[2] ?? join(here, "../../../../../kardiograph"));
const imp = (f: string) => import(pathToFileURL(join(kg, "src/core", f)).href);
const { synthesizeCalibrated } = await imp("calibrate.ts");
const { PRESETS, applyPreset } = await imp("presets.ts");
const tl = JSON.parse(readFileSync(join(here, "src/data/timeline.json"), "utf8"));

const LEAD = "V5", SHORT = 0.5;
const bpm = 60 / tl.beat;
const base = { ...applyPreset(PRESETS.find((p: any) => p.id === "tachy")), heartRateBpm: bpm, rrSdMs: 0, durationS: Math.ceil(tl.end + 2) };
const low = { ...base, qAmpMv: base.qAmpMv * SHORT, rAmpMv: base.rAmpMv * SHORT, sAmpMv: base.sAmpMv * SHORT };
const A = synthesizeCalibrated(base, 1).signal, Bs = synthesizeCalibrated(low, 1).signal;
const fs: number = A.sampleRateHz;
const a: Float32Array = A.leads[LEAD], b: Float32Array = Bs.leads[LEAD];
const on: number[] = A.beatOnsets;
const rr = Math.round(tl.beat * fs);
if (on[1]! - on[0]! !== rr || Bs.beatOnsets[0] !== on[0]) throw new Error("the two recordings are not beat for beat in step");
// R peak of beat 0
let iR = on[0]!;
for (let i = on[0]!; i < on[0]! + rr / 2; i++) if (a[i]! > a[iR]!) iR = i;
// each beat owns the samples from 0.22 s before its R peak to 0.28 s after it (the join falls between T and P)
const mv: number[] = [];
let worstJoin = 0;
for (let i = 0; i < a.length; i++) {
  const k = Math.floor((i - iR + Math.round(0.22 * fs)) / rr);
  const tall = k < 0 || k >= tl.k.steady || k % 2 === 0;
  mv.push(+(tall ? a[i]! : b[i]!).toFixed(4));
  if ((i - iR + Math.round(0.22 * fs)) % rr === 0) worstJoin = Math.max(worstJoin, Math.abs(a[i]! - b[i]!));
}
const out = {
  note: `Lead ${LEAD} from Kardiograph's engine: sinus tachycardia ${bpm}/min; odd beats have half the QRS voltage until beat ${tl.k.steady}. Made by kardiograph_strip.ts.`,
  lead: LEAD, hz: fs, mmPerS: 25, mmPerMv: 10, rPeakS: iR / fs, mv,
};
writeFileSync(join(here, "src/data/strip.json"), JSON.stringify(out));
const pk = (k: number) => Math.max(...mv.slice(iR + k * rr - 20, iR + k * rr + 20)).toFixed(2);
console.log(`${LEAD} ${bpm}/min, ${fs} Hz, ${mv.length / fs} s; R peak of beat 0 at ${(iR / fs).toFixed(3)} s; R ${pk(0)} / ${pk(1)} mV, beat ${tl.k.steady}: ${pk(tl.k.steady)} mV; largest step at a join ${worstJoin.toFixed(4)} mV`);
