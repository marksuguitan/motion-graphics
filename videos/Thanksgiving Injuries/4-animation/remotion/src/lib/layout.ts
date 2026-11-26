// layout.ts: where the words sit, per format. "wide" is the 16:9 YouTube video; "reel" is the 9:16 Instagram reel
// (Reel.tsx), where the art sits in the top band and the cards below it, clear of the reel's own captions and buttons.
import {createContext, useContext} from 'react';

export type Layout = {
  title: {left: number; top: number; width: number; wrap: boolean};
  card: {x: number; cy: number; width: number}; // scenes 2-6, left-aligned beside or under the art
  close: {x: number; cy: number; width: number}; // scene 7, centred under the plate
};
export const WIDE: Layout = {
  title: {left: 110, top: 650, width: 1700, wrap: false},
  card: {x: 1090, cy: 540, width: 780},
  close: {x: 960, cy: 735, width: 1400},
};
export const REEL: Layout = {
  title: {left: 70, top: 1000, width: 940, wrap: true},
  card: {x: 90, cy: 1360, width: 900},
  close: {x: 540, cy: 1075, width: 940},
};
export const LayoutCtx = createContext<Layout>(WIDE);
export const useLayout = () => useContext(LayoutCtx);
