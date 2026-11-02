export const T = {
  bg: '#F6F1E8', card: '#FFFCF7', line: '#E6DED2', grid: '#EFE3D6', gridBig: '#E2D2C2',
  ink: '#1F1D1B', ink2: '#6E675E', ink3: '#A49C91',
  amber: '#F0A030', amberSoft: '#FBEBD2', amberLine: '#F3CF95', amberInk: '#8A5410',
  teal: '#078BAA', tealSoft: '#CFEAF0', tealLine: '#9FD3E0', tealInk: '#0A6A82',
  coral: '#E8554B', coralSoft: '#FBDAD5', coralLine: '#F3B2AB', coralInk: '#B22F2F',
  muted: '#DCCFC0',
  font: '"DM Sans", system-ui, sans-serif',
};
export const FPS = 30;
export const LEAD = 1.5;            // seconds of silence before the first word (built into vo.mp3)
export const END_VO = 166.0;        // VO-time at which the video ends
export const TOTAL = Math.round((END_VO + LEAD) * FPS);
