import {continueRender, delayRender, staticFile} from 'remotion';
export const fontFamily = 'DM Sans Local';
if (typeof document !== 'undefined') {
  const h = delayRender('font');
  Promise.all(['400', '500', '700'].map((w) => new FontFace(fontFamily, `url(${staticFile('dmsans-' + w + '.woff2')})`, {weight: w}).load().then((ff) => (document as any).fonts.add(ff))))
    .then(() => continueRender(h)).catch(() => continueRender(h));
}
export const C = {
  bg: '#F3EEE5', card: '#FBF8F2', ink: '#22201E', ink2: '#5E5850', mute: '#A9A095', line: '#E3DBCF', grid: '#E9E2D7',
  red: '#B23A30', redSoft: '#F3DCD6', blue: '#36589A', blueSoft: '#DCE4F1',
  oxy: '#C8463A', deoxy: '#7E2A27', o2: '#12B5F5',
  alpha: '#E2A391', alphaDark: '#C77D69', beta: '#9FB3CF', betaDark: '#7E95B6', heme: '#8E2F2B', fe: '#E3A13A',
  band: '#EFE6D8', tube: '#F2D9D2', tubeWall: '#D9A79B',
};
