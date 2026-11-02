// theme.ts: Warm Clinical look (Motion Style Guide: Typography, Color, soft geometry).
// Hex values and sizes are the guide's *starting values*; if the guide changes, change them here.
import type React from 'react';

export const W = 1920;
export const H = 1080;
export const FPS = 30;

export const C = {
  bg: '#FFFFFF',
  soft: '#F7F7F5', // cards, panels, alternate scenes
  divider: '#E6E4E0',
  ink: '#222222', // headings and body
  ink2: '#6A6A6A', // kickers, units, captions
  focus: '#F0645A', // coral: what to look at now; a change or abnormality
  arterial: '#C94A44', // oxygenated
  venous: '#3D6FB6', // deoxygenated
  signal: '#E3A33B', // amber: conduction, waveforms, sound
  normal: '#2E9C8F', // teal: the reference / healthy state
};

export const FONT = {
  head: 'Manrope, system-ui, sans-serif',
  body: 'Inter, system-ui, sans-serif',
};

export const TYPE: Record<'title' | 'heading' | 'kicker' | 'label' | 'body' | 'number', React.CSSProperties> = {
  title: {fontFamily: FONT.head, fontWeight: 600, fontSize: 80, lineHeight: 1.05, color: C.ink},
  heading: {fontFamily: FONT.head, fontWeight: 600, fontSize: 52, lineHeight: 1.1, color: C.ink},
  kicker: {fontFamily: FONT.head, fontWeight: 700, fontSize: 23, letterSpacing: 3, textTransform: 'uppercase', color: C.ink2},
  label: {fontFamily: FONT.body, fontWeight: 500, fontSize: 30, color: C.ink},
  body: {fontFamily: FONT.body, fontWeight: 400, fontSize: 28, lineHeight: 1.35, color: C.ink},
  number: {fontFamily: FONT.body, fontWeight: 600, fontVariantNumeric: 'tabular-nums', color: C.ink},
};

export const RADIUS = {card: 24, chip: 12};
export const SHADOW = '0 8px 24px rgba(34, 34, 34, 0.10)'; // one soft shadow, no hard drops, no glows
