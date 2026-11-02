import React from 'react';
import {staticFile} from 'remotion';
import {T} from './theme';

export const clamp = (v: number, a = 0, b = 1) => Math.max(a, Math.min(b, v));
export const easeIO = (p: number) => (p < 0.5 ? 4 * p * p * p : 1 - (-2 * p + 2) ** 3 / 2);
export const easeOut = (p: number) => 1 - (1 - p) ** 3;
export const ramp = (t: number, a: number, b: number, ease = easeIO) => ease(clamp((t - a) / (b - a)));
export const lerp = (a: number, b: number, k: number) => a + (b - a) * k;

// enter: rise + fade with a gentle overshoot-free settle; exit: quick fade and lift
export function appear(t: number, tin: number, tout = 1e9, rise = 22) {
  const p = clamp((t - tin) / 0.5), e = 1 - (1 - p) ** 4;
  const q = clamp((t - tout) / 0.3);
  return {o: clamp(p * 2.4) * (1 - q), dy: rise * (1 - e) - 12 * easeIO(q), live: t >= tin - 0.01 && t <= tout + 0.31};
}

export const At: React.FC<{t: number; tin: number; tout?: number; x: number; y: number; w?: number; rise?: number; style?: React.CSSProperties; children: React.ReactNode}> = ({t, tin, tout, x, y, w, rise, style, children}) => {
  const a = appear(t, tin, tout, rise);
  if (!a.live) return null;
  return <div style={{position: 'absolute', left: x, top: y, width: w, opacity: a.o, transform: `translateY(${a.dy}px)`, ...style}}>{children}</div>;
};

export type ChipKind = '' | 'amber' | 'teal' | 'coral' | 'ink';
const CHIP: Record<string, React.CSSProperties> = {
  '': {background: T.card, borderColor: T.line, color: T.ink},
  amber: {background: T.amberSoft, borderColor: T.amberLine, color: T.amberInk},
  teal: {background: T.tealSoft, borderColor: T.tealLine, color: T.tealInk},
  coral: {background: T.coralSoft, borderColor: T.coralLine, color: T.coralInk},
  ink: {background: T.ink, borderColor: T.ink, color: T.bg},
};
export const Chip: React.FC<{kind?: ChipKind; children: React.ReactNode; size?: number}> = ({kind = '', children, size = 28}) => (
  <span style={{display: 'inline-flex', alignItems: 'center', gap: 12, padding: `${Math.round(size * 0.43)}px ${Math.round(size * 0.8)}px`, borderRadius: 999, fontWeight: 500, fontSize: size, lineHeight: 1.2, whiteSpace: 'nowrap', border: '1.5px solid', ...CHIP[kind]}}>{children}</span>
);
export const Sub: React.FC<{children: React.ReactNode}> = ({children}) => <span style={{fontWeight: 400, color: T.ink2}}>{children}</span>;

export const S = {
  h1: {fontWeight: 700, fontSize: 92, lineHeight: 1.02, letterSpacing: '-0.02em'} as React.CSSProperties,
  h2: {fontWeight: 700, fontSize: 56, lineHeight: 1.08, letterSpacing: '-0.015em'} as React.CSSProperties,
  h3: {fontWeight: 700, fontSize: 38, lineHeight: 1.15, letterSpacing: '-0.01em'} as React.CSSProperties,
  lead: {fontWeight: 400, fontSize: 34, lineHeight: 1.3, color: T.ink2} as React.CSSProperties,
  eyebrow: {fontWeight: 700, fontSize: 22, letterSpacing: '0.12em', textTransform: 'uppercase', color: T.ink2} as React.CSSProperties,
};

export const FontFaces: React.FC = () => (
  <style>{[400, 500, 700].map(w => `@font-face{font-family:"DM Sans";font-weight:${w};src:url(${staticFile(`dmsans-${w}.woff2`)}) format("woff2")}`).join('')}</style>
);
