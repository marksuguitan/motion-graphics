import React from 'react';
// Ribbon-style hemoglobin tetramer: each subunit is a globin chain drawn as a continuous tube
// (the globin fold, simplified) cradling one heme. alpha chains in the project red, beta in purple-blue.

export const CHAIN = {
  alpha: {body: '#E0907F', edge: '#A9564A', sheen: '#F8D6CD'},
  beta: {body: '#8B8BD8', edge: '#4F4FA3', sheen: '#DCDCF7'},
};
const HEME = '#7E2A27', FE = '#B23A30', PAPER = '#FBF8F2';

// control points of one globin chain (local coords): an outer loop, a diagonal crossing, and an inner curl
// that cradles the heme. Drawn as two strands so the second passes over the first.
const PTS: [number, number][] = [[90, -80], [30, -98], [-45, -85], [-92, -35], [-88, 35], [-45, 82], [25, 90], [78, 52], [70, -5], [15, -35], [-50, -5], [-35, 50], [25, 40], [40, -25], [5, -70], [-40, -110]];
const K = 9; // split index between back and front strand
export const HEME_POS: [number, number] = [8, 12];

const strands = (() => {
  const P = PTS, c: string[] = [];
  for (let i = 0; i < P.length - 1; i++) {
    const p0 = P[i - 1] || P[i], p1 = P[i], p2 = P[i + 1], p3 = P[i + 2] || P[i + 1];
    const c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
    const c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
    c.push(`C${c1[0].toFixed(1)},${c1[1].toFixed(1)} ${c2[0].toFixed(1)},${c2[1].toFixed(1)} ${p2[0]},${p2[1]}`);
  }
  return [`M${P[0][0]},${P[0][1]} ` + c.slice(0, K).join(' '), `M${P[K][0]},${P[K][1]} ` + c.slice(K).join(' ')];
})();

const W_EDGE = 22, W_BODY = 16, W_SHEEN = 6;

export const Chain: React.FC<{kind: 'alpha' | 'beta'}> = ({kind}) => {
  const c = CHAIN[kind];
  const ends = [PTS[0], PTS[PTS.length - 1]];
  return (
    <g>
      {strands.map((d, i) => (
        <g key={i}>
          <circle cx={ends[i][0]} cy={ends[i][1]} r={W_EDGE / 2} fill={c.edge} />
          <path d={d} fill="none" stroke={c.edge} strokeWidth={W_EDGE} />
          <circle cx={ends[i][0]} cy={ends[i][1]} r={W_BODY / 2} fill={c.body} />
          <path d={d} fill="none" stroke={c.body} strokeWidth={W_BODY} />
          <path d={d} fill="none" stroke={c.sheen} strokeWidth={W_SHEEN} opacity={0.6} transform="translate(-1.5,-2.5)" />
        </g>))}
    </g>);
};

// simplified porphyrin ring: macrocycle, four pyrroles, central Fe2+ bonded to four N
export const Heme: React.FC<{x: number; y: number; s?: number; op?: number}> = ({x, y, s = 1, op = 1}) => {
  const pent = (a: number) => {
    const cx = Math.cos(a) * 20, cy = Math.sin(a) * 20;
    let d = '';
    for (let k = 0; k < 5; k++) {
      const b = a + Math.PI + (k * 2 * Math.PI) / 5;
      d += (k ? 'L' : 'M') + (cx + Math.cos(b) * 8).toFixed(1) + ',' + (cy + Math.sin(b) * 8).toFixed(1);
    }
    return d + 'Z';
  };
  const A = [0, Math.PI / 2, Math.PI, (3 * Math.PI) / 2].map((a) => a + Math.PI / 4);
  return (
    <g transform={`translate(${x},${y}) scale(${s})`} opacity={op}>
      <circle r={29} fill={PAPER} opacity={0.94} />
      <circle r={21} fill="none" stroke={HEME} strokeWidth={2.4} />
      {A.map((a, i) => <path key={i} d={pent(a)} fill={PAPER} stroke={HEME} strokeWidth={2.2} strokeLinejoin="round" />)}
      {A.map((a, i) => <line key={'b' + i} x1={0} y1={0} x2={Math.cos(a) * 13} y2={Math.sin(a) * 13} stroke={HEME} strokeWidth={2} />)}
      <circle r={6.5} fill={FE} stroke={PAPER} strokeWidth={1.5} />
    </g>);
};
