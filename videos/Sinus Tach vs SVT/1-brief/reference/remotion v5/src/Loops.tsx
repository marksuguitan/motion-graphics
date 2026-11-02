import React from 'react';
import {HeartLayer, HeartState, AV, ACC, VENT_MAX} from './Heart';
import {T} from './theme';
import {clamp} from './ui';

// ---- path sampling (absolute M/L/C/Z only) ----
type P = {x: number; y: number};
function samplePath(d: string, n = 1200) {
  const tok = d.match(/[MLCZ]|-?\d*\.?\d+(?:e-?\d+)?/gi)!;
  const segs: P[][] = []; let cur: P = {x: 0, y: 0}, start: P = {x: 0, y: 0}, i = 0, cmd = '';
  const num = () => parseFloat(tok[i++]);
  while (i < tok.length) {
    if (/[MLCZ]/i.test(tok[i])) cmd = tok[i++].toUpperCase();
    if (cmd === 'M') { cur = {x: num(), y: num()}; start = cur; cmd = 'L'; continue; }
    if (cmd === 'L') { const p = {x: num(), y: num()}; segs.push([cur, p]); cur = p; continue; }
    if (cmd === 'C') { const a = {x: num(), y: num()}, b = {x: num(), y: num()}, p = {x: num(), y: num()}; segs.push([cur, a, b, p]); cur = p; continue; }
    if (cmd === 'Z') { segs.push([cur, start]); cur = start; }
  }
  const pts: P[] = [];
  for (const s of segs) for (let k = 0; k < 60; k++) {
    const u = k / 60;
    if (s.length === 2) pts.push({x: s[0].x + (s[1].x - s[0].x) * u, y: s[0].y + (s[1].y - s[0].y) * u});
    else { const m = 1 - u; pts.push({x: m * m * m * s[0].x + 3 * m * m * u * s[1].x + 3 * m * u * u * s[2].x + u * u * u * s[3].x, y: m * m * m * s[0].y + 3 * m * m * u * s[1].y + 3 * m * u * u * s[2].y + u * u * u * s[3].y}); }
  }
  pts.push(cur);
  const L = [0]; for (let k = 1; k < pts.length; k++) L.push(L[k - 1] + Math.hypot(pts[k].x - pts[k - 1].x, pts[k].y - pts[k - 1].y));
  const total = L[L.length - 1];
  const at = (f: number): P => { const s = (((f % 1) + 1) % 1) * total; let lo = 0, hi = L.length - 1; while (hi - lo > 1) { const m = (lo + hi) >> 1; if (L[m] < s) lo = m; else hi = m; } const k = (s - L[lo]) / (L[hi] - L[lo] || 1); return {x: pts[lo].x + (pts[hi].x - pts[lo].x) * k, y: pts[lo].y + (pts[hi].y - pts[lo].y) * k}; };
  const nearest = (q: P) => { let best = 0, bd = 1e18; for (let k = 0; k < pts.length; k++) { const dd = (pts[k].x - q.x) ** 2 + (pts[k].y - q.y) ** 2; if (dd < bd) { bd = dd; best = k; } } return L[best] / total; };
  return {at, total, nearest};
}

