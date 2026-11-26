// Art.tsx: every drawn thing in the video, as one SVG layer (1920 x 1080), a pure function of time t (s).
// One "hero" shape carries the story: the plate becomes the knife blade, the pot, a small plate, the dish, the glass
// and the ECG baseline, then the plate again. All its forms are rr4() shapes, so each change is a smooth morph.
// Other objects grow in with snap and settle (6% overshoot) and leave by shrinking on the accelerate curve.
import React from 'react';
import {C, FONT} from '../style/theme';
import {Curve, ease, fadeSmall, gravity, keys, overshoot, progress, squash} from '../style/comma';
import {Corner, lerp, mixHex, rr4} from '../lib/geo';
import {CARD, EV, TL} from '../lib/tl';

const OUT = 0.25;
const ev = EV as any;
const ES = TL.endScreen.start;
const clamp01 = (x: number) => Math.max(0, Math.min(1, x));

// ---------- shapes ----------
type Sh = {cx: number; cy: number; w: number; h: number; tl: Corner; tr: Corner; br: Corner; bl: Corner; fill: string; stroke: string; sw: number};
const r4 = (r: number): Corner => [r, r];
const disc = (cx: number, cy: number, r: number, fill: string = C.bg, stroke: string = C.line, sw = 6): Sh =>
  ({cx, cy, w: 2 * r, h: 2 * r, tl: r4(r), tr: r4(r), br: r4(r), bl: r4(r), fill, stroke, sw});
const rr = (cx: number, cy: number, w: number, h: number, r: number) => rr4(cx, cy, w, h, r4(r), r4(r), r4(r), r4(r));
const pathOf = (s: Sh) => rr4(s.cx, s.cy, s.w, s.h, s.tl, s.tr, s.br, s.bl);
const mixC = (a: Corner, b: Corner, k: number): Corner => [lerp(a[0], b[0], k), lerp(a[1], b[1], k)];
const mixSh = (a: Sh, b: Sh, k: number): Sh => ({
  cx: lerp(a.cx, b.cx, k), cy: lerp(a.cy, b.cy, k), w: lerp(a.w, b.w, k), h: lerp(a.h, b.h, k),
  tl: mixC(a.tl, b.tl, k), tr: mixC(a.tr, b.tr, k), br: mixC(a.br, b.br, k), bl: mixC(a.bl, b.bl, k),
  fill: mixHex(a.fill, b.fill, k), stroke: mixHex(a.stroke, b.stroke, k), sw: lerp(a.sw, b.sw, k),
});

/** Grow in (snap 6% past, settle) at tIn; shrink out on the accelerate curve at tOut. */
const popK = (t: number, tIn: number, tOut = Infinity, dIn = 0.5, over = 0.06) => {
  if (t < tIn) return 0;
  if (t >= tOut) return 1 - progress(t, tOut, OUT, 'accel');
  return overshoot(t, tIn, dIn, 0, 1, over);
};
const Pop: React.FC<{t: number; tIn: number; tOut?: number; cx: number; cy: number; dIn?: number; over?: number; children: React.ReactNode}> =
  ({t, tIn, tOut = Infinity, cx, cy, dIn, over, children}) => {
    const k = popK(t, tIn, tOut, dIn, over);
    if (k <= 0.0005) return null;
    return <g transform={`translate(${cx} ${cy}) scale(${k}) translate(${-cx} ${-cy})`}>{children}</g>;
  };
const Label: React.FC<{x: number; y: number; children: React.ReactNode; anchor?: 'start' | 'middle'; size?: number; color?: string; weight?: number}> =
  ({x, y, children, anchor = 'start', size = 22, color = C.ink2, weight = 500}) => (
    <text x={x} y={y} textAnchor={anchor} fontFamily={FONT.body} fontSize={size} fontWeight={weight} fill={color}>{children}</text>
  );
const vis = (t: number, a: number, b = Infinity) => t >= a && t < b;

// ---------- the hero shape ----------
const P1 = disc(960, 420, 190);
const BLADE: Sh = {cx: 650, cy: 540, w: 440, h: 92, tl: r4(6), tr: r4(0.01), br: [200, 90], bl: r4(6), fill: C.steel, stroke: '#C9C5BE', sw: 4};
const CHOP = 46; // the blade drops this far onto the board
const BLADE_DOWN: Sh = {...BLADE, cy: BLADE.cy + CHOP};
const POT: Sh = {cx: 600, cy: 420, w: 380, h: 230, tl: r4(8), tr: r4(8), br: r4(70), bl: r4(70), fill: C.bg, stroke: C.ink, sw: 6};
const PLATE2 = disc(380, 830, 110);
const DISH: Sh = {cx: 600, cy: 640, w: 480, h: 120, tl: r4(16), tr: r4(16), br: [110, 90], bl: [110, 90], fill: C.board, stroke: C.line, sw: 5};
const GLASS: Sh = {cx: 600, cy: 470, w: 150, h: 220, tl: r4(4), tr: r4(4), br: r4(36), bl: r4(36), fill: C.bg, stroke: C.line, sw: 5};
const LINE: Sh = {cx: 580, cy: 560, w: 880, h: 6, tl: r4(3), tr: r4(3), br: r4(3), bl: r4(3), fill: C.signal, stroke: C.signal, sw: 0};
const P3 = disc(960, 410, 190);

