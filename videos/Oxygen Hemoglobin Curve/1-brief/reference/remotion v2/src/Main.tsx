import React from 'react';
import {AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {C, fontFamily} from './theme';
import {FPS, clamp, ss, lerp, mix, spr, win} from './util';
import {w, SENT} from './cues';
import {Chain, Heme, HEME_POS, CHAIN} from './tetramer';
import {LogoMorph} from './logo';
import {introAt, IM, tPeak} from './intromotion';
import {N, P50N, P50L, P50R, sat, PL, PR, PT, PB, X, Y, curvePath} from './hill';

// ---------- key times (seconds), all taken from the approved voice-over ----------
const T = {
  pick: w(7), go: w(13), oneGraph: w(20), title: w(27),
  axesX: w(31), xTitle: w(36), yAx: w(45), yTitle: w(49),
  hb: w(60), sub: w(62), heme: w(68), coop: w(76), first: w(82), shape: w(85), next: w(90), straight: w(101), S: w(108), sig: w(111),
  lm: w(113), lung: w(116), tis: w(131), quarter: w(145),
  p50: w(157), p50def: w(167), p50val: w(185),
  shapeS: w(189), flat: w(192), slide1: w(205), plateau: w(218), steep: w(223), slide2: w(233), unload: w(244),
  shift: w(250), right: w(267), rightP50: w(282), f1: w(291), f2: w(293), f3: w(296), f4: w(299), bohr: w(312), muscle: w(314), released: w(327),
  left: w(336), leftP50: w(353), g1: w(358), g2: w(360), g3: w(363), g4: w(366), fetal: w(369), co: w(390),
  sum: w(407), sr: w(410), sl: w(419), rmr: w(435),
};

// ---------- rich text: subscripts for chemistry/physiology notation ----------
const SUB: Record<string, [string, string]> = {
  PO2: ['PO', '2'], P50: ['P', '50'], CO2: ['CO', '2'], SO2: ['SO', '2'], O2: ['O', '2'], 'Fe2+': ['Fe', '2+'],
  a1: ['α', '1'], a2: ['α', '2'], b1: ['β', '1'], b2: ['β', '2'],
};
const Rich: React.FC<{t: string}> = ({t}) => {
  const parts = t.split(/(PO2|P50|CO2|SO2|O2|Fe2\+|a1|a2|b1|b2)/);
  return (<>{parts.map((p, i) => SUB[p]
    ? <span key={i}>{SUB[p][0]}<span style={{fontSize: '0.62em', position: 'relative', top: p === 'Fe2+' ? '-0.55em' : '0.32em', marginLeft: 1}}>{SUB[p][1]}</span></span>
    : <span key={i}>{p}</span>)}</>);
};

// arrow glyph drawn as SVG (font independent)
const Arrow: React.FC<{up: boolean; color: string; size?: number}> = ({up, color, size = 28}) => (
  <svg width={size * 0.62} height={size} viewBox="0 0 20 32" style={{display: 'inline-block', verticalAlign: '-0.12em', marginRight: 8}}>
    <g transform={up ? '' : 'rotate(180 10 16)'}>
      <path d="M10 30 V6" stroke={color} strokeWidth={4} strokeLinecap="round" />
      <path d="M2 13 L10 3 L18 13" stroke={color} strokeWidth={4} fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </g>
  </svg>
);

// positioned HTML label; anchor ax/ay in 0..1; padding keeps text off the edges
const Tag: React.FC<{x: number; y: number; ax?: number; ay?: number; op?: number; k?: number; bg?: string; fg?: string; size?: number; weight?: number; border?: string; pad?: string; radius?: number; children: any; style?: any}> =
  ({x, y, ax = 0.5, ay = 0.5, op = 1, k = 1, bg = C.card, fg = C.ink, size = 26, weight = 500, border, pad = '10px 18px', radius = 12, children, style}) => (
    <div style={{position: 'absolute', left: x, top: y, transform: `translate(${-ax * 100}%, ${-ay * 100}%) translate(0, ${(1 - k) * 14}px) scale(${0.94 + 0.06 * k})`,
      opacity: op * clamp(k * 1.4), background: bg, color: fg, fontSize: size, fontWeight: weight, padding: pad, borderRadius: radius, whiteSpace: 'nowrap', lineHeight: 1.25,
      border: border ? `2px solid ${border}` : undefined, boxShadow: bg === 'transparent' ? undefined : '0 2px 10px rgba(34,32,30,0.06)', ...style}}>{children}</div>
  );

// side panel card
const PX = 1290, PW = 540;
const Card: React.FC<{y: number; op: number; k: number; accent?: string; title: any; lines: any[]; small?: boolean}> = ({y, op, k, accent = C.ink, title, lines, small}) => (
  <div style={{position: 'absolute', left: PX, top: y, width: PW, boxSizing: 'border-box', padding: '22px 28px 24px', background: C.card, borderRadius: 18,
    borderLeft: `8px solid ${accent}`, opacity: op * clamp(k * 1.4), transform: `translate(${(1 - k) * 30}px, 0)`, boxShadow: '0 4px 18px rgba(34,32,30,0.07)'}}>
    <div style={{fontSize: small ? 28 : 32, fontWeight: 700, color: accent, marginBottom: 8}}>{title}</div>
    {lines.map((l, i) => <div key={i} style={{fontSize: small ? 25 : 27, color: C.ink2, lineHeight: 1.4}}>{l}</div>)}
  </div>
);

// ---------- molecules / cells ----------
const O2: React.FC<{x: number; y: number; op?: number; s?: number}> = ({x, y, op = 1, s = 1}) => (
  <g transform={`translate(${x},${y}) scale(${s})`} opacity={op}>
    <circle cx={-6.5} cy={0} r={10} fill={C.o2} stroke="#FBF8F2" strokeWidth={2} />
    <circle cx={6.5} cy={0} r={10} fill={C.o2} stroke="#FBF8F2" strokeWidth={2} />
  </g>
);

const RBC: React.FC<{x: number; y: number; color: string}> = ({x, y, color}) => (
  <g transform={`translate(${x},${y})`}>
    <ellipse cx={0} cy={58} rx={70} ry={10} fill="rgba(34,32,30,0.10)" />
    <ellipse cx={0} cy={0} rx={80} ry={50} fill={color} />
    <ellipse cx={0} cy={-3} rx={78} ry={46} fill="none" stroke="rgba(255,255,255,0.18)" strokeWidth={3} />
    {/* central depression of the biconcave disc */}
    <ellipse cx={0} cy={3} rx={42} ry={23} fill={mix(color, '#000000', 0.22)} />
    <ellipse cx={0} cy={8} rx={36} ry={16} fill={mix(color, '#FFFFFF', 0.12)} />
  </g>
);

// ---------- intro: one red cell, lungs to tissues ----------
const Intro: React.FC<{t: number}> = ({t}) => {
  const out = ss(T.oneGraph + 0.4, T.oneGraph + 1.2, t);
  const appear = ss(1.62, 1.9, t);
  // logo intro: static logo, then the dash (see intromotion.ts)
  const logoIn = spr(t, 0.0, {damping: 16, stiffness: 320});
  const im = introAt(t);
  const mk = im.morph, lxx = im.x, lyy = IM.y, body = im.body;
  const morphOn = mk < 1;
  const rbcOn = mk >= 1 ? 1 : 0;
  const cx = t < T.go ? im.x : lerp(1380, 540, ss(T.go + 0.1, T.go + 1.9, t));
  const load = ss(T.pick + 0.2, T.pick + 2.4, t), unload = ss(T.go + 0.9, T.go + 2.2, t);
  const s = 75 + 22 * load - 22 * unload;
  const color = mix(C.deoxy, C.oxy, (s - 75) / 22);
  const cy = 530;
  const slot = (i: number) => { const a = -Math.PI / 2 + (i / 8) * Math.PI * 2; return [Math.cos(a) * 104, Math.sin(a) * 68]; };
  const mols: any[] = [];
  for (let i = 0; i < 8; i++) {
    let [ox, oy] = slot(i);
    let x = cx + ox, y = cy + oy, op = 1;
    if (i >= 6) {
      const kin = ss(T.pick + 0.1 + (i - 6) * 0.4, T.pick + 1.7 + (i - 6) * 0.4, t);
      const kout = ss(T.go + 0.9 + (i - 6) * 0.3, T.go + 2.0 + (i - 6) * 0.3, t);
      const sx = 1380 + (i === 6 ? -60 : 70), sy = 400;
      x = lerp(sx, x, kin); y = lerp(sy, y, kin); op = clamp(kin * 3);
      if (kout > 0) { const ex = cx + (i === 6 ? -150 : 150), ey = cy + 150; x = lerp(x, ex, kout); y = lerp(y, ey, kout); op = 1 - kout; }
    }
    mols.push(<O2 key={i} x={x} y={y} op={op * appear} />);
  }
  const zone = (x: number, name: string, sub: string, hot: number) => (
    <Tag x={x} y={404} ay={1} k={spr(t, 1.64, {damping: 14, stiffness: 260})} bg={C.card} border={hot > 0.5 ? C.ink : C.line}>
      <div style={{fontSize: 40, fontWeight: 700}}>{name}</div><div style={{fontSize: 28, color: C.ink2}}><Rich t={sub} /></div>
    </Tag>);
  return (<>
    <AbsoluteFill style={{opacity: 1 - out}}>
      <svg width={1920} height={1080} style={{position: 'absolute'}}>
        <g opacity={appear}>
          <rect x={260} y={470} width={1400} height={120} rx={60} fill={C.tube} />
          <rect x={260} y={470} width={1400} height={120} rx={60} fill="none" stroke={C.tubeWall} strokeWidth={3} />
        </g>
        {mols}
        {morphOn && <g transform={body}><LogoMorph lx={lxx} ly={lyy} s={4.6 * (0.9 + 0.1 * logoIn)} ex={lxx} ey={lyy} rx={80} ry={50} k={mk} fill={mix(C.red, C.deoxy, mk)} op={clamp(logoIn * 1.5)} /></g>}
        <g opacity={rbcOn} transform={t < tPeak + 1.2 ? body : undefined}><RBC x={cx} y={cy} color={color} /></g>
      </svg>
      {zone(540, 'Tissues', 'PO2 ≈ 40 mmHg', unload)}
      {zone(1380, 'Lungs', 'PO2 ≈ 100 mmHg', t < T.go ? 1 : 0)}
      <div style={{position: 'absolute', left: 260, top: 690, display: 'flex', alignItems: 'center', gap: 12, fontSize: 24, color: C.ink2, opacity: appear}}>
        <svg width={36} height={24}><O2 x={18} y={12} /></svg><span><Rich t="= one O2 molecule (schematic)" /></span>
      </div>
      <Tag x={cx} y={cy + 92} ay={0} k={appear} size={26} weight={700} fg={color} bg={C.card}>Saturation {Math.round(s)}%</Tag>
    </AbsoluteFill>
    <Tag x={960} y={590} ay={0} k={spr(t, T.oneGraph + 1.0)} op={1 - ss(T.axesX - 1.2, T.axesX - 0.6, t)} bg="transparent" fg={C.ink2} size={30} weight={400} style={{boxShadow: 'none'}}>
      Hemoglobin carries 98% of the oxygen in blood. Only 2% is dissolved in plasma.
    </Tag>
  </>);
};

// ---------- hemoglobin tetramer (ribbon schematic, see tetramer.tsx) ----------
const CS = 0.88; // chain scale
const Tetramer: React.FC<{t: number}> = ({t}) => {
  const cx = PX + PW / 2, cy = 455;
  const rState = ss(T.shape - 0.1, T.shape + 1.0, t);
  const rot = 9 * (1 - rState), gap = 10 * (1 - rState);
  // alpha chains diagonal; top pair = a1b1 dimer, bottom pair = b2a2 dimer
  const sub = [
    {n: 'a1', kind: 'alpha', sx: 1, sy: 1, dx: -98, dy: -88, bind: T.first, top: true},
    {n: 'b1', kind: 'beta', sx: -1, sy: 1, dx: 98, dy: -88, bind: T.next, top: true},
    {n: 'b2', kind: 'beta', sx: 1, sy: -1, dx: -98, dy: 88, bind: T.next + 0.7, top: false},
    {n: 'a2', kind: 'alpha', sx: -1, sy: -1, dx: 98, dy: 88, bind: T.next + 0.35, top: false},
  ] as const;
  const hemeK = ss(T.heme - 0.1, T.heme + 0.5, t);
  const pulse = 1 + 0.18 * Math.sin(clamp((t - T.heme) / 1.2) * Math.PI);
  const labK = ss(T.sub - 0.1, T.sub + 0.5, t);
  const group = (top: boolean) => sub.filter((s) => s.top === top).map((s) => {
    const hx = s.dx + s.sx * HEME_POS[0] * CS, hy = s.dy + s.sy * HEME_POS[1] * CS;
    const bk = ss(s.bind, s.bind + 0.7, t);
    const ang = Math.atan2(s.dy, s.dx);
    const fx = hx + Math.cos(ang) * 200, fy = hy + Math.sin(ang) * 160;
    return (
      <g key={s.n}>
        <g transform={`translate(${s.dx},${s.dy}) scale(${s.sx * CS},${s.sy * CS})`}><Chain kind={s.kind} /></g>
        <Heme x={hx} y={hy} s={hemeK > 0 ? pulse : 1} op={0.55 + 0.45 * hemeK} />
        {t > s.bind - 0.05 && <O2 x={lerp(fx, hx, bk)} y={lerp(fy, hy + (s.top ? -12 : 12), bk)} op={clamp(bk * 3)} s={0.9} />}
      </g>);
  });
  const subLabels = sub.map((s) => (
    <Tag key={s.n} x={cx + Math.sign(s.dx) * 238} y={cy + Math.sign(s.dy) * 160} op={labK} bg="transparent" fg={CHAIN[s.kind].edge} size={32} weight={700} pad="0px 4px" style={{boxShadow: 'none'}}><Rich t={s.n} /></Tag>));
  return (
    <>
      <svg width={1920} height={1080} style={{position: 'absolute'}}>
        <g transform={`translate(${cx},${cy})`}>
          <g transform={`translate(0,${-gap}) rotate(${-rot})`}>{group(true)}</g>
          <g transform={`translate(0,${gap}) rotate(${rot})`}>{group(false)}</g>
        </g>
      </svg>
      {subLabels}
    </>);
};

// ---------- the graph ----------
const Graph: React.FC<{t: number}> = ({t}) => {
  const xK = ss(T.axesX - 0.4, T.axesX + 0.9, t), yK = ss(T.yAx - 0.3, T.yAx + 0.8, t);
  const gridK = ss(T.yAx + 0.5, T.yAx + 1.5, t);
  const ticks = Array.from({length: 11}, (_, i) => i * 10);
  // normal curve draw-on
  const drawK = ss(T.S - 0.3, T.S + 2.0, t);
  const straightOp = win(t, T.straight - 0.3, T.S + 2.4, 0.4, 0.6);
  // shifts
  const rK = spr(t, T.right + 0.2, {damping: 22, stiffness: 70});
  const lK = spr(t, T.left + 0.4, {damping: 22, stiffness: 70});
  const p50r = lerp(P50N, P50R, rK), p50l = lerp(P50N, P50L, lK);
  const rDim = 1 - 0.68 * ss(T.left - 0.2, T.left + 0.6, t) + 0.68 * ss(T.sum - 0.2, T.sum + 0.6, t);
  const rOp = ss(T.right - 0.2, T.right + 0.4, t) * rDim;
  const lOp = ss(T.left, T.left + 0.6, t);
  // landmarks
  const lmFade = 1 - 0.75 * ss(T.p50 - 0.3, T.p50 + 0.4, t);
  const lmOut = 1 - ss(T.shapeS - 0.4, T.shapeS + 0.3, t);
  const A = ss(T.lung - 0.1, T.lung + 0.7, t) * lmFade * lmOut, B = ss(T.tis - 0.1, T.tis + 0.7, t) * lmFade * lmOut;
  const Q = ss(T.quarter, T.quarter + 0.8, t) * lmFade * lmOut;
  // P50 normal marker: visible from p50 on, dims in the shape section, returns for shifts
  const p50K = ss(T.p50 - 0.1, T.p50 + 1.2, t);
  const p50Op = p50K * (1 - 0.8 * win(t, T.shapeS - 0.2, T.shift + 0.2, 0.5, 0.5));
  // shape section
  const shapeOp = win(t, T.flat - 0.3, T.shift - 0.1, 0.5, 0.6);
  const m1 = ss(T.slide1, T.slide1 + 1.8, t), m1Op = win(t, T.flat + 0.6, T.steep - 0.1, 0.4, 0.5);
  const m2 = ss(T.slide2, T.slide2 + 1.4, t), m2Op = win(t, T.steep + 0.2, T.shift - 0.1, 0.4, 0.5);
  const plateauBand = win(t, T.flat - 0.3, T.steep - 0.1, 0.5, 0.5), steepBand = win(t, T.steep - 0.2, T.shift - 0.1, 0.5, 0.5);
  const p1 = lerp(100, 60, m1), p2 = lerp(40, 30, m2);
  // released comparison at PO2 40
  const relOp = win(t, T.released, T.left, 0.5, 0.5);
  const dash = '7 8';
  const p50Line = (p: number, color: string, op: number, label: string) => (
    <g opacity={op}>
      <line x1={X(0)} y1={Y(50)} x2={X(p)} y2={Y(50)} stroke={color} strokeWidth={2} strokeDasharray={dash} />
      <line x1={X(p)} y1={Y(50)} x2={X(p)} y2={PB} stroke={color} strokeWidth={2} strokeDasharray={dash} />
      <circle cx={X(p)} cy={Y(50)} r={8} fill={color} stroke={C.card} strokeWidth={3} />
    </g>);
  return (
    <>
      <svg width={1920} height={1080} style={{position: 'absolute'}}>
        {yK > 0.001 && <rect x={PL} y={PT} width={(PR - PL) * xK} height={PB - PT} fill={C.card} opacity={yK} />}
        <g opacity={gridK}>
          {ticks.slice(1).map((v) => <line key={'gx' + v} x1={X(v)} y1={PT} x2={X(v)} y2={PB} stroke={C.grid} strokeWidth={1.5} />)}
          {ticks.slice(1).map((v) => <line key={'gy' + v} x1={PL} y1={Y(v)} x2={PR} y2={Y(v)} stroke={C.grid} strokeWidth={1.5} />)}
        </g>
        {/* shape-section bands */}
        <rect x={X(60)} y={PT} width={X(100) - X(60)} height={PB - PT} fill={C.band} opacity={plateauBand} />
        <rect x={X(20)} y={PT} width={X(60) - X(20)} height={PB - PT} fill={C.band} opacity={steepBand} />
        {/* quarter unloaded band */}
        <rect x={X(40)} y={Y(sat(100, P50N))} width={X(100) - X(40)} height={Y(sat(40, P50N)) - Y(sat(100, P50N))} fill={C.redSoft} opacity={0.75 * Q} />
        {/* axes */}
        <line x1={PL} y1={PB} x2={PL + (PR - PL) * xK} y2={PB} stroke={C.ink} strokeWidth={3} />
        {yK > 0.001 && <line x1={PL} y1={PB} x2={PL} y2={PB - (PB - PT) * yK} stroke={C.ink} strokeWidth={3} />}
        {ticks.map((v) => { const o = ss(T.axesX + v / 120, T.axesX + v / 120 + 0.3, t); return o > 0.001 ? <line key={'tx' + v} x1={X(v)} y1={PB} x2={X(v)} y2={PB + 10} stroke={C.ink} strokeWidth={2} opacity={o} /> : null; })}
        {ticks.map((v) => { const o = ss(T.yAx + v / 120, T.yAx + v / 120 + 0.3, t); return o > 0.001 ? <line key={'ty' + v} x1={PL - 10} y1={Y(v)} x2={PL} y2={Y(v)} stroke={C.ink} strokeWidth={2} opacity={o} /> : null; })}
        {/* straight-line foil */}
        <line x1={X(0)} y1={Y(0)} x2={X(100)} y2={Y(100)} stroke={C.mute} strokeWidth={3} strokeDasharray="4 10" opacity={straightOp} />
        {/* landmark guides */}
        <g opacity={A}>
          <line x1={PL} y1={Y(sat(100, P50N))} x2={X(100)} y2={Y(sat(100, P50N))} stroke={C.ink} strokeWidth={2} strokeDasharray={dash} />
        </g>
        <g opacity={B}>
          <line x1={PL} y1={Y(sat(40, P50N))} x2={X(40)} y2={Y(sat(40, P50N))} stroke={C.ink} strokeWidth={2} strokeDasharray={dash} />
          <line x1={X(40)} y1={Y(sat(40, P50N))} x2={X(40)} y2={PB} stroke={C.ink} strokeWidth={2} strokeDasharray={dash} />
        </g>
        {/* P50 guides */}
        {p50Line(p50r, C.red, rOp * ss(T.rightP50 - 0.2, T.rightP50 + 0.5, t), '')}
        {p50Line(p50l, C.blue, lOp * ss(T.leftP50 - 0.2, T.leftP50 + 0.5, t), '')}
        <g opacity={p50Op}>
          <line x1={X(0)} y1={Y(50)} x2={X(P50N) * 1} y2={Y(50)} stroke={C.ink} strokeWidth={2} strokeDasharray={dash} strokeDashoffset={0} style={{}} />
          <line x1={X(P50N)} y1={Y(50)} x2={X(P50N)} y2={lerp(Y(50), PB, ss(T.p50def - 0.2, T.p50def + 0.8, t))} stroke={C.ink} strokeWidth={2} strokeDasharray={dash} />
        </g>
        {/* released comparison at 40 mmHg */}
        <g opacity={relOp}>
          <line x1={X(40)} y1={Y(sat(40, P50N))} x2={X(40)} y2={Y(sat(40, P50R))} stroke={C.red} strokeWidth={8} strokeLinecap="round" opacity={0.35} />
          <line x1={X(40)} y1={Y(sat(40, P50N)) + 12} x2={X(40)} y2={PB} stroke={C.ink2} strokeWidth={2} strokeDasharray={dash} />
        </g>
        {/* curves */}
        <path d={curvePath(p50r)} fill="none" stroke={C.red} strokeWidth={6} strokeLinecap="round" opacity={rOp} />
        <path d={curvePath(p50l)} fill="none" stroke={C.blue} strokeWidth={6} strokeLinecap="round" opacity={lOp} />
        <path d={curvePath(P50N)} fill="none" stroke={C.ink} strokeWidth={6} strokeLinecap="round" pathLength={1} strokeDasharray={`${drawK} 1`} opacity={drawK > 0 ? 1 : 0} />
        {/* landmark dots */}
        <circle cx={X(100)} cy={Y(sat(100, P50N))} r={10} fill={C.oxy} stroke={C.card} strokeWidth={3} opacity={A} />
        <circle cx={X(40)} cy={Y(sat(40, P50N))} r={10} fill={C.deoxy} stroke={C.card} strokeWidth={3} opacity={B} />
        {p50Line(P50N, C.ink, p50Op * ss(T.p50 + 0.6, T.p50 + 1.0, t), '')}
        {/* released comparison dots */}
        <g opacity={relOp}>
          <circle cx={X(40)} cy={Y(sat(40, P50N))} r={9} fill={C.ink} stroke={C.card} strokeWidth={3} />
          <circle cx={X(40)} cy={Y(sat(40, P50R))} r={9} fill={C.red} stroke={C.card} strokeWidth={3} />
        </g>
        {/* shape markers + axis highlight bars */}
        <g opacity={m1Op}>
          <rect x={PL - 6} y={Y(sat(100, P50N))} width={12} height={Y(sat(p1, P50N)) - Y(sat(100, P50N))} rx={6} fill={C.red} />
          <rect x={X(p1)} y={PB - 6} width={X(100) - X(p1)} height={12} rx={6} fill={C.ink} />
          <line x1={PL} y1={Y(sat(p1, P50N))} x2={X(p1)} y2={Y(sat(p1, P50N))} stroke={C.ink} strokeWidth={2} strokeDasharray={dash} />
          <circle cx={X(p1)} cy={Y(sat(p1, P50N))} r={11} fill={C.ink} stroke={C.card} strokeWidth={3} />
        </g>
        <g opacity={m2Op}>
          <rect x={PL - 6} y={Y(sat(40, P50N))} width={12} height={Y(sat(p2, P50N)) - Y(sat(40, P50N))} rx={6} fill={C.red} />
          <rect x={X(p2)} y={PB - 6} width={X(40) - X(p2)} height={12} rx={6} fill={C.ink} />
          <line x1={PL} y1={Y(sat(p2, P50N))} x2={X(p2)} y2={Y(sat(p2, P50N))} stroke={C.ink} strokeWidth={2} strokeDasharray={dash} />
          <circle cx={X(p2)} cy={Y(sat(p2, P50N))} r={11} fill={C.ink} stroke={C.card} strokeWidth={3} />
        </g>
      </svg>
      {/* tick labels */}
      {ticks.map((v) => <Tag key={'lx' + v} x={X(v)} y={PB + 36} op={ss(T.axesX + v / 120, T.axesX + v / 120 + 0.3, t)} bg="transparent" size={26} weight={500} pad="0" style={{boxShadow: 'none'}}>{v}</Tag>)}
      {ticks.map((v) => <Tag key={'ly' + v} x={PL - 22} y={Y(v)} ax={1} op={ss(T.yAx + v / 120, T.yAx + v / 120 + 0.3, t)} bg="transparent" size={26} weight={500} pad="0" style={{boxShadow: 'none'}}>{v}</Tag>)}
      <Tag x={X(50)} y={PB + 92} k={spr(t, T.xTitle - 0.2)} bg="transparent" size={32} weight={700} pad="0" style={{boxShadow: 'none'}}><Rich t="PO2 (mmHg)" /></Tag>
      <div style={{position: 'absolute', left: PL - 108, top: Y(50), transform: `translate(-50%,-50%) rotate(-90deg)`, opacity: ss(T.yTitle - 0.2, T.yTitle + 0.5, t), fontSize: 32, fontWeight: 700, whiteSpace: 'nowrap', color: C.ink}}>
        <Rich t="Hemoglobin O2 saturation (%)" />
      </div>
      {/* sigmoid label */}
      <Tag x={X(45)} y={Y(42)} ax={0} k={spr(t, T.sig)} op={1 - ss(T.lm - 0.3, T.lm + 0.2, t)} fg={C.ink} size={28} weight={700}>Sigmoid (S-shaped)</Tag>
      <Tag x={X(62)} y={Y(52)} ax={0} op={straightOp * (1 - drawK)} bg="transparent" fg={C.ink2} size={26} pad="0" style={{boxShadow: 'none'}}>not a straight line</Tag>
      {/* landmark tags */}
      <Tag x={X(100) + 14} y={Y(sat(100, P50N))} ax={0} op={A} fg={C.oxy} size={26} weight={700} pad="6px 14px">Lungs</Tag>
      <Tag x={X(40) + 18} y={Y(sat(40, P50N)) + 14} ax={0} ay={0} op={B} fg={C.deoxy} size={26} weight={700} pad="6px 14px">Resting tissue</Tag>
      <Tag x={X(76)} y={Y(84)} op={Q} bg="transparent" fg={C.red} size={28} weight={700} pad="0" style={{boxShadow: 'none'}}>≈ 25% unloaded</Tag>
      {/* P50 tags */}
      <Tag x={X(P50N) + 16} y={Y(50) + 14} ax={0} ay={0} k={spr(t, T.p50def - 0.2)} op={p50Op * (1 - ss(T.right - 0.3, T.right + 0.3, t))} fg={C.ink} size={28} weight={700} pad="6px 14px"><Rich t="P50" /></Tag>
      <Tag x={X(P50N) + 8} y={PB - 10} ax={0} ay={1} k={spr(t, T.p50val - 0.3)} op={p50Op} bg="transparent" fg={C.ink} size={24} weight={700} pad="0" style={{boxShadow: 'none'}}>26.8</Tag>
      <Tag x={X(p50r) + 8} y={PB - 10} ax={0} ay={1} op={rOp * ss(T.rightP50 - 0.2, T.rightP50 + 0.5, t)} bg="transparent" fg={C.red} size={24} weight={700} pad="0" style={{boxShadow: 'none'}}>{p50r.toFixed(0)}</Tag>
      <Tag x={X(p50l) - 8} y={PB - 10} ax={1} ay={1} op={lOp * ss(T.leftP50 - 0.2, T.leftP50 + 0.5, t)} bg="transparent" fg={C.blue} size={24} weight={700} pad="0" style={{boxShadow: 'none'}}>{p50l.toFixed(0)}</Tag>
      {/* shape-section labels */}
      <Tag x={X(80)} y={Y(42)} op={plateauBand} bg="transparent" fg={C.ink2} size={28} weight={700} pad="0" style={{boxShadow: 'none'}}>Flat top</Tag>
      <Tag x={X(46)} y={Y(18)} op={steepBand} bg="transparent" fg={C.ink2} size={28} weight={700} pad="0" style={{boxShadow: 'none'}}>Steep middle</Tag>
      {/* factor lists, placed like the reference graph */}
      <FactorList t={t} x={X(57)} y={Y(57)} color={C.red} op={rDim} items={[['down', 'pH', T.f1], ['up', 'CO2', T.f2], ['up', '2,3-DPG', T.f3], ['up', 'Temp', T.f4]]} bohr={T.bohr} />
      <FactorList t={t} x={X(2.5)} y={Y(97)} color={C.blue} op={1} items={[['up', 'pH', T.g1], ['down', 'CO2', T.g2], ['down', '2,3-DPG', T.g3], ['down', 'Temp', T.g4]]} />
    </>);
};

const FactorList: React.FC<{t: number; x: number; y: number; color: string; op: number; items: [string, string, number][]; bohr?: number}> = ({t, x, y, color, op, items, bohr}) => {
  const bK = bohr ? spr(t, bohr - 0.2) : 0;
  return (<>
    {items.map(([dir, label, at], i) => (
      <Tag key={label} x={x} y={y + i * 54} ax={0} ay={0} k={spr(t, at - 0.15)} op={op} bg="transparent" fg={color} size={34} weight={700} pad="0 4px" style={{boxShadow: 'none'}}>
        <Arrow up={dir === 'up'} color={color} size={30} /><Rich t={label} />
      </Tag>))}
    {bohr && <>
      <svg width={1920} height={1080} style={{position: 'absolute', opacity: clamp(bK) * op}}>
        <path d={`M${x + 150} ${y + 6} h14 v${54 + 36} h-14`} fill="none" stroke={color} strokeWidth={3} strokeLinecap="round" />
      </svg>
      <Tag x={x + 182} y={y + 48} ax={0} k={bK} op={op} bg={C.redSoft} fg={color} size={26} weight={700} pad="6px 14px">Bohr effect</Tag>
    </>}
  </>);
};

// ---------- side panel ----------
const Panel: React.FC<{t: number}> = ({t}) => {
  const k = (a: number) => spr(t, a - 0.1);
  const hbOp = win(t, T.hb - 0.3, T.lm - 0.1, 0.5, 0.5);
  const tState = 1 - ss(T.shape, T.shape + 0.8, t);
  const lmOp = win(t, T.lung - 0.2, T.p50 - 0.1, 0.4, 0.5);
  const p50Op = win(t, T.p50 - 0.1, T.shapeS - 0.1, 0.4, 0.5);
  const flatOp = win(t, T.flat - 0.2, T.shift - 0.1, 0.4, 0.5);
  const s1a = ss(T.slide1, T.slide1 + 1.8, t), s2a = ss(T.slide2, T.slide2 + 1.4, t);
  const shiftOp = win(t, T.shift - 0.1, T.right - 0.1, 0.4, 0.5);
  const rightOp = win(t, T.right - 0.1, T.left - 0.1, 0.4, 0.5);
  const leftOp = win(t, T.left - 0.1, T.sum - 0.1, 0.4, 0.5);
  const sumOp = ss(T.sum - 0.1, T.sum + 0.4, t);
  const noteOp = ss(T.right + 1.5, T.right + 2.2, t) * (1 - ss(T.sum - 0.3, T.sum + 0.2, t)) + ss(T.rmr + 1.5, T.rmr + 2.2, t);
  const pct = (v: number) => Math.round(v) + '%';
  return (<>
    {/* hemoglobin */}
    <div style={{opacity: hbOp}}>
      <Tag x={PX + PW / 2} y={160} k={k(T.hb)} bg="transparent" size={38} weight={700} pad="0" style={{boxShadow: 'none'}}>Hemoglobin</Tag>
      <Tag x={PX + PW / 2} y={204} k={k(T.sub)} bg="transparent" fg={C.ink2} size={27} weight={500} pad="0" style={{boxShadow: 'none'}}>2 α + 2 β globin chains, each with a heme</Tag>
      <Tetramer t={t} />
      <Tag x={PX + PW / 2} y={702} k={k(T.heme)} fg={C.heme} size={26} weight={700}><Rich t="Heme iron (Fe2+) binds one O2" /></Tag>
      <Tag x={PX + PW / 2} y={764} k={k(T.coop)} op={tState} fg={C.ink} border={C.line} size={26} weight={500}><b>T state</b> · tense · low affinity</Tag>
      <Tag x={PX + PW / 2} y={764} k={k(T.shape)} op={1 - tState} fg={C.ink} border={C.ink} size={26} weight={500}><b>R state</b> · relaxed · high affinity</Tag>
      <Tag x={PX + PW / 2} y={824} k={k(T.coop)} bg={C.ink} fg={C.card} size={28} weight={700}>Positive cooperativity</Tag>
      <Tag x={PX + PW / 2} y={874} op={ss(T.hb + 1, T.hb + 1.6, t)} bg="transparent" fg={C.mute} size={22} weight={500} pad="0" style={{boxShadow: 'none'}}>Schematic, not to scale</Tag>
    </div>
    {/* landmarks */}
    <Card y={150} op={lmOp} k={k(T.lung)} accent={C.oxy} title="Lungs" lines={[<Rich t="PO2 ≈ 100 mmHg" />, 'Saturation ≈ 97%']} />
    <Card y={340} op={lmOp} k={k(T.tis)} accent={C.deoxy} title="Resting tissue" lines={[<Rich t="PO2 ≈ 40 mmHg" />, 'Saturation ≈ 75%']} />
    <Card y={530} op={lmOp} k={k(T.quarter)} accent={C.red} title="At rest" lines={[<Rich t="About 1/4 of the O2 is unloaded" />]} />
    {/* P50 */}
    <Card y={150} op={p50Op} k={k(T.p50)} accent={C.ink} title={<Rich t="P50" />} lines={[<Rich t="The PO2 at 50% saturation" />]} />
    <Card y={330} op={p50Op} k={k(T.p50val - 0.4)} accent={C.ink} title="Healthy adult" lines={[<Rich t="P50 ≈ 26.8 mmHg" />]} />
    {/* shape */}
    <Card y={150} op={flatOp} k={k(T.flat)} accent={C.ink} title="Flat top: loading" lines={[<Rich t={`PO2 100 → ${Math.round(lerp(100, 60, s1a))} mmHg`} />, `Saturation 97% → ${pct(sat(lerp(100, 60, s1a), P50N))}`, <Rich t="A big drop in PO2, a small loss" />]} />
    <Card y={420} op={flatOp} k={k(T.steep)} accent={C.red} title="Steep middle: unloading" lines={[<Rich t={`PO2 40 → ${Math.round(lerp(40, 30, s2a))} mmHg`} />, `Saturation 75% → ${pct(sat(lerp(40, 30, s2a), P50N))}`, <Rich t="A small drop in PO2, a large release" />]} />
    {/* shifts */}
    <Card y={150} op={shiftOp} k={k(T.shift)} accent={C.ink} title={<Rich t="Shifts move the P50" />} lines={[<Rich t="P50 tells you how tightly hemoglobin holds O2" />]} small />
    <Card y={150} op={rightOp} k={k(T.right)} accent={C.red} title="Right shift" lines={[<span><Arrow up={false} color={C.red} size={24} />affinity for O<sub style={{fontSize: '0.62em'}}>2</sub></span>, <span><Arrow up color={C.red} size={24} /><Rich t="P50 (26.8 → 36*)" /></span>, <Rich t="O2 unloads more easily" />]} />
    <Card y={420} op={rightOp} k={k(T.muscle)} accent={C.red} title="Exercising muscle" lines={[<Rich t="Warm · acidic · high CO2" />, <span style={{opacity: ss(T.released - 0.2, T.released + 0.5, t)}}><Rich t="At PO2 40: 75% → 57% saturated" /></span>]} small />
    <Card y={150} op={leftOp} k={k(T.left)} accent={C.blue} title="Left shift" lines={[<span><Arrow up color={C.blue} size={24} />affinity for O<sub style={{fontSize: '0.62em'}}>2</sub></span>, <span><Arrow up={false} color={C.blue} size={24} /><Rich t="P50 (26.8 → 20*)" /></span>, <Rich t="O2 held more tightly" />]} />
    <Card y={420} op={leftOp} k={k(T.fetal)} accent={C.blue} title="Fetal hemoglobin (HbF)" lines={['2 α + 2 γ chains', 'γ chains bind 2,3-DPG poorly', <Rich t="Pulls O2 from maternal blood" />]} small />
    <Card y={652} op={leftOp} k={k(T.co)} accent={C.blue} title="Carbon monoxide" lines={[<Rich t="Binds Hb 200–300× more than O2" />, <Rich t="Left shift and less O2 carried" />]} small />
    {/* summary */}
    <Card y={150} op={sumOp} k={k(T.sr)} accent={C.red} title="Right shift" lines={[<span><Arrow up={false} color={C.red} size={24} />affinity  ·  <Arrow up color={C.red} size={24} /><Rich t="P50" /></span>, <Rich t="More O2 released" />]} />
    <Card y={370} op={sumOp} k={k(T.sl)} accent={C.blue} title="Left shift" lines={[<span><Arrow up color={C.blue} size={24} />affinity  ·  <Arrow up={false} color={C.blue} size={24} /><Rich t="P50" /></span>, <Rich t="O2 held more tightly" />]} />
    <Tag x={PX + PW / 2} y={640} k={spr(t, T.rmr - 0.1, {damping: 11})} op={sumOp} bg={C.red} fg={C.card} size={44} weight={700} pad="18px 34px" radius={16}>Right means release</Tag>
    {/* footnotes */}
    <div style={{position: 'absolute', left: PX, top: lerp(880, 740, sumOp), width: PW, fontSize: 19, lineHeight: 1.4, color: C.ink2, opacity: noteOp}}>
      <Rich t={`*Shifted curves are illustrative. Curves plotted with the Hill equation (n = ${N}).`} />
      <div style={{opacity: ss(T.rmr + 1.5, T.rmr + 2.2, t)}}>Source: Patel S, Jose A, Mohiuddin SS. Physiology, Oxygen Transport and Carbon Dioxide Dissociation Curve. StatPearls, 2023.</div>
    </div>
  </>);
};

const Title: React.FC<{t: number}> = ({t}) => {
  const titleK = ss(T.axesX - 1.0, T.axesX - 0.1, t);
  return (
    <div style={{position: 'absolute', left: lerp(960, 80, titleK), top: lerp(500, 58, titleK), transform: `translate(${-50 * (1 - titleK)}%, -50%)`,
      fontSize: lerp(78, 26, titleK), fontWeight: lerp(700, 500, titleK), color: titleK > 0.5 ? C.ink2 : C.ink, whiteSpace: 'nowrap', letterSpacing: lerp(-1, 0, titleK),
      opacity: ss(T.title - 0.1, T.title + 0.5, t)}}>
      The Oxyhemoglobin Dissociation Curve
    </div>
  );
};

const Captions: React.FC<{t: number}> = ({t}) => {
  const s = SENT.find((x) => t >= x.s - 0.1 && t <= x.e + 0.35);
  if (!s) return null;
  const op = Math.min(ss(s.s - 0.1, s.s + 0.1, t), 1 - ss(s.e + 0.15, s.e + 0.35, t));
  return (
    <div style={{position: 'absolute', left: 160, right: 160, top: 1018, transform: 'translateY(-50%)', textAlign: 'center', fontSize: 27, color: C.ink2, opacity: op, lineHeight: 1.3}}>
      <Rich t={s.text} />
    </div>);
};

export const Main: React.FC = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = f / fps;
  const graphOp = ss(T.axesX - 0.8, T.axesX - 0.1, t);
  return (
    <AbsoluteFill style={{background: C.bg, fontFamily, color: C.ink}}>
      <Audio src={staticFile('vo_timed.wav')} />
      <Audio src={staticFile('sfx_logo.wav')} />
      {t < T.axesX + 1 && <Intro t={t} />}
      {t > T.axesX - 1 && <AbsoluteFill style={{opacity: graphOp}}><Graph t={t} /><Panel t={t} /></AbsoluteFill>}
      <Title t={t} />
      <Captions t={t} />
    </AbsoluteFill>);
};
