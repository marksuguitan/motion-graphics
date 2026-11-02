import React from 'react';
import {Img, staticFile} from 'remotion';
import art from './data/art.json';
import {T} from './theme';

// Mark's heart-conduction-system.svg (8000x8000 units), split into heart body and conduction paths.
const A = art as {heart: [string, string][]; cond: [string, string][]};
export const SA = {x: 2160, y: 2300};
export const AV = {x: 3320, y: 3400};
// geodesic distances (mask px, 1 px = 4 units) along the conduction system
export const ATR_MAX = 975.5;   // SA node -> farthest atrial branch
export const VENT_MAX = 2029.8; // AV node -> farthest Purkinje branch
export const AV_REACH = 408;    // atrial front reaches the AV node body
export const SA_BODY = 70;      // SA node body lit
export const ACC = 'M6295 3770 L6200 3440 L6010 3110'; // accessory pathway across the lateral mitral annulus, inside the wall (LV myocardium -> LA), for AVRT

const SW = 0.73;
const BODY = <g>{A.heart.map(([d, f], i) => <path key={i} d={d} fill={f} stroke={f} strokeWidth={SW} strokeMiterlimit={10} />)}</g>;
const COND_MUTED = <g>{A.cond.map(([d], i) => <path key={i} d={d} fill={T.muted} stroke={T.muted} strokeWidth={SW} />)}</g>;

export type HeartState = {atr: number; vent: number; lit: number; band?: boolean; saGlow?: number; avGlow?: number};

// Lit conduction is pre-rendered (tools-genlit.js) at 96 atrial and 128 ventricular wavefront levels from
// geodesic distance maps, so the wave always travels continuously along the tracts.
const NA = 96, NV = 128;
const litSrc = (k: 'a' | 'v', F: number, dmax: number, n: number) => {
  const i = Math.max(0, Math.min(n - 1, Math.round((F / dmax) * (n - 1))));
  return i === 0 ? null : staticFile(`maps/lit/${k}${String(i).padStart(3, '0')}.png`);
};
const abs: React.CSSProperties = {position: 'absolute', left: 0, top: 0, width: 2000, height: 2000};

// The heart as an HTML layer, 2000 px = 8000 units; place it with a CSS transform.
export const HeartLayer: React.FC<{s: HeartState; transform: string; bodyOpacity?: number; overlay?: React.ReactNode}> = ({s, transform, bodyOpacity = 1, overlay}) => {
  const a = s.lit > 0.001 ? litSrc('a', s.atr, ATR_MAX, NA) : null;
  const v = s.lit > 0.001 ? litSrc('v', s.vent, VENT_MAX, NV) : null;
  return (
    <div style={{...abs, transformOrigin: '0 0', transform}}>
      <svg width={2000} height={2000} viewBox="0 0 8000 8000" style={abs}>
        <g opacity={bodyOpacity}>{BODY}</g>
        {COND_MUTED}
      </svg>
      {a && <Img src={a} style={{...abs, opacity: s.lit}} />}
      {v && <Img src={v} style={{...abs, opacity: s.lit}} />}
      <svg width={2000} height={2000} viewBox="0 0 8000 8000" style={{...abs, overflow: 'visible'}}>
        {(s.saGlow ?? 0) > 0.01 && <circle cx={SA.x} cy={SA.y} r={380} fill={T.amber} opacity={0.28 * s.saGlow!} />}
        {(s.avGlow ?? 0) > 0.01 && <circle cx={AV.x} cy={AV.y} r={360} fill={T.amber} opacity={0.32 * s.avGlow!} />}
        {overlay}
      </svg>
    </div>
  );
};

// stage placement of the illustration: stage = L.x + L.s * (HTX + HS * u)
export const HS = 0.142, HTX = 391.5, HTY = -37;
export type Layout = {x: number; y: number; s: number};
export const toStage = (u: number, v: number, L: Layout) => ({x: L.x + L.s * (HTX + HS * u), y: L.y + L.s * (HTY + HS * v)});
export const layoutTransform = (L: Layout) => `translate(${L.x} ${L.y}) scale(${L.s}) translate(${HTX} ${HTY}) scale(${HS})`;
export const stageTransform = (L: Layout) => `translate(${L.x + L.s * HTX}px, ${L.y + L.s * HTY}px) scale(${L.s * HS * 4})`;
