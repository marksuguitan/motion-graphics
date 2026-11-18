// mono.ts: the monochrome palette for this piece (Mark, Nov 2, 2026: "monochromatic colors", from the Comma
// reference's light grey ground and charcoal dot). Overrides Comma Clinical's colours only; type and motion stay.
export const M = {
  bg: '#EFEFED', // Comma's light grey ground
  ink: '#1C1C1C', // text, the trace, emphasis rings
  ink2: '#6A6A6A', // body lines
  inactive: '#B9B9B7', // upcoming steps, the ECG baseline
  path: '#FFFFFF', // the conduction system before the impulse reaches it
  lit: '#2A2A2A', // the conduction system once the impulse has passed
  orb: '#141414', // the impulse
  ring: '#FFFFFF', // a thin white rim keeps the orb readable on the lit path
};
export const FONT_HEAD = 'Manrope, system-ui, sans-serif';
export const FONT_BODY = 'Inter, system-ui, sans-serif';
