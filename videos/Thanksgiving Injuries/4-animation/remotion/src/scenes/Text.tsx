// Text.tsx: the words on screen, scene by scene. Times come from the timeline (reading-time rule);
// the rows here are script v1 as built (see the production doc for the final wording and sources).
import React from 'react';
import {Cards, Row} from './Card';

const R = (kind: Row['kind'], text: React.ReactNode): Row => ({kind, text});

export const Texts: React.FC<{t: number}> = ({t}) => (
  <>
    <Cards t={t} beats={['1A']} kicker="Thanksgiving" x={960} cy={722} align="center" width={1700}
      rows={{'1A': [R('title', 'Five ways the feast ends in the ER')]}} />
    <Cards t={t} beats={['2A']} kicker="Morning" rows={{
      '2A': [R('heading', 'Carving cuts'), R('big', '1,190'), R('body', 'knife injuries reach US ERs every day'), R('note', 'Average, 1990–2008 · Smith, J Emerg Med 2013')],
    }} />
    <Cards t={t} beats={['3A', '3B']} kicker="Afternoon" rows={{
      '3A': [R('heading', 'Hot-oil burns run'), R('heading', 'deeper than they look'), R('note', 'Often full thickness · StatPearls; Hankins, Burns 2006')],
      '3B': [R('tipHead', 'Cool running water,'), R('tipHead', '20 minutes'), R('body', 'Within 3 hours. No ice.'), R('note', 'Griffin, Ann Emerg Med 2020')],
    }} />
    <Cards t={t} beats={['4A', '4B', '4C']} kicker="Dinner" rows={{
      '4A': [R('big', '71%'), R('body', 'of adult choking deaths:'), R('bodyStrong', 'meat, fish or sausage'), R('note', 'Autopsy series of 200 · StatPearls')],
      '4B': [R('heading', 'Can’t speak or cough?'), R('tip', 'Abdominal thrusts until it clears')],
      '4C': [R('heading', 'Meat stuck in'), R('heading', 'the esophagus?'), R('body', '85–90% have a cause:'), R('body', 'think eosinophilic esophagitis'), R('note', 'Adults · StatPearls')],
    }} />
    <Cards t={t} beats={['5A', '5B', '5C']} kicker="After dinner" rows={{
      '5A': [R('heading', <i>Clostridium perfringens</i>), R('body', 'Its spores survive cooking.')],
      '5B': [R('heading', 'Then: cramps and'), R('heading', 'watery diarrhea'), R('body', '8 to 16 hours later')],
      '5C': [R('heading', 'US outbreaks peak in'), R('heading', 'November and December'), R('note', 'Grass, Foodborne Pathog Dis 2013')],
    }} />
    <Cards t={t} beats={['6A', '6B']} kicker="Late night" rows={{
      '6A': [R('heading', 'Holiday heart'), R('body', 'Atrial fibrillation after heavy drinking')],
      '6B': [R('heading', 'Over 90% revert'), R('heading', 'on their own'), R('body', 'within 12–24 hours'), R('tip', 'Check potassium and magnesium')],
    }} />
    <Cards t={t} beats={['7A']} x={960} cy={735} align="center" width={1400}
      rows={{'7A': [R('title', 'Happy Thanksgiving'), R('sub', 'from Medzcool')]}} />
  </>
);
