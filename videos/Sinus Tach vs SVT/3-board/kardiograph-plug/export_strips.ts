/*
 * Exports lead II strips from Kardiograph's own engine (repo medzcool/kardiograph) for the plug frames.
 * Run from the kardiograph clone:
 *   node --experimental-strip-types --import ./tests/md-hooks.mjs "<this file>"
 * Writes strips.json beside this file: { name: { fs, mv[], label } } at 250 Hz, 10 s each.
 */
import { writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { DECKS, makeCase } from "../../../../../kardiograph/src/practice/cases.ts";
import { synthesizeCalibrated } from "../../../../../kardiograph/src/core/calibrate.ts";
import { DEFAULT_PARAMS } from "../../../../../kardiograph/src/core/params.ts";

const here = dirname(fileURLToPath(import.meta.url));
const down = (sig: any) => {
  const fs = sig.sampleRateHz as number;
  const lead = sig.leads.II as ArrayLike<number>;
  const step = Math.round(fs / 250);
  const mv: number[] = [];
  for (let i = 0; i < lead.length; i += step) mv.push(+lead[i]!.toFixed(3));
  return { fs: fs / step, mv };
};
const out: Record<string, unknown> = {};
const sinus = synthesizeCalibrated({ ...DEFAULT_PARAMS }, 1);
out.sinus = { ...down(sinus.signal), label: "Normal sinus rhythm", hr: sinus.measurements.heartRateBpm };

const deck = DECKS.find((d) => d.id === "rhythm")!;
const want = new Set(["svt", "afib", "flutter", "avb1", "mobitz1"]);
for (let s = 1; s < 3000 && want.size; s++) {
  const c = makeCase(deck, s);
  const m: any = c.result.measurements;
  if (!want.has(c.base) || c.overlay || !c.validated) continue;
  if (c.base === "svt" && !(m.heartRateBpm >= 165 && m.heartRateBpm <= 185 && (m.qrsMs ?? 200) <= 100)) continue;
  want.delete(c.base);
  out[c.base] = { ...down(c.result.signal), label: c.base, seed: s, hr: m.heartRateBpm, qrs: m.qrsMs };
}
writeFileSync(join(here, "strips.json"), JSON.stringify(out));
console.log(Object.entries(out).map(([k, v]: any) => `${k} seed=${v.seed ?? "-"} hr=${Math.round(v.hr)}`).join("\n"));
