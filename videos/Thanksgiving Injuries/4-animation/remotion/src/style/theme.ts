// theme.ts: Warm Clinical look (Motion Style Guide: Typography, Color, soft geometry), plus this video's
// object tints (plate, food, skin, oil), which are neutrals, not accents.
import type React from 'react';

export const W = 1920;
export const H = 1080;
export const FPS = 30;

export const C = {
  bg: '#FFFFFF',
  soft: '#F7F7F5',
  divider: '#E6E4E0',
  line: '#CFCBC4', // object outlines
  ink: '#222222',
  ink2: '#6A6A6A',
  focus: '#F0645A', // coral: the injury, the hazard
  signal: '#E3A33B', // amber: the ECG
  normal: '#2E9C8F', // teal: what to do
  alert: '#E53935', // emphasis rings only
  inactive: '#B9B5AE',
  // object tints
  steel: '#DEDBD5',
  board: '#EADFCF',
  oil: '#F3E3B5',
  oilLine: '#E2CB8A',
  epi: '#F3D3C6',
  dermis: '#ECBBA8',
  fat: '#F7E7C3',
  food: '#D9C0A3',
  mound: '#E8D6BF',
  drink: '#E9CFAE',
};

export const FONT = {head: 'Manrope, system-ui, sans-serif', body: 'Inter, system-ui, sans-serif'};

export const TYPE: Record<'title' | 'heading' | 'kicker' | 'label' | 'body' | 'number', React.CSSProperties> = {
  title: {fontFamily: FONT.head, fontWeight: 600, fontSize: 80, lineHeight: 1.05, color: C.ink},
  heading: {fontFamily: FONT.head, fontWeight: 600, fontSize: 52, lineHeight: 1.1, color: C.ink},
  kicker: {fontFamily: FONT.head, fontWeight: 700, fontSize: 23, letterSpacing: 3, textTransform: 'uppercase', color: C.ink2},
  label: {fontFamily: FONT.body, fontWeight: 500, fontSize: 30, color: C.ink},
  body: {fontFamily: FONT.body, fontWeight: 400, fontSize: 28, lineHeight: 1.35, color: C.ink},
  number: {fontFamily: FONT.body, fontWeight: 600, fontVariantNumeric: 'tabular-nums', color: C.ink},
};
export const RADIUS = {card: 24, chip: 12};