// AVNRT: small circuit around the AV node (starts at the top, runs clockwise; bottom = phase 0.5)
const RX = 330, RY = 250;
export const AVNRT_D = `M${AV.x} ${AV.y - RY}a${RX} ${RY} 0 1 1 -0.1 0`;
const avnrtAt = (f: number): P => { const a = 2 * Math.PI * f; return {x: AV.x + RX * Math.sin(a), y: AV.y - RY * Math.cos(a)}; };
// orthodromic AVRT: left atrium -> AV node -> His / left bundle -> apex -> lateral Purkinje -> accessory pathway -> left atrium
// the ventricular leg is traced along the centre of Mark's conduction art so the circuit never leaves the His-Purkinje system
export const AVRT_D = `M4300 3050 C3800 3150 3450 3250 3320 3400 L3352 3396 L3384 3385 L3416 3376 L3448 3372 L3480 3370 L3512 3374 L3544 3379 L3576 3380 L3608 3381 L3640 3384 L3672 3386 L3704 3391 L3736 3397 L3768 3405 L3800 3415 L3832 3429 L3864 3445 L3892 3463 L3920 3485 L3944 3508 L3968 3532 L3991 3556 L4014 3584 L4033 3612 L4050 3640 L4066 3672 L4081 3704 L4092 3736 L4103 3768 L4115 3800 L4124 3832 L4138 3864 L4157 3891 L4184 3913 L4212 3929 L4242 3951 L4265 3976 L4288 4004 L4312 4032 L4334 4060 L4355 4088 L4374 4116 L4393 4144 L4411 4172 L4428 4200 L4444 4228 L4461 4256 L4478 4288 L4494 4316 L4512 4348 L4529 4380 L4545 4412 L4560 4444 L4574 4476 L4588 4508 L4602 4540 L4615 4572 L4629 4604 L4642 4636 L4655 4668 L4668 4700 L4681 4732 L4693 4764 L4705 4796 L4717 4828 L4729 4860 L4740 4892 L4752 4924 L4764 4956 L4775 4988 L4787 5020 L4800 5052 L4814 5084 L4828 5116 L4841 5148 L4857 5180 L4873 5212 L4889 5244 L4900 5276 L4905 5308 L4909 5340 L4915 5372 L4924 5404 L4936 5436 L4948 5468 L4960 5500 L4972 5532 L4984 5564 L4996 5596 L5008 5628 L5021 5660 L5033 5692 L5046 5724 L5058 5756 L5071 5788 L5083 5820 L5096 5852 L5109 5884 L5122 5916 L5135 5948 L5150 5980 L5165 6012 L5180 6044 L5195 6076 L5209 6108 L5225 6140 L5241 6172 L5258 6204 L5274 6232 L5290 6260 L5307 6288 L5324 6316 L5342 6344 L5360 6372 L5380 6400 L5401 6428 L5423 6456 L5447 6484 L5469 6508 L5492 6531 L5520 6555 L5548 6576 L5576 6595 L5604 6612 L5636 6628 L5668 6641 L5700 6649 L5732 6652 L5764 6650 L5796 6644 L5828 6635 L5860 6623 L5892 6605 L5920 6585 L5944 6564 L5967 6540 L5991 6512 L6012 6484 L6030 6456 L6047 6428 L6064 6396 L6078 6364 L6089 6332 L6099 6300 L6107 6268 L6122 6237 L6144 6212 L6165 6184 L6175 6152 L6182 6120 L6190 6088 L6198 6056 L6207 6024 L6214 5992 L6222 5960 L6229 5928 L6236 5896 L6242 5864 L6248 5832 L6254 5800 L6260 5768 L6265 5736 L6269 5704 L6271 5672 L6273 5640 L6276 5608 L6282 5576 L6295 5544 L6306 5512 L6308 5480 L6308 5448 L6311 5416 L6314 5384 L6318 5352 L6321 5320 L6324 5288 L6327 5256 L6328 5224 L6330 5192 L6333 5160 L6335 5128 L6336 5096 L6336 5064 L6336 5032 L6335 5000 L6335 4968 L6339 4936 L6346 4904 L6350 4872 L6352 4840 L6352 4808 L6352 4776 L6354 4744 L6357 4712 L6358 4680 L6356 4648 L6354 4616 L6353 4584 L6352 4552 L6352 4520 L6352 4488 L6352 4456 L6350 4424 L6348 4392 L6348 4360 L6345 4328 L6342 4296 L6339 4264 L6336 4232 L6330 4200 L6329 4168 L6331 4136 L6331 4104 L6328 4072 L6324 4040 L6321 4008 L6317 3976 L6313 3944 L6308 3912 L6304 3880 L6300 3848 L6300 3820 L6295 3770 L6200 3440 L6010 3110 C5700 2850 4800 2950 4300 3050Z`; // AV node -> His -> left bundle -> lateral Purkinje trunk (geodesic centreline of the conduction art) -> accessory pathway -> LA
export const AVRT = samplePath(AVRT_D);
export const AVRT_AV = AVRT.nearest(AV);                  // phase at the AV node
export const AVRT_ACC = AVRT.nearest({x: 6200, y: 3440}); // phase at the accessory pathway

export type LoopProps = {uid: string; kind: 'avnrt' | 'avrt'; w: number; h: number; draw: number; phase: number | null; block?: boolean; heart: HeartState; accGlow?: number; view?: number; center?: {x: number; y: number}};

// Zoomed card on Mark's heart with the re-entry circuit drawn on top.
export const LoopCard: React.FC<LoopProps> = ({uid, kind, w, h, draw, phase, block, heart, accGlow = 0, view: vw, center}) => {
  const view = vw ?? (kind === 'avrt' ? 6600 : 4200), S = w / view;
  const cx = center?.x ?? (kind === 'avrt' ? 4500 : 4200), cy = center?.y ?? (kind === 'avrt' ? 4500 : 3900);
  const tx = w / 2 - cx * S, ty = h / 2 - cy * S;
  const d = kind === 'avrt' ? AVRT_D : AVNRT_D;
  const at = kind === 'avrt' ? AVRT.at : avnrtAt;
  const px = (v: number) => v / S;               // stage px -> heart units
  const col = block ? T.ink3 : T.coral;
  const trail = phase === null || block ? [] : [0, 1, 2, 3, 4, 5, 6].map(k => ({p: at(phase - k * (kind === 'avrt' ? 0.012 : 0.03)), k}));
  const overlay = (
    <g>
      {kind === 'avrt' && (
        <g>
          <path d={ACC} fill="none" stroke={T.teal} strokeWidth={90} strokeLinecap="round" strokeLinejoin="round" />
          {accGlow > 0 && <path d={ACC} fill="none" stroke="#64CAE0" strokeWidth={150} strokeLinecap="round" strokeLinejoin="round" opacity={0.45 * accGlow} />}
          <path d={ACC} fill="none" stroke={T.card} strokeWidth={px(6)} strokeLinecap="round" strokeDasharray={`${px(2)} ${px(10)}`} />
        </g>
      )}
      {draw > 0 && <path d={d} pathLength={1} fill="none" stroke={col} strokeWidth={px(5)} strokeLinecap="round" strokeDasharray={block ? `${0.012} ${0.016}` : `${draw} 2`} />}
      {trail.reverse().map(({p, k}) => <circle key={k} cx={p.x} cy={p.y} r={px(k === 0 ? 12 : 10 - k)} fill={T.amber} opacity={k === 0 ? 1 : 0.5 - k * 0.06} stroke={k === 0 ? T.card : 'none'} strokeWidth={px(3)} />)}
      {block && (
        <g transform={`translate(${AV.x} ${AV.y}) scale(${1 / S})`}>
          <rect x={-58} y={-14} width={116} height={28} rx={8} fill={T.ink} />
          <text x={0} y={7} textAnchor="middle" fontFamily={T.font} fontSize={17} fontWeight={700} fill={T.bg}>BLOCKED</text>
        </g>
      )}
    </g>
  );
  void uid;
  return (
    <div style={{position: 'relative', width: w, height: h, borderRadius: 24, overflow: 'hidden', background: T.card, boxShadow: `inset 0 0 0 1.5px ${T.line}`}}>
      <HeartLayer s={heart} bodyOpacity={0.95} transform={`translate(${tx}px, ${ty}px) scale(${S * 4})`} overlay={overlay} />
      <div style={{position: 'absolute', inset: 0, borderRadius: 24, boxShadow: `inset 0 0 0 1.5px ${T.line}`, pointerEvents: 'none'}} />
    </div>
  );
};