const T_ECG_ON = ev.s6.line + 0.47; // the trace takes over from the hero baseline
const T_ECG_OFF = ev.s7.grow; // the hero baseline takes back over
const SEGS: {at: number; dur: number; curve: Curve; to: Sh}[] = [
  {at: ev.s2.move, dur: 0.75, curve: 'cross', to: BLADE},
  {at: ev.s2.chop - 0.2, dur: 0.2, curve: 'accel', to: BLADE_DOWN},
  {at: ev.s3.morph, dur: 0.6, curve: 'snap', to: POT},
  {at: ev.s4.clear, dur: 0.7, curve: 'cross', to: PLATE2},
  {at: ev.s5.dish, dur: 0.75, curve: 'cross', to: DISH},
  {at: ev.s6.glass, dur: 0.6, curve: 'snap', to: GLASS},
  {at: ev.s6.line, dur: 0.45, curve: 'snap', to: LINE},
  {at: ev.s7.grow, dur: 0.7, curve: 'cross', to: P3},
];
export function heroAt(t: number): Sh {
  let cur = P1;
  for (const s of SEGS) {
    if (t < s.at) break;
    const k = progress(t, s.at, s.dur, s.curve);
    cur = mixSh(cur, s.to, k);
    if (k < 1) return cur;
  }
  return cur;
}

// knife swing: raise 18 degrees (anticipation), then strike down on the accelerate curve, landing on the chop
const knifeRot = (t: number) =>
  t < ev.s2.swish ? 0 : t < ev.s2.chop - 0.2 ? ease(t, ev.s2.swish, ev.s2.chop - 0.2 - ev.s2.swish, 0, -18, 'anti') : ease(t, ev.s2.chop - 0.2, 0.2, -18, 0, 'accel');

const Hero: React.FC<{t: number}> = ({t}) => {
  if (t >= T_ECG_ON && t < T_ECG_OFF) return null;
  const h = heroAt(t);
  let xf = '';
  // scene 1: grow in, one gravity hop, land with a small squash (a plate, not anatomy)
  if (t < ev.s2.anti) {
    const k = t < ev.s1.grow ? 0 : overshoot(t, ev.s1.grow, 0.55, 0, 1, 0.06);
    const y = gravity(t, ev.s1.rise, 0, -44, 0.28, 0.1, 0.27);
    const {sx, sy} = squash(t, ev.s1.land, 'y', 0.08);
    xf = `translate(0 ${y}) translate(960 610) scale(${k * sx} ${k * sy}) translate(-960 -610)`;
  } else if (t < ev.s3.morph) {
    // anticipation: a small counter-move up and right before the move down-left
    const ax = t < ev.s2.move ? ease(t, ev.s2.anti, 0.2, 0, 22, 'anti') : ease(t, ev.s2.move, 0.75, 22, 0, 'cross');
    const ay = t < ev.s2.move ? ease(t, ev.s2.anti, 0.2, 0, -12, 'anti') : ease(t, ev.s2.move, 0.75, -12, 0, 'cross');
    xf = `translate(${ax} ${ay}) rotate(${knifeRot(t)} 345 ${h.cy})`;
  } else if (t >= ev.s7.grow) {
    const u = clamp01((t - ev.s7.grow) / 0.7);
    const hop = -150 * Math.sin(Math.PI * u);
    const {sx, sy} = squash(t, ev.s7.land, 'y', 0.08);
    const out = t >= ES ? 1 - progress(t, ES, OUT, 'accel') : 1;
    xf = `translate(0 ${hop}) translate(960 600) scale(${sx * out} ${sy * out}) translate(-960 -600)`;
    if (out <= 0.0005) return null;
  }
  // inner rim, only while the hero is a plate
  const rimK = t < ev.s2.move + OUT ? 1 - progress(t, ev.s2.move, OUT, 'accel')
    : t < ev.s5.clear ? (t >= ev.s4.clear ? popK(t, ev.s4.clear + 0.5, ev.s5.clear, 0.45) : 0)
    : t >= ev.s7.land - 0.05 ? popK(t, ev.s7.land - 0.05, Infinity, 0.45) : 0;
  return (
    <g transform={xf}>
      <path d={pathOf(h)} fill={h.fill} stroke={h.stroke} strokeWidth={h.sw} />
      {rimK > 0.001 ? <circle cx={h.cx} cy={h.cy} r={h.w * 0.36 * rimK} fill="none" stroke={C.divider} strokeWidth={4} /> : null}
    </g>
  );
};

