export const N = 2.7;
export const P50N = 26.8, P50L = 20, P50R = 36;
export const sat = (p: number, p50: number) => (p <= 0 ? 0 : 100 * p ** N / (p ** N + p50 ** N));
// plot geometry
export const PL = 250, PR = 1150, PT = 120, PB = 840;
export const X = (p: number) => PL + (p / 100) * (PR - PL);
export const Y = (s: number) => PB - (s / 100) * (PB - PT);
export const curvePath = (p50: number, to = 100) => {
  let d = '';
  for (let p = 0; p <= to + 1e-6; p += 0.5) d += (d ? 'L' : 'M') + X(p).toFixed(1) + ',' + Y(sat(p, p50)).toFixed(1);
  return d;
};
