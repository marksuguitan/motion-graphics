import React, {useEffect, useState} from 'react';
import {AbsoluteFill, continueRender, delayRender, staticFile} from 'remotion';
import {T} from './theme';
import {strip} from './ecg';
const F = '"Manrope", system-ui, sans-serif';
const FontFaces: React.FC = () => <style>{`@font-face{font-family:"Manrope";src:url(${staticFile('manrope-var.woff2')}) format("woff2");font-weight:200 800;font-display:block}`}</style>;
import {LoopCard} from './Loops';

const useFonts = () => {
  const [ready, setReady] = useState(false);
  const [h] = useState(() => delayRender('fonts'));
  useEffect(() => { Promise.all([400, 500, 700, 800].map(w => document.fonts.load(`${w} 30px "Manrope"`))).then(() => { setReady(true); setTimeout(() => continueRender(h), 150); }); }, [h]);
  return ready;
};

// static ECG card: `secs` of a strip, fixed time grid like the video
const MiniStrip: React.FC<{name: string; t0: number; secs: number; w: number; h: number; label: string; rate: number; color: string; pMarks?: boolean; noP?: boolean}> = ({name, t0, secs, w, h, label, rate, color, pMarks, noP}) => {
  const s = strip(name), head = 58, px = w / secs, mv = 92, by = head + (h - head) * 0.68;
  const pts: string[] = [];
  for (let t = t0; t <= t0 + secs + 1e-9; t += 0.002) pts.push(`${pts.length ? 'L' : 'M'}${((t - t0) * px).toFixed(1)} ${(by - s.v(t) * mv).toFixed(1)}`);
  const beats = s.beats.filter(b => b.t > t0 + 0.12 && b.t < t0 + secs - 0.05);
  const grid: React.ReactNode[] = [];
  for (let x = 0; x <= w; x += px * 0.2) grid.push(<line key={'x' + x} x1={x} x2={x} y1={head} y2={h} stroke={T.line} strokeWidth={1} opacity={0.55} />);
  for (let y = by; y < h; y += px * 0.2) grid.push(<line key={'y' + y} x1={0} x2={w} y1={y} y2={y} stroke={T.line} strokeWidth={1} opacity={0.55} />);
  for (let y = by - px * 0.2; y > head; y -= px * 0.2) grid.push(<line key={'z' + y} x1={0} x2={w} y1={y} y2={y} stroke={T.line} strokeWidth={1} opacity={0.55} />);
  return (
    <svg width={w} height={h} style={{display: 'block', borderRadius: 22, background: T.card, boxShadow: `0 10px 30px rgba(31,29,27,0.10), inset 0 0 0 2px ${T.line}`}}>
      <defs><clipPath id={name + 'c'}><rect x={0} y={head} width={w} height={h - head} /></clipPath></defs>
      <g clipPath={`url(#${name}c)`}>{grid}</g>
      <line x1={0} x2={w} y1={head} y2={head} stroke={T.line} strokeWidth={2} />
      <text x={26} y={40} fontFamily={F} fontWeight={700} fontSize={30} fill={color}>{label}</text>
      <text x={w - 26} y={40} fontFamily={F} fontWeight={700} fontSize={30} fill={T.ink} textAnchor="end">{rate}<tspan fontWeight={500} fontSize={22} fill={T.ink2}> /min</tspan></text>
      <g clipPath={`url(#${name}c)`}>
        {pMarks && beats.map((b, i) => <text key={i} x={(b.t - 0.10 - t0) * px} y={by - 0.16 * mv - 18} textAnchor="middle" fontFamily={F} fontWeight={700} fontSize={30} fill={color}>P</text>)}
        {noP && beats.map((b, i) => <g key={i} transform={`translate(${(b.t - 0.10 - t0) * px} ${by - 0.16 * mv - 30})`}><circle r={13} fill="none" stroke={color} strokeWidth={3.5} /><line x1={-9} y1={9} x2={9} y2={-9} stroke={color} strokeWidth={3.5} /></g>)}
        <path d={pts.join('')} fill="none" stroke={T.ink} strokeWidth={4.5} strokeLinejoin="round" strokeLinecap="round" />
      </g>
    </svg>
  );
};

const Headline: React.FC<{size?: number}> = ({size = 1}) => (
  <div style={{fontFamily: F, color: T.ink, lineHeight: 0.98}}>
    <div style={{fontWeight: 800, fontSize: 92 * size, letterSpacing: '-0.02em', wordSpacing: '0.06em', color: T.tealInk}}>Sinus tach</div>
    <div style={{fontWeight: 500, fontSize: 52 * size, color: T.ink2, margin: `${6 * size}px 0 ${2 * size}px`}}>or</div>
    <div style={{fontWeight: 800, fontSize: 196 * size, letterSpacing: '-0.025em', color: T.coral}}>SVT?</div>
  </div>
);

// A: the two ECGs side by side (the comparison the video teaches)
export const ThumbA: React.FC = () => {
  const ready = useFonts();
  return (
    <AbsoluteFill style={{background: T.bg}}>
      <FontFaces />
      {ready && <>
        <div style={{position: 'absolute', left: 64, top: 165}}><Headline /></div>
        <div style={{position: 'absolute', left: 600, top: 70, display: 'flex', flexDirection: 'column', gap: 28}}>
          <MiniStrip name="sinus130" t0={1.2} secs={2.2} w={620} h={276} label="Sinus tach" rate={130} color={T.tealInk} pMarks />
          <MiniStrip name="avnrt180" t0={1.2} secs={2.2} w={620} h={276} label="SVT" rate={180} color={T.coral} noP />
        </div>
      </>}
    </AbsoluteFill>
  );
};

// B: the AVNRT loop on Mark's conduction heart
export const ThumbB: React.FC = () => {
  const ready = useFonts();
  return (
    <AbsoluteFill style={{background: T.bg}}>
      <FontFaces />
      {ready && <>
        <div style={{position: 'absolute', left: 64, top: 165}}><Headline /></div>
        <div style={{position: 'absolute', left: 600, top: 48, borderRadius: 24, boxShadow: '0 12px 34px rgba(31,29,27,0.12)'}}>
          <LoopCard uid="th" kind="avnrt" w={624} h={624} draw={1} phase={0.62} heart={{atr: 0, vent: 0, lit: 0, avGlow: 1}} view={6000} center={{x: 4000, y: 4250}} />
        </div>
      </>}
    </AbsoluteFill>
  );
};
