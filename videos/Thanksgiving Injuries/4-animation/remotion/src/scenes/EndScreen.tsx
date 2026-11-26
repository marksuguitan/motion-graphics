// EndScreen.tsx: the house end screen, layout B (Oxygen Hemoglobin Curve 3-board/style/endscreen_spec.md), 15 s.
// The dashed plates are where YouTube's end-screen elements go. No sounds here.
import React from 'react';
import {C, FONT} from '../style/theme';
import {overshoot, progress} from '../style/comma';
import {TL} from '../lib/tl';

const ES = TL.endScreen.start;
const MARK = [
  '144.1,160.4 127.4,160.4 120.0,173.8 151.9,173.8 160.4,158.6 179.6,189.0 186.9,175.6 159.7,132.3',
  '226.2,146.1 207.6,115.2 191.1,144.0 170.9,112.0 163.6,125.6 191.6,170.0 207.9,141.7 218.6,159.5 233.3,159.5 240.0,146.1',
];
export const TAKEAWAY = 'Knives, hot oil, big bites, food left out, one more round.';

export const EndScreen: React.FC<{t: number}> = ({t}) => {
  const u = t - ES;
  if (u < 0.25) return null;
  const mk = u < 0.45 ? 0 : overshoot(u, 0.45, 0.5, 0, 1, 0.06);
  const circ = progress(u, 0.6, 0.5, 'snap');
  const L = 2 * Math.PI * 90;
  const plate = (i: number) => (u < 0.8 + i * 0.1 ? 0 : overshoot(u, 0.8 + i * 0.1, 0.6, 0, 1, 0.06));
  const dash = {fill: C.soft, stroke: C.inactive, strokeWidth: 3, strokeDasharray: '14 10'};
  return (
    <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0}}>
      <rect width={1920} height={1080} fill={C.soft} />
      <defs>
        <mask id="circTrace">
          <circle cx={1700} cy={160} r={90} fill="none" stroke="#fff" strokeWidth={12} strokeDasharray={`${circ * L} ${L}`} transform="rotate(-90 1700 160)" />
        </mask>
      </defs>
      {mk > 0 ? (
        <g transform={`translate(180 150) scale(${mk}) translate(-180 -150)`}>
          {MARK.map((p, i) => <polygon key={i} points={p} fill={C.ink} />)}
        </g>
      ) : null}
      {u >= 0.55 ? <text x={280} y={150} fontFamily={FONT.head} fontSize={52} fontWeight={600} fill={C.ink}>Thanks for watching</text> : null}
      {u >= 0.55 + 0.1 ? <text x={282} y={200} fontFamily={FONT.body} fontSize={28} fill={C.ink2}>{TAKEAWAY}</text> : null}
      {circ > 0 ? <circle cx={1700} cy={160} r={90} {...dash} mask="url(#circTrace)" /> : null}
      {u >= 1.1 ? <text x={1700} y={170} textAnchor="middle" fontFamily={FONT.head} fontSize={26} fontWeight={600} fill={C.ink2}>Subscribe</text> : null}
      {u >= 0.75 ? (
        <g fontFamily={FONT.head} fontSize={23} fontWeight={700} letterSpacing={3} fill={C.ink2}>
          <text x={120} y={356}>WATCH NEXT</text>
          <text x={1000} y={356}>RECOMMENDED</text>
        </g>
      ) : null}
      {[120, 1000].map((x, i) => {
        const k = plate(i);
        if (k <= 0) return null;
        const cx = x + 400;
        return (
          <g key={i} transform={`translate(${cx} 615) scale(${k}) translate(${-cx} -615)`}>
            <rect x={x} y={390} width={800} height={450} rx={16} {...dash} />
          </g>
        );
      })}
    </svg>
  );
};