// Simplified AV-junction schematic: atria -> AV node ring (with circuit) -> His -> ventricles. One open channel.
export const Schematic: React.FC<{w: number; h: number; phase: number | null; flash: number; block?: boolean; draw?: number}> = ({w, h, phase, flash, block, draw = 1}) => {
  const cx = w / 2, nodeY = 170, r = 70, hisY = 300, tipY = h - 60, lr = r - 22;
  const channel = `M${cx} 40V${hisY}L${cx - 120} ${tipY}M${cx} ${hisY}L${cx + 120} ${tipY}`;
  const down = `M${cx} ${nodeY + lr}V${hisY}L${cx + 120} ${tipY}M${cx} ${hisY}L${cx - 120} ${tipY}`;
  const lab = (x: number, y: number, t: string, a: 'start' | 'end' | 'middle' = 'middle') => <text x={x} y={y} fontFamily={T.font} fontSize={22} fontWeight={500} fill={T.ink2} textAnchor={a}>{t}</text>;
  const pos = (f: number) => { const a = 2 * Math.PI * f; return {x: cx + lr * Math.sin(a), y: nodeY - lr * Math.cos(a)}; };
  const col = block ? T.ink3 : T.coral;
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{display: 'block'}}>
      <rect width={w} height={h} rx={24} fill={T.card} stroke={T.line} strokeWidth={1.5} />
      <circle cx={cx} cy={nodeY} r={r} fill={T.card} stroke={T.line} strokeWidth={12} />
      <path d={channel} fill="none" stroke={T.line} strokeWidth={34} strokeLinecap="round" strokeLinejoin="round" />
      <path d={channel} fill="none" stroke={T.card} strokeWidth={22} strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={cx} cy={nodeY} r={r - 6} fill={T.card} />
      {flash > 0 && !block && <path d={down} fill="none" stroke={T.amber} strokeWidth={8} strokeLinecap="round" strokeLinejoin="round" opacity={flash} />}
      <path d={`M${cx} ${nodeY - lr}a${lr} ${lr} 0 1 1 -0.1 0`} pathLength={1} fill="none" stroke={col} strokeWidth={6} strokeDasharray={block ? '0.03 0.04' : `${draw} 2`} />
      {phase !== null && !block && [0, 1, 2, 3, 4].reverse().map(k => { const p = pos(phase - k * 0.035); return <circle key={k} cx={p.x} cy={p.y} r={k ? 9 - k : 11} fill={T.amber} opacity={k ? 0.45 - k * 0.08 : 1} stroke={k ? 'none' : T.card} strokeWidth={3} />; })}
      {block && <g transform={`translate(${cx} ${nodeY})`}><rect x={-58} y={-14} width={116} height={28} rx={8} fill={T.ink} /><text x={0} y={7} textAnchor="middle" fontFamily={T.font} fontSize={17} fontWeight={700} fill={T.bg}>BLOCKED</text></g>}
      {lab(cx - r - 24, nodeY + 8, 'AV node', 'end')}{lab(cx - 30, 56, 'Atria', 'end')}{lab(cx + 36, hisY + 8, 'His bundle', 'start')}{lab(cx, tipY + 40, 'Ventricles')}
    </svg>
  );
};

// ventricular activation after a lap leaves the node at time tq (s): front sweeps, then fades
export function lapFlash(t: number, tq: number): HeartState {
  const d = t - tq;
  if (d < 0) return {atr: 0, vent: 0, lit: 0};
  return {atr: 0, vent: clamp(d / 0.12) * VENT_MAX, lit: 1 - clamp((d - 0.12) / 0.16), band: true};
}
export {clamp};