// ---------- scene 2: knife ----------
const Knife: React.FC<{t: number; part: 'board' | 'handle'}> = ({t, part}) => {
  if (!vis(t, ev.s2.move, ev.s3.morph + OUT)) return null;
  const dy = heroAt(t).cy - BLADE.cy;
  const sx = t < ev.s3.morph ? (t < ev.s2.board - 0.05 ? 0 : progress(t, ev.s2.board - 0.05, 0.45, 'snap')) : 1 - progress(t, ev.s3.morph, OUT, 'accel');
  const chop = ev.s2.chop;
  const tick = t >= chop ? fadeSmall(t, chop, 0.08) * (1 - progress(t, chop + 0.3, 0.2, 'linear')) : 0;
  const tl = 8 + 14 * progress(t, chop, 0.3, 'snap');
  return (
    <g>
      {part === 'board' ? <Pop t={t} tIn={ev.s2.board} tOut={ev.s3.morph} cx={600} cy={660}>
        <g transform={`translate(600 632) scale(${squash(t, chop, 'y', 0.05).sx} ${squash(t, chop, 'y', 0.05).sy}) translate(-600 -632)`}>
          <path d={rr(600, 660, 760, 56, 22)} fill={C.board} />
          <path d={rr(600, 650, 700, 6, 3)} fill="#E0D2BE" />
        </g>
      </Pop> : null}
      {part === 'handle' && sx > 0.001 ? (
        <g transform={`rotate(${knifeRot(t)} 345 ${540 + dy}) translate(0 ${dy})`}>
          <g transform={`translate(430 540) scale(${sx} 1) translate(-430 -540)`}>
            <path d={rr(345, 540, 170, 64, 24)} fill={C.ink} />
            <circle cx={300} cy={540} r={6} fill="#5A5A5A" />
            <circle cx={360} cy={540} r={6} fill="#5A5A5A" />
            <path d={rr(434, 540, 16, 84, 6)} fill="#5A5A5A" />
          </g>
        </g>
      ) : null}
      {part === 'handle' && tick > 0.001 ? (
        <g stroke={C.ink2} strokeWidth={4} strokeLinecap="round" opacity={tick}>
          {[[-1, 0.0], [-1, 0.6], [1, 0.0], [1, 0.6]].map(([d, a], i) => {
            const x0 = d < 0 ? 412 : 700;
            const ang = (d < 0 ? Math.PI : 0) + (d < 0 ? a : -a);
            return <line key={i} x1={x0 + Math.cos(ang) * 6} y1={622 + Math.sin(ang) * 6 - a * 10} x2={x0 + Math.cos(ang) * tl} y2={622 + Math.sin(ang) * tl - a * 10} />;
          })}
        </g>
      ) : null}
    </g>
  );
};

// ---------- scene 3: hot oil, skin, water ----------
const SKIN_TOP = 690;
const BURN_X = 760;
const Oil: React.FC<{t: number}> = ({t}) => {
  if (!vis(t, ev.s3.morph, ev.s4.clear + OUT)) return null;
  const pot = heroAt(t);
  const k = t >= ev.s4.clear ? 1 - progress(t, ev.s4.clear, OUT, 'accel') : 1;
  const top = ease(t, ev.s3.morph + 0.38, 0.6, 540, 345);
  const bubbles = [[470, 0.0, 7], [540, 0.55, 9], [610, 0.2, 6], [680, 0.85, 8], [735, 0.4, 6], [505, 1.05, 5]];
  return (
    <g>
      <defs>
        <clipPath id="potClip"><path d={pathOf(pot)} /></clipPath>
      </defs>
      <g clipPath="url(#potClip)" opacity={k < 1 ? 1 : 1}>
        <g transform={`translate(600 540) scale(1 ${k}) translate(-600 -540)`}>
          <rect x={380} y={top} width={440} height={560 - top} fill={C.oil} />
          <line x1={380} x2={820} y1={top + 2} y2={top + 2} stroke={C.oilLine} strokeWidth={4} />
          {t >= ev.s3.bubbles
            ? bubbles.map(([x, ph, r], i) => {
                const per = 1.3;
                const u = ((t - ev.s3.bubbles + ph) % per) / per; // constant-rate rise (a running process)
                const y = lerp(530, top + 10, u);
                const g = Math.min(1, (t - ev.s3.bubbles) / 0.2);
                return <circle key={i} cx={x + Math.sin(u * 6 + i) * 4} cy={y} r={r * (0.6 + 0.4 * u) * g} fill="none" stroke={C.oilLine} strokeWidth={3} />;
              })
            : null}
        </g>
      </g>
      {/* outline again on top of the oil */}
      <path d={pathOf(pot)} fill="none" stroke={pot.stroke} strokeWidth={pot.sw} />
    </g>
  );
};

