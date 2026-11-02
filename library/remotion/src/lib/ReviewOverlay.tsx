// ReviewOverlay.tsx: burned into review renders only (render:review), never into the final.
// Mark writes notes against what it shows, e.g. "3B +1.2 s: hold the curve longer".
import React from 'react';
import {useCurrentFrame} from 'remotion';
import {beatAt, useTime} from './timing';

const tc = (t: number) => {
  const s = Math.max(0, t);
  const m = Math.floor(s / 60);
  return `${m}:${(s - m * 60).toFixed(2).padStart(5, '0')}`;
};

export const ReviewOverlay: React.FC<{label?: string}> = ({label}) => {
  const frame = useCurrentFrame();
  const t = useTime();
  const b = beatAt(t);
  const into = b ? `${b.id} +${(t - b.start).toFixed(1)} s` : 'lead-in';
  return (
    <div
      style={{
        position: 'absolute', left: 24, bottom: 20, padding: '6px 14px', borderRadius: 10,
        background: 'rgba(34,34,34,0.72)', color: '#FFFFFF', font: '500 22px Inter, sans-serif',
        fontVariantNumeric: 'tabular-nums', letterSpacing: 0.5,
      }}
    >
      {label ? `${label} · ` : ''}{into} · {tc(t)} · f{frame}
    </div>
  );
};
