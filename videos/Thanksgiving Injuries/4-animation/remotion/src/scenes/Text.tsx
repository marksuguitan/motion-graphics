// Text.tsx: the words on screen, scene by scene. Times come from the timeline (reading-time rule);
// the rows here are the script as built (see the production doc for the wording and sources).
import React from 'react';
import {Cards, Row} from './Card';
import {progress} from '../style/comma';
import {C, FONT} from '../style/theme';
import {EV} from '../lib/tl';
import {useLayout} from '../lib/layout';

const R = (kind: Row['kind'], text: Row['text']): Row => ({kind, text});
const tab: React.CSSProperties = {fontVariantNumeric: 'tabular-nums'};
/** A number that counts up to its value as the row comes on, fast at first and settling (Mark, Nov 25, 2026). */
const count = (to: number, from = 0, dur = 0.9) => (u: number) => {
  const k = 1 - (1 - Math.max(0, Math.min(1, u / dur))) ** 3;
  return Math.round(from + (to - from) * k);
};
const n = (to: number, from = 0, dur = 0.9) => {
  const f = count(to, from, dur);
  return (u: number) => <span style={tab}>{f(u).toLocaleString('en-US')}</span>;
};

/** The title types on under the plate, holds, and is erased from the end; the plate leaves for scene 2 as it goes. */
const Title: React.FC<{t: number}> = ({t}) => {
  const s = EV.s1;
  const L = useLayout().title;
  const full: string = s.title;
  if (t < s.type || t >= s.erased) return null;
  const shown = t < s.erase
    ? Math.min(full.length, Math.floor((t - s.type) / s.charDur) + 1)
    : Math.ceil(full.length * (1 - Math.min(1, (t - s.erase) / (s.erased - s.erase)) ** 1.5));
  const moving = t < s.typed + 0.1 || t >= s.erase;
  const caret = moving || Math.floor((t - s.typed) / 0.4) % 2 === 1; // steady while typing or erasing, blinking in between
  const kick = -38 * progress(t, s.erase, 0.25, 'accel');
  return (
    <div style={{position: 'absolute', left: L.left, width: L.width, top: L.top, textAlign: 'center'}}>
      <div style={{height: 34, overflow: 'hidden', marginBottom: 14}}>
        <div style={{fontFamily: FONT.head, fontWeight: 700, fontSize: 23, letterSpacing: 3, color: C.ink2, lineHeight: '34px', transform: `translateY(${kick}px)`}}>THANKSGIVING</div>
      </div>
      <div style={{fontFamily: FONT.head, fontWeight: 600, fontSize: 80, lineHeight: '96px', color: C.ink, letterSpacing: -0.5, whiteSpace: L.wrap ? 'normal' : 'nowrap'}}>
        <span>{full.slice(0, shown)}</span>
        <span style={{display: 'inline-block', width: 0, position: 'relative', height: 76, verticalAlign: 'middle'}}>
          <span style={{position: 'absolute', left: 6, top: 2, width: 5, height: 72, borderRadius: 2.5, background: C.ink, opacity: caret ? 1 : 0}} />
        </span>
        <span style={{visibility: 'hidden'}}>{full.slice(shown)}</span>
      </div>
    </div>
  );
};

export const Texts: React.FC<{t: number}> = ({t}) => {
  const {card, close} = useLayout();
  return (
  <>
    <Title t={t} />
    <Cards t={t} {...card} beats={['2A']} kicker="Morning" rows={{
      '2A': [R('heading', 'Carving cuts'), R('big', n(1190)), R('body', 'knife injuries reach US ERs every day'), R('note', 'Average, 1990–2008 · Smith, J Emerg Med 2013')],
    }} />
    <Cards t={t} {...card} beats={['3A', '3B']} kicker="Afternoon" rows={{
      '3A': [R('heading', 'Hot-oil burns run'), R('heading', 'deeper than they look'), R('note', 'Often full thickness · StatPearls; Hankins, Burns 2006')],
      '3B': [R('tipHead', 'Cool running water,'), R('tipHead', (u) => <>{n(20, 0, 0.8)(u)} minutes</>), R('body', 'Within 3 hours. No ice.'), R('note', 'Griffin, Ann Emerg Med 2020')],
    }} />
    <Cards t={t} {...card} x={card.x + (card.x > 540 ? 10 : 0)} beats={['4A', '4B', '4C']} kicker="Dinner" rows={{
      '4A': [R('big', (u) => <>{n(71)(u)}%</>), R('body', 'of adult choking deaths:'), R('bodyStrong', 'meat, fish or sausage'), R('note', 'Autopsy series of 200 · StatPearls')],
      '4B': [R('heading', 'Can’t speak or cough?'), R('tip', 'Abdominal thrusts until it clears')],
      '4C': [R('heading', 'Meat stuck in'), R('heading', 'the esophagus?'), R('body', (u) => <>{n(85, 60, 0.8)(u)}–{n(90, 65, 0.8)(u)}% have a cause:</>), R('body', 'think eosinophilic esophagitis'), R('note', 'Adults · StatPearls')],
    }} />
    <Cards t={t} {...card} beats={['5A', '5B', '5C']} kicker="After dinner" rows={{
      '5A': [R('heading', <i>Clostridium perfringens</i>), R('body', 'Its spores survive cooking.')],
      '5B': [R('heading', 'Then: cramps and'), R('heading', 'watery diarrhea'), R('body', '8 to 16 hours later')],
      '5C': [R('heading', 'US outbreaks peak in'), R('heading', 'November and December'), R('note', 'Grass, Foodborne Pathog Dis 2013')],
    }} />
    <Cards t={t} {...card} beats={['6A', '6B']} kicker="Late night" rows={{
      '6A': [R('heading', 'Holiday heart'), R('body', 'Atrial fibrillation after heavy drinking')],
      '6B': [R('heading', (u) => <>Over {n(90, 60, 0.8)(u)}% revert</>), R('heading', 'on their own'), R('body', 'within 12–24 hours'), R('tip', 'Check potassium and magnesium')],
    }} />
    <Cards t={t} beats={['7A']} {...close} align="center"
      rows={{'7A': [R('title', 'Happy Thanksgiving'), R('sub', 'from Medzcool')]}} />
  </>
  );
};
