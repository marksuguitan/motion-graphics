import React from 'react';
import {PXS, PXMV, strip} from './ecg';
import {T} from './theme';
import {clamp} from './ui';

export type Marker = {kind: 'P' | 'noP' | 'bracket' | 'tick' | 'lap'; t: number; t2?: number; text?: string; color?: string; anchor?: 'start' | 'end' | 'middle'; dx?: number; showAt?: number};

// A monitor strip: the trace prints from the left at 25 mm/s, then the paper scrolls.
// The path is built once on a fixed time grid and only translated, so nothing re-samples or jitters.
export const StripCard: React.FC<{id: string; t: number; t0: number; name: string; w: number; h: number; baseline?: number; label?: string; rate?: number; markers?: Marker[]; dim?: number; head?: boolean}> = ({id, t, t0, name, w, h, baseline = 0.62, label, rate, markers = [], dim = 0, head = true}) => {
  const s = strip(name);
  const HB = label || rate ? 56 : 0;
  const by = HB + (h - HB) * baseline;
  const H = Math.max(0, t - t0);                 // strip time printed so far
  const win = w / PXS;
  const off = Math.max(0, H - win + 0.04);       // paper scroll, in seconds
  const x0 = -off * PXS;
  const px = (H - off) * PXS;                    // print head x
  const small = PXS / 25, big = small * 5;
  const vis = (m: Marker) => {
    if (m.t > H) return 0;
    const a = clamp((H - m.t) / 0.25);
    const b = m.showAt === undefined ? 1 : clamp((t - m.showAt) / 0.35);
    return Math.min(a, b);
  };
  const mk = markers.map((m, i) => {
    const x = (m.t - off) * PXS; const o = vis(m);
    if (o <= 0 || x < -40 || x > w + 40) return null;
    const pY = by - 0.16 * PXMV;
    if (m.kind === 'P') return <text key={i} x={x} y={pY - 14} opacity={o} textAnchor="middle" fontWeight={700} fontSize={22} fill={T.teal}>P</text>;
    if (m.kind === 'noP') return <g key={i} opacity={o}><circle cx={x} cy={pY - 20} r={12} fill="none" stroke={T.coral} strokeWidth={2.5} /><line x1={x - 8} y1={pY - 12} x2={x + 8} y2={pY - 28} stroke={T.coral} strokeWidth={2.5} /></g>;
    if (m.kind === 'bracket') { const x2 = (m.t2! - off) * PXS, y = by + 0.42 * PXMV; return <g key={i} opacity={o}><path d={`M${x} ${y - 10}v10h${x2 - x}v-10`} stroke={m.color || T.amber} strokeWidth={3} fill="none" /><text x={(x + x2) / 2} y={y + 30} textAnchor="middle" fontWeight={500} fontSize={22} fill={m.color || T.amber}>{m.text}</text></g>; }
    if (m.kind === 'tick') return <g key={i} opacity={o}><line x1={x} y1={by - 1.55 * PXMV} x2={x} y2={by + 0.85 * PXMV} stroke={m.color || T.coral} strokeWidth={3} strokeDasharray="8 8" />{m.text && <text x={x + (m.dx ?? 12)} y={by + 0.78 * PXMV} fontWeight={700} fontSize={22} fill={m.color || T.coral} textAnchor={m.anchor || 'start'}>{m.text}</text>}</g>;
    if (m.kind === 'lap') return <circle key={i} opacity={o} cx={x} cy={by + 0.62 * PXMV} r={8} fill={T.amber} />;
    return null;
  });
  const hv = s.v(H);
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{display: 'block', fontFamily: T.font, overflow: 'visible'}}>
      <defs>
        <pattern id={`${id}-g1`} width={small} height={small} patternUnits="userSpaceOnUse" x={x0 % small}><path d={`M${small} 0H0V${small}`} fill="none" stroke={T.grid} strokeWidth={1} /></pattern>
        <pattern id={`${id}-g5`} width={big} height={big} patternUnits="userSpaceOnUse" x={x0 % big} y={by % big - big}><rect width={big} height={big} fill={`url(#${id}-g1)`} /><path d={`M${big} 0H0V${big}`} fill="none" stroke={T.gridBig} strokeWidth={1.2} /></pattern>
        <clipPath id={`${id}-clip`}><rect width={w} height={h} rx={18} /></clipPath>
        <clipPath id={`${id}-print`}><rect x={-10} y={0} width={Math.max(0, px + 10)} height={h} /></clipPath>
        <linearGradient id={`${id}-fade`} x1="0" x2="1"><stop offset="0" stopColor={T.card} stopOpacity="0" /><stop offset="1" stopColor={T.card} stopOpacity="0.0" /></linearGradient>
      </defs>
      <rect width={w} height={h} rx={18} fill={T.card} stroke={T.line} strokeWidth={1.5} />
      <g clipPath={`url(#${id}-clip)`}>
        <rect x={0} y={HB} width={w} height={h - HB} fill={`url(#${id}-g5)`} />
        <g clipPath={`url(#${id}-print)`} opacity={1 - 0.65 * dim}>
          <path d={s.d} transform={`translate(${x0} ${by})`} fill="none" stroke={T.ink} strokeWidth={3.2} strokeLinejoin="round" strokeLinecap="round" />
        </g>
        {head && H > 0 && px <= w + 1 && <circle cx={px} cy={by - hv * PXMV} r={6} fill={T.ink} opacity={0.9 * (1 - dim)} />}
        <g opacity={1 - 0.65 * dim}>{mk}</g>
      </g>
      {HB > 0 && (
        <g>
          <path d={`M18 0H${w - 18}A18 18 0 0 1 ${w} 18V${HB}H0V18A18 18 0 0 1 18 0Z`} fill={T.card} />
          <line x1={0} y1={HB} x2={w} y2={HB} stroke={T.line} strokeWidth={1.5} />
          <rect width={w} height={h} rx={18} fill="none" stroke={T.line} strokeWidth={1.5} />
          {label && <text x={26} y={36} fontSize={22} fontWeight={500} fill={T.ink2}>{label}</text>}
          {rate && <text x={w - 26} y={40} textAnchor="end" fontSize={32} fontWeight={700} fill={T.ink}>{H > 1.2 ? rate : '– –'}<tspan fontSize={20} fontWeight={500} fill={T.ink2}> /min</tspan></text>}
        </g>
      )}
    </svg>
  );
};
