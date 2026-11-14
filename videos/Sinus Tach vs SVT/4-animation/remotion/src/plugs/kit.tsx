// kit.tsx: shared pieces for the two Kardiograph plugs (opener and end plug) cut into the finished v8.
// Look: Comma Clinical type and soft geometry on v8's own warm-paper ground, so the cuts in and out are seamless.
// Every ECG strip is lead II from Kardiograph's engine (3-board/kardiograph-plug/export_strips.ts).
import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import strips from '../data/kardiograph-strips.json';
import {C, FONT, SHADOW} from '../style/theme';

export const BG = '#F5EFE8'; // v8's ground, sampled from its frames
export const CORAL = '#E0574F'; // Kardiograph's brand coral (kardiograph public/learn/learn.css)
export const CORAL_SOFT = '#FCEBEA';

/** Plug time in seconds from its first frame. */
export const useT = () => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  return f / fps;
};

type Strip = {fs: number; mv: number[]};
const S = strips as unknown as Record<string, Strip>;

const WAVE = 'M2 12h3l2-6 3 12 3-9 2 3h7';
export const ICON = {
  book: ['M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z', 'M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z'],
  clipboard: ['M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2', 'm9 14 2 2 4-4', 'M9 2h6a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z'],
  rotate: ['M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8', 'M3 3v5h5'],
};

export const Icon: React.FC<{d: string[]; size: number; color: string; sw?: number}> = ({d, size, color, sw = 2}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={sw} strokeLinecap="round" strokeLinejoin="round">
    {d.map((p) => (
      <path key={p} d={p} />
    ))}
  </svg>
);

/** The Kardiograph mark: a coral rounded square with the white wave. */
export const Mark: React.FC<{size: number}> = ({size}) => (
  <div style={{width: size, height: size, borderRadius: size * 0.25, background: CORAL, display: 'grid', placeItems: 'center'}}>
    <svg width={size * 0.62} height={size * 0.62} viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth={2.4} strokeLinecap="round" strokeLinejoin="round">
      <path d={WAVE} />
    </svg>
  </div>
);

export const kicker: React.CSSProperties = {fontFamily: FONT.head, fontWeight: 700, fontSize: 24, letterSpacing: '0.14em', textTransform: 'uppercase', color: C.ink2, whiteSpace: 'nowrap'};
export const heading: React.CSSProperties = {fontFamily: FONT.head, fontWeight: 600, fontSize: 64, letterSpacing: '-0.01em', color: C.ink, whiteSpace: 'nowrap'};
export const pill: React.CSSProperties = {fontFamily: FONT.body, fontWeight: 500, fontSize: 30, padding: '14px 30px', borderRadius: 999, border: `2px solid ${C.divider}`, background: '#fff', color: C.ink, whiteSpace: 'nowrap', display: 'inline-flex', alignItems: 'center', gap: 14};

/** The wordmark beside the mark. */
export const Wordmark: React.FC = () => (
  <div style={{whiteSpace: 'nowrap'}}>
    <div style={{fontFamily: FONT.head, fontWeight: 700, fontSize: 104, letterSpacing: '-0.02em', lineHeight: 1, color: C.ink}}>Kardiograph</div>
    <div style={{fontFamily: FONT.body, fontWeight: 500, fontSize: 34, color: C.ink2, marginTop: 12}}>by Medzcool</div>
  </div>
);

const MM = 9.6; // px per mm: 25 mm/s * 9.6 = 240 px/s
const H_MM = 30;

/**
 * A strip of lead II on true-scale paper (25 mm/s, 10 mm/mV) that scrolls: the paper and trace move left at
 * 25 mm/s from `scrollFrom` (in strip seconds). ECG traces only scroll, never jitter.
 */
export const EcgStrip: React.FC<{name: string; seconds?: number; scrollFrom?: number; children?: React.ReactNode}> = ({name, seconds = 6, scrollFrom = 0, children}) => {
  const st = S[name];
  const w = seconds * 25 * MM;
  const h = H_MM * MM;
  const base = H_MM * 0.62;
  const i0 = Math.max(0, Math.floor(scrollFrom * st.fs));
  const i1 = Math.min(st.mv.length - 1, Math.ceil((scrollFrom + seconds) * st.fs) + 1);
  const pts: string[] = [];
  for (let i = i0; i <= i1; i++) pts.push(`${((i / st.fs - scrollFrom) * 25 * MM).toFixed(1)},${((base - st.mv[i] * 10) * MM).toFixed(1)}`);
  const off = ((scrollFrom * 25) % 5) * MM; // grid moves with the paper
  const minor: string[] = [];
  const major: string[] = [];
  for (let x = 0; x <= seconds * 25 + 5; x++) (x % 5 ? minor : major).push(`M${(x * MM - off).toFixed(1)} 0V${h}`);
  for (let y = 0; y <= H_MM; y++) (y % 5 ? minor : major).push(`M0 ${y * MM}H${w}`);
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} style={{display: 'block', borderRadius: 10, overflow: 'visible'}}>
      <defs>
        <clipPath id={`paper-${name}`}>
          <rect width={w} height={h} rx={10} />
        </clipPath>
      </defs>
      <g clipPath={`url(#paper-${name})`}>
        <rect width={w} height={h} fill="#fff" />
        <path d={minor.join('')} stroke="#F6DEDB" strokeWidth={1} fill="none" />
        <path d={major.join('')} stroke="#EDBDB7" strokeWidth={1.5} fill="none" />
        <polyline points={pts.join(' ')} fill="none" stroke={C.ink} strokeWidth={3.2} strokeLinejoin="round" strokeLinecap="round" />
      </g>
      <text x={22} y={40} fontFamily="Inter" fontWeight={600} fontSize={24} fill={C.ink}>
        II
      </text>
      {children}
    </svg>
  );
};

/** R peaks of a strip (indices), for calipers. */
export function rPeaks(name: string): number[] {
  const {mv, fs} = S[name];
  const thr = 0.6 * Math.max(...mv);
  const out: number[] = [];
  for (let i = 1; i < mv.length - 1; i++) {
    if (mv[i] >= thr && mv[i] >= mv[i - 1] && mv[i] > mv[i + 1] && (!out.length || i - out[out.length - 1] > 0.2 * fs)) out.push(i);
  }
  return out;
}
export const stripFs = (name: string) => S[name].fs;
export const STRIP_PX = {mm: MM, h: H_MM * MM, base: H_MM * 0.62};

export const Card: React.FC<{children: React.ReactNode; style?: React.CSSProperties}> = ({children, style}) => (
  <div style={{padding: 20, background: C.soft, borderRadius: 24, boxShadow: SHADOW, ...style}}>{children}</div>
);