const PotParts: React.FC<{t: number}> = ({t}) => (
  <g>
    <Pop t={t} tIn={ev.s3.morph + 0.35} tOut={ev.s4.clear} cx={600} cy={305}>
      <path d={rr(600, 305, 424, 20, 10)} fill={C.ink} />
    </Pop>
    <Pop t={t} tIn={ev.s3.morph + 0.4} tOut={ev.s4.clear} cx={386} cy={345}>
      <path d={rr(386, 345, 48, 18, 9)} fill={C.ink} />
    </Pop>
    <Pop t={t} tIn={ev.s3.morph + 0.4} tOut={ev.s4.clear} cx={814} cy={345}>
      <path d={rr(814, 345, 48, 18, 9)} fill={C.ink} />
    </Pop>
  </g>
);

const Skin: React.FC<{t: number}> = ({t}) => {
  const {pop, drop, water} = ev.s3;
  // the burn: spreads deep (into deep dermis) after the drop lands; cooling under running water pulls it back
  let burn: React.ReactNode = null;
  if (t >= drop) {
    const k1 = progress(t, drop, 0.7, 'snap');
    let w = lerp(26, 190, k1);
    let d = lerp(8, 106, k1);
    const k2 = progress(t, water + 0.6, 1.1, 'snap');
    w = lerp(w, 168, k2);
    d = lerp(d, 58, k2);
    const fill = mixHex(C.focus, '#F59E95', k2);
    burn = <path d={rr4(BURN_X, SKIN_TOP + d / 2, w, d, r4(0.01), r4(0.01), [w * 0.47, d * 0.94], [w * 0.47, d * 0.94])} fill={fill} opacity={0.92} />;
  }
  return (
    <Pop t={t} tIn={ev.s3.skin} tOut={ev.s4.clear} cx={600} cy={790}>
      <defs>
        <clipPath id="skinClip"><path d={rr(600, 790, 640, 200, 18)} /></clipPath>
      </defs>
      <g clipPath="url(#skinClip)">
        <rect x={280} y={690} width={640} height={24} fill={C.epi} />
        <rect x={280} y={714} width={640} height={86} fill={C.dermis} />
        <rect x={280} y={800} width={640} height={90} fill={C.fat} />
        <line x1={280} x2={920} y1={714} y2={714} stroke="#E4A992" strokeWidth={2} />
        <line x1={280} x2={920} y1={800} y2={800} stroke="#E6CFA0" strokeWidth={2} />
        {burn}
      </g>
      {t >= ev.s3.skin + 0.3 ? (
        <g>
          <Label x={940} y={710}>Epidermis</Label>
          <Label x={940} y={765}>Dermis</Label>
          <Label x={940} y={853}>Fat</Label>
        </g>
      ) : null}
      {/* the droplet of hot oil: a ballistic arc out of the pot */}
      {vis(t, pop, drop) ? (() => {
        const u = (t - pop) / (drop - pop);
        const x = lerp(690, BURN_X, u);
        const y = lerp(335, SKIN_TOP - 6, u) - 260 * 4 * u * (1 - u);
        return <circle cx={x} cy={y} r={13} fill={C.focus} />;
      })() : null}
    </Pop>
  );
};

const Water: React.FC<{t: number}> = ({t}) => {
  const on = CARD('3B').on;
  const {water} = ev.s3;
  const len = t >= water ? ease(t, water, 0.35, 0, SKIN_TOP - 598, 'snap') : 0;
  return (
    <g>
      <Pop t={t} tIn={on} tOut={ev.s4.clear} cx={790} cy={575}>
        <path d={rr(812, 568, 110, 22, 11)} fill={C.ink2} />
        <path d={rr(BURN_X, 584, 28, 32, 8)} fill={C.ink2} />
      </Pop>
      {len > 0.5 && t < ev.s4.clear + OUT ? (
        <g opacity={1} transform={t >= ev.s4.clear ? `translate(${BURN_X} ${SKIN_TOP}) scale(${1 - progress(t, ev.s4.clear, OUT, 'accel')}) translate(${-BURN_X} ${-SKIN_TOP})` : ''}>
          <rect x={BURN_X - 11} y={598} width={22} height={len} fill={C.normal} opacity={0.9} />
          <line x1={BURN_X} x2={BURN_X} y1={598} y2={598 + len} stroke="#FFFFFF" strokeOpacity={0.45} strokeWidth={5} strokeDasharray="10 22" strokeDashoffset={-(t - water) * 260} />
          <path d={rr(BURN_X, SKIN_TOP + 1, 30 + 60 * clamp01((len - 60) / 32), 8, 4)} fill={C.normal} opacity={0.75} />
        </g>
      ) : null}
    </g>
  );
};

// ---------- scene 4: choking and food bolus ----------
const AIR_X = 630;
const ESO_X = 770;
const ESO_PATH = 'M728 260 L812 260 L812 772 C812 790 798 792 798 805 C798 818 812 820 812 838 L812 916 Q812 940 788 940 L752 940 Q728 940 728 916 L728 838 C728 820 742 818 742 805 C742 792 728 790 728 772 Z';
const CAP_OUTLINE = 'M582 292 L582 250 A80 60 0 0 1 662 190 L738 190 A80 60 0 0 1 818 250 L818 292 M678 292 L728 292';

