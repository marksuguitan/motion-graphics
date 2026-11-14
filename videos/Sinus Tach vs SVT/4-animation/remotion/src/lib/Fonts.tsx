// Fonts.tsx: Manrope (headings) and Inter (body, labels), vendored from @fontsource-variable (SIL OFL)
// so renders never depend on Google Fonts being reachable. SVG art that says font-family="Manrope" or
// "Inter" picks these up. Rendering waits until every face has loaded.
import {cancelRender, continueRender, delayRender, staticFile} from 'remotion';

const LATIN = 'U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD';
const LATIN_EXT = 'U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF';
const GREEK = 'U+0370-0377,U+037A-037F,U+0384-038A,U+038C,U+038E-03A1,U+03A3-03FF';

const FACES: [string, string, string][] = [
  ['Manrope', 'fonts/manrope-latin-wght-normal.woff2', LATIN],
  ['Manrope', 'fonts/manrope-latin-ext-wght-normal.woff2', LATIN_EXT],
  ['Inter', 'fonts/inter-latin-wght-normal.woff2', LATIN],
  ['Inter', 'fonts/inter-latin-ext-wght-normal.woff2', LATIN_EXT],
  ['Inter', 'fonts/inter-greek-wght-normal.woff2', GREEK],
];

let started = false;
export function loadFonts() {
  if (started || typeof document === 'undefined') return;
  started = true;
  const handle = delayRender('Loading Manrope and Inter');
  Promise.all(
    FACES.map(([family, file, range]) => {
      const face = new FontFace(family, `url(${staticFile(file)}) format("woff2")`, {weight: '200 900', unicodeRange: range});
      document.fonts.add(face);
      return face.load();
    }),
  )
    .then(() => continueRender(handle))
    .catch((e) => cancelRender(e)); // fail the render rather than ship a fallback font
}