const biteAt = (t: number): [number, number] => {
  const s = ev.s4;
  if (t < s.toss) return [380, 826];
  if (t < s.biteLand) {
    const u = (t - s.toss) / (s.biteLand - s.toss);
    return [lerp(380, AIR_X, u), lerp(826, 335, u) - 380 * 4 * u * (1 - u)];
  }
  const t2 = s.thrust2 + 0.08;
  if (t < s.thrust1) return [AIR_X, 335];
  if (t < t2) return [AIR_X, keys(t, [[s.thrust1, 335], [s.thrust1 + 0.15, 318], [s.thrust1 + 0.45, 335]], 'snap')];
  if (t < s.fall) return overshoot(t, t2, 0.5, [AIR_X, 335], [700, 248], 0.06) as [number, number];
  return [ease(t, s.fall, 0.25, 700, ESO_X, 'snap'), ease(t, s.fall, s.lodge - s.fall, 248, 775, 'accel')];
};

const Airways: React.FC<{t: number}> = ({t}) => {
  const s = ev.s4;
  if (!vis(t, s.tubes, ev.s5.clear + OUT)) return null;
  const grow = ease(t, s.tubes, 0.7, 0, 790, 'snap');
  const out = t >= ev.s5.clear ? 1 - progress(t, ev.s5.clear, OUT, 'accel') : 1;
  if (out <= 0.0005) return null;
  const g = progress(t, s.fall, 0.3, 'snap'); // 4C: the airway is no longer the story
  const airStroke = mixHex(C.line, C.divider, g);
  const ringFill = mixHex(C.divider, '#F1EFEB', g);
  const rings = [] as number[];
  for (let y = 312; y <= 912; y += 46) rings.push(y);
  return (
    <g transform={`translate(700 560) scale(${out}) translate(-700 -560)`}>
      <defs>
        <clipPath id="tubeClip"><rect x={560} y={182} width={280} height={grow} /></clipPath>
      </defs>
      <g clipPath="url(#tubeClip)">
        <path d={rr4(AIR_X, 600, 96, 680, r4(0.01), r4(0.01), r4(24), r4(24))} fill={C.soft} stroke={airStroke} strokeWidth={4} />
        {rings.map((y) => <path key={y} d={rr(AIR_X, y, 78, 10, 5)} fill={ringFill} />)}
        <path d={ESO_PATH} fill={C.epi} stroke="#E2A592" strokeWidth={4} />
        <path d={rr4(700, 240, 236, 104, [80, 60], [80, 60], r4(0.01), r4(0.01))} fill={C.epi} />
        <path d={CAP_OUTLINE} fill="none" stroke="#E2A592" strokeWidth={4} strokeLinejoin="round" />
      </g>
      {t >= s.tubes + 0.5 ? (
        <g>
          <Label x={AIR_X} y={985} anchor="middle" color={mixHex(C.ink2, C.inactive, g)}>Airway</Label>
          <Label x={ESO_X + 18} y={985} anchor="middle">Esophagus</Label>
        </g>
      ) : null}
    </g>
  );
};

const Bite: React.FC<{t: number}> = ({t}) => {
  const s = ev.s4;
  const k = popK(t, ev.s4.clear + 0.4, ev.s5.clear, 0.45);
  if (k <= 0.0005) return null;
  const [x, y] = biteAt(t);
  const sq1 = squash(t, s.biteLand, 'y', 0.14);
  const sq2 = squash(t, s.lodge, 'y', 0.14);
  const rx = 30 * k * sq1.sx * sq2.sx;
  const ry = 30 * k * sq1.sy * sq2.sy;
  // ring A: red on the blocked airway, teal once the thrusts clear it, gone when it falls
  const t2 = s.thrust2 + 0.08;
  const ringA = t >= s.biteLand && t < s.fall + OUT ? (t < s.fall ? overshoot(t, s.biteLand, 0.45, 0, 1, 0.08) : 1 - progress(t, s.fall, OUT, 'accel')) : 0;
  const ringAc = mixHex(C.alert, C.normal, progress(t, t2, 0.3, 'snap'));
  const ringB = popK(t, s.lodge, ev.s5.clear, 0.45, 0.08);
  // abdominal thrusts: two pulses of upward chevrons below the bite
  const chev = [s.thrust1, s.thrust2].flatMap((tp) => [0, 1].map((j) => ({tp: tp + j * 0.07, y0: 520 + j * 52})));
  return (
    <g>
      {chev.map(({tp, y0}, i) => {
        if (t < tp || t > tp + 0.55) return null;
        const yy = ease(t, tp, 0.45, y0, y0 - 70, 'snap');
        const o = fadeSmall(t, tp, 0.1) * (1 - progress(t, tp + 0.35, 0.2, 'linear'));
        return <polyline key={i} points={`${AIR_X - 24},${yy + 12} ${AIR_X},${yy - 10} ${AIR_X + 24},${yy + 12}`} fill="none" stroke={C.normal} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" opacity={o} />;
      })}
      <ellipse cx={x} cy={y} rx={rx} ry={ry} fill={C.food} stroke="#C2A27E" strokeWidth={3} />
      <path d={`M${x - 12 * k} ${y - 6 * k} q ${8 * k} ${-6 * k} ${16 * k} 0`} fill="none" stroke="#C2A27E" strokeWidth={3} strokeLinecap="round" />
      {ringA > 0.001 ? <circle cx={x} cy={y} r={48 * ringA} fill="none" stroke={ringAc} strokeWidth={5} /> : null}
      {ringB > 0.001 ? <circle cx={ESO_X} cy={792} r={56 * ringB} fill="none" stroke={C.alert} strokeWidth={5} /> : null}
    </g>
  );
};

// ---------- scene 5: C. perfringens ----------
function mulberry(seed: number) {
  return () => {
    seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
    let r = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}
const ROD_POS: {x: number; y: number; a: number}[] = (() => {
  const rnd = mulberry(11);
  const pts: {x: number; y: number; a: number}[] = [];
  [494, 514, 534, 553, 570].forEach((y, row) => {
    for (let x = 600 - 170 + (row % 2) * 16; x <= 770; x += 32) {
      if (((x - 600) / 158) ** 2 + ((y - 581) / 100) ** 2 <= 1) pts.push({x: x + (rnd() - 0.5) * 8, y: y + (rnd() - 0.5) * 5, a: (rnd() - 0.5) * 70});
    }
  });
  for (let i = pts.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [pts[i], pts[j]] = [pts[j], pts[i]];
  }
  return pts.slice(0, 40);
})();
const genOf = (i: number) => (i < 5 ? 0 : i < 10 ? 1 : i < 20 ? 2 : 3);
const parentOf = (i: number) => [0, 5, 10, 20][genOf(i)];

const Dish: React.FC<{t: number}> = ({t}) => {
  const s = ev.s5;
  const clr = ev.s6.clear;
  const lidT = s.dish + 0.45;
  const lift = progress(t, s.lid, 0.6, 'snap');
  const lidOut = t >= clr ? 1 - progress(t, clr, OUT, 'accel') : 1;
  const lidIn = popK(t, lidT, Infinity, 0.45);
  const gens: number[] = s.gens;
  const spore: Sh = {cx: 0, cy: 0, w: 22, h: 14, tl: [11, 7], tr: [11, 7], br: [11, 7], bl: [11, 7], fill: C.bg, stroke: C.ink2, sw: 3};
  const rod: Sh = {cx: 0, cy: 0, w: 30, h: 12, tl: r4(6), tr: r4(6), br: r4(6), bl: r4(6), fill: C.focus, stroke: C.focus, sw: 2};
  return (
    <g>
      <Pop t={t} tIn={lidT} tOut={clr} cx={600} cy={560} dIn={0.45}>
        <path d="M420 582 A180 118 0 0 1 780 582 Z" fill={C.mound} stroke="#D6C0A2" strokeWidth={3} />
      </Pop>
      {/* bacteria: spores survive cooking; then they germinate and double, again and again */}
      {ROD_POS.map((p, i) => {
        const g = genOf(i);
        const born = g === 0 ? s.spores + i * (2 / 30) : gens[g];
        if (t < born) return null;
        const out = t >= clr ? 1 - progress(t, clr, OUT, 'accel') : 1;
        if (out <= 0.0005) return null;
        let x = p.x, y = p.y, a = p.a, sc = 1, sh: Sh;
        if (g === 0) {
          sc = overshoot(t, born, 0.4, 0, 1, 0.08);
          sh = mixSh(spore, rod, progress(t, gens[0], 0.35, 'snap'));
        } else {
          const par = ROD_POS[i - parentOf(i)];
          const k = progress(t, born, 0.45, 'snap');
          x = lerp(par.x, p.x, k); y = lerp(par.y, p.y, k); a = lerp(par.a, p.a, k);
          sh = rod;
        }
        return (
          <g key={i} transform={`translate(${x} ${y}) rotate(${a}) scale(${sc * out})`}>
            <path d={pathOf(sh)} fill={sh.fill} stroke={sh.stroke} strokeWidth={sh.sw} />
          </g>
        );
      })}
      {lidIn > 0.0005 && lidOut > 0.0005 ? (
        <g transform={`translate(${-170 * lift} ${-190 * lift}) rotate(${-14 * lift} 600 506) translate(600 540) scale(${lidIn * lidOut}) translate(-600 -540)`}>
          <path d="M398 582 A202 150 0 0 1 802 582 Z" fill={C.bg} stroke={C.ink} strokeWidth={5} strokeLinejoin="round" />
          <path d={rr(600, 423, 56, 22, 11)} fill={C.ink} />
        </g>
      ) : null}
      {/* shield (spores survive heat), swapped for the clock (time at room temperature) */}
      <Pop t={t} tIn={s.shield} tOut={s.clock - OUT} cx={860} cy={300}>
        <path d="M860 254 L896 268 L896 300 C896 326 878 342 860 350 C842 342 824 326 824 300 L824 268 Z" fill={C.bg} stroke={C.ink} strokeWidth={5} strokeLinejoin="round" />
        <path d="M860 286 C870 296 872 304 868 314 C866 320 854 320 852 314 C848 306 852 298 860 286 Z" fill={C.ink2} />
      </Pop>
      <Pop t={t} tIn={s.clock} tOut={clr} cx={860} cy={300}>
        <Clock t={t} t0={s.clock + 0.2} />
      </Pop>
      {/* months: outbreaks peak in November and December */}
      {'JFMAMJJASOND'.split('').map((m, i) => {
        const cx = 186 + i * 70 + 29;
        const hot = i >= 10;
        const k = hot ? progress(t, s.peak, 0.3, 'snap') : 0;
        const bump = hot ? keys(t, [[s.peak, 1], [s.peak + 0.18, 1.12], [s.peak + 0.45, 1]], 'snap') : 1;
        return (
          <Pop key={i} t={t} tIn={s.months + i * (2 / 30)} tOut={clr} cx={cx} cy={860} dIn={0.45}>
            <g transform={`translate(${cx} 860) scale(${bump}) translate(${-cx} -860)`}>
              <path d={rr(cx, 860, 58, 58, 12)} fill={mixHex(C.soft, C.focus, k)} stroke={mixHex(C.divider, C.focus, k)} strokeWidth={2} />
              <text x={cx} y={869} textAnchor="middle" fontFamily={FONT.head} fontWeight={700} fontSize={24} fill={mixHex(C.ink2, '#FFFFFF', k)}>{m}</text>
            </g>
          </Pop>
        );
      })}
    </g>
  );
};

const Clock: React.FC<{t: number; t0: number}> = ({t, t0}) => {
  const turns = ease(t, t0, 2.6, 0, 8, 'cross'); // 8 hours pass on the minute hand
  const mA = turns * 360 - 90;
  const hA = 180 + turns * 30 - 90; // from 6 o'clock
  const p = (a: number, r: number) => [860 + Math.cos((a * Math.PI) / 180) * r, 300 + Math.sin((a * Math.PI) / 180) * r];
  const [mx, my] = p(mA, 38);
  const [hx, hy] = p(hA, 25);
  return (
    <g>
      <circle cx={860} cy={300} r={56} fill={C.bg} stroke={C.ink} strokeWidth={5} />
      {Array.from({length: 12}, (_, i) => {
        const [x1, y1] = p(i * 30, 44);
        const [x2, y2] = p(i * 30, 49);
        return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={C.ink2} strokeWidth={3} strokeLinecap="round" />;
      })}
      <line x1={860} y1={300} x2={hx} y2={hy} stroke={C.ink} strokeWidth={6} strokeLinecap="round" />
      <line x1={860} y1={300} x2={mx} y2={my} stroke={C.ink} strokeWidth={4} strokeLinecap="round" />
      <circle cx={860} cy={300} r={6} fill={C.ink} />
    </g>
  );
};

// ---------- scene 6: holiday heart ----------
const X0 = 140, X1 = 1020, BASE = 560, SPEED = 260;
const g = (x: number, s: number) => Math.exp(-(x * x) / (s * s));
function ecg(tau: number): number {
  const s = ev.s6;
  if (tau < s.write) return 0;
  let v = 0;
  const af = tau < s.convert ? clamp01((tau - s.write) / 0.25) * (1 - clamp01((tau - s.convert + 0.15) / 0.15)) : 0;
  if (af > 0) v += af * (4.5 * Math.sin(2 * Math.PI * 6.3 * tau) + 3 * Math.sin(2 * Math.PI * 8.9 * tau + 1.3) + 2.2 * Math.sin(2 * Math.PI * 4.7 * tau + 2.1));
  for (const q of s.qrs as {t: number; kind: string}[]) {
    const d = tau - q.t;
    if (d < -0.3 || d > 0.6) continue;
    v += -10 * g(d + 0.026, 0.009) + 118 * g(d, 0.011) - 30 * g(d - 0.027, 0.01) + 20 * g(d - 0.29, 0.055);
    if (q.kind === 'sinus') v += 11 * g(d + 0.17, 0.034);
  }
  return v;
}
const Ecg: React.FC<{t: number}> = ({t}) => {
  const s = ev.s6;
  if (!vis(t, s.line, T_ECG_OFF)) return null;
  const amp = t >= ev.s7.clear ? 1 - progress(t, ev.s7.clear, 0.3, 'accel') : 1;
  const pts: string[] = [];
  for (let x = X0; x <= X1; x += 2) pts.push(`${x},${(BASE - amp * ecg(t - (X1 - x) / SPEED)).toFixed(1)}`);
  const head = BASE - amp * ecg(t);
  const sinus = t >= s.qrs.find((q: any) => q.kind === 'sinus').t;
  return (
    <g>
      {vis(t, T_ECG_ON, T_ECG_OFF) ? (
        <g>
          <polyline points={pts.join(' ')} fill="none" stroke={C.signal} strokeWidth={5} strokeLinejoin="round" strokeLinecap="round" />
          <circle cx={X1} cy={head} r={8} fill={C.signal} />
        </g>
      ) : null}
      {vis(t, CARD('6A').on, ev.s7.clear) ? <Label x={X0} y={400} size={26} weight={600}>{sinus ? 'Sinus rhythm' : 'Atrial fibrillation'}</Label> : null}
    </g>
  );
};
const GlassDrink: React.FC<{t: number}> = ({t}) => {
  const s = ev.s6;
  if (!vis(t, s.glass + 0.2, s.line)) return null;
  const top = ease(t, s.glass + 0.3, 0.5, 582, 432);
  const out = 1 - progress(t, s.line - OUT, OUT, 'accel'); // drains just before the glass flattens into the baseline
  const gl = heroAt(t);
  return (
    <g>
      <defs><clipPath id="glassClip"><path d={pathOf(gl)} /></clipPath></defs>
      <g clipPath="url(#glassClip)">
        <g transform={`translate(600 580) scale(1 ${out}) translate(-600 -580)`}>
          <rect x={520} y={top} width={160} height={600 - top} fill={C.drink} />
        </g>
      </g>
      <path d={pathOf(gl)} fill="none" stroke={gl.stroke} strokeWidth={gl.sw} />
    </g>
  );
};

// ---------- scene 7: the plate and the five hazards ----------
const Icon: React.FC<{kind: number; x: number; y: number}> = ({kind, x, y}) => {
  const ink = C.ink;
  switch (kind) {
    case 0: // knife
      return (
        <g transform={`rotate(-35 ${x} ${y})`}>
          <path d={rr4(x + 10, y - 1, 52, 16, r4(2), r4(0.01), [24, 15], r4(2))} fill={ink} />
          <path d={rr(x - 26, y, 26, 12, 6)} fill={ink} />
        </g>
      );
    case 1: // pot
      return (
        <g>
          <path d={rr4(x, y + 6, 52, 36, r4(3), r4(3), r4(12), r4(12))} fill={ink} />
          <path d={rr(x, y - 14, 62, 7, 3.5)} fill={ink} />
          <path d={rr(x - 31, y - 3, 12, 6, 3)} fill={ink} />
          <path d={rr(x + 31, y - 3, 12, 6, 3)} fill={ink} />
        </g>
      );
    case 2: // drumstick
      return (
        <g transform={`rotate(-40 ${x} ${y})`}>
          <ellipse cx={x + 8} cy={y} rx={20} ry={15} fill={ink} />
          <path d={rr(x - 16, y, 22, 8, 4)} fill={ink} />
          <circle cx={x - 27} cy={y - 5} r={5.5} fill={ink} />
          <circle cx={x - 27} cy={y + 5} r={5.5} fill={ink} />
        </g>
      );
    case 3: // covered dish
      return (
        <g>
          <path d={`M${x - 28} ${y + 10} A28 24 0 0 1 ${x + 28} ${y + 10} Z`} fill={ink} />
          <path d={rr(x, y + 14, 66, 7, 3.5)} fill={ink} />
          <path d={rr(x, y - 16, 12, 7, 3.5)} fill={ink} />
        </g>
      );
    default: // wine glass
      return (
        <g>
          <path d={`M${x - 16} ${y - 24} L${x + 16} ${y - 24} L${x + 16} ${y - 12} A16 16 0 0 1 ${x - 16} ${y - 12} Z`} fill={ink} />
          <path d={rr(x, y + 10, 5, 26, 2.5)} fill={ink} />
          <path d={rr(x, y + 24, 28, 6, 3)} fill={ink} />
        </g>
      );
  }
};
const Icons: React.FC<{t: number}> = ({t}) => (
  <g>
    {[-165, -125, -90, -55, -15].map((a, i) => {
      const x = 960 + Math.cos((a * Math.PI) / 180) * 285;
      const y = 410 + Math.sin((a * Math.PI) / 180) * 285;
      return (
        <Pop key={i} t={t} tIn={ev.s7.icons + i * (2 / 30)} tOut={ES} cx={x} cy={y} dIn={0.45} over={0.08}>
          <Icon kind={i} x={x} y={y} />
        </Pop>
      );
    })}
  </g>
);

/** The whole art layer for time t (no <svg> wrapper, so the thumbnail can reuse it). */
export const ArtLayer: React.FC<{t: number}> = ({t}) => (
  <g>
    <Knife t={t} part="board" />
    <Airways t={t} />
    <Dish t={t} />
    <Hero t={t} />
    <Knife t={t} part="handle" />
    {t < ev.s4.clear + OUT ? <Oil t={t} /> : null}
    <PotParts t={t} />
    <GlassDrink t={t} />
    <Skin t={t} />
    <Water t={t} />
    <Bite t={t} />
    <Ecg t={t} />
    <Icons t={t} />
  </g>
);
