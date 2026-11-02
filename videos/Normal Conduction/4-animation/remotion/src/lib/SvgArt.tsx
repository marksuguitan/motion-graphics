// SvgArt.tsx: puts a beat's SVG (3-board/art/[ID]_[name].svg, copied to public/art/ by `npm run prep`)
// on screen inline, so its named layers can be animated. This is the Remotion path's replacement for
// the Illustrator .ai conversion: the SVG approved at Gate 3 is rendered as is.
//
//   <SvgArt src="art/3B_cooperative.svg" layers={{
//     'Curves/Normal': {clip: [0, 100 - 100 * p, 0, 0]},        // wipe on left to right
//     'Panel/RightShift': {y: ease(t, t0, 0.6, 40, 0), scale: s},
//     'Takeaway/Text': {visible: cut(t, sync('3B', 'cooperative'))},
//   }} paths={{'curve-path': morph(t, t1, 0.6, dA, dB)}} />
//
// Layer names are the `Group/Sublayer` ids from the art. Illustrator's escaped form (`Group_x2F_Sublayer`)
// is found too. The `Meta/BeatID` layer (the small beat ID for the Motion Board) is hidden unless showMeta.
import React, {useEffect, useLayoutEffect, useMemo, useRef, useState} from 'react';
import {cancelRender, continueRender, delayRender, staticFile} from 'remotion';

export type LayerStyle = {
  visible?: boolean;
  opacity?: number;
  x?: number; // px in the SVG's own units (1920x1080 art: px)
  y?: number;
  scale?: number;
  sx?: number; // multiplies scale on x (squash)
  sy?: number;
  rotate?: number; // degrees
  origin?: string; // CSS transform-origin within the layer's box, default 'center'
  clip?: [number, number, number, number]; // inset in % of the layer's box: top, right, bottom, left (wipes, reveals)
  fill?: string;
  stroke?: string;
};

const ids = (name: string) => [name, name.replace(/\//g, '_x2F_'), name.replace(/[\s/]/g, '_')];

function find(root: Element, name: string): Element | null {
  for (const id of ids(name)) {
    const el = root.querySelector(`[id="${CSS.escape(id)}"]`);
    if (el) return el;
  }
  return null;
}

// CSS transforms replace an SVG transform attribute, so a layer that already has one is wrapped once
// in a plain <g> and the wrapper is what moves.
function target(el: Element): SVGElement {
  if (!el.hasAttribute('transform')) return el as SVGElement;
  const parent = el.parentElement;
  if (parent && parent.getAttribute('data-wrap') === el.id) return parent as unknown as SVGElement;
  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  g.setAttribute('data-wrap', el.id);
  el.replaceWith(g);
  g.appendChild(el);
  return g;
}

function apply(el: SVGElement, s: LayerStyle) {
  const st = el.style;
  st.display = s.visible === false ? 'none' : '';
  st.opacity = s.opacity === undefined ? '' : String(s.opacity);
  const sc = s.scale ?? 1;
  const tf = `translate(${s.x ?? 0}px, ${s.y ?? 0}px) rotate(${s.rotate ?? 0}deg) scale(${sc * (s.sx ?? 1)}, ${sc * (s.sy ?? 1)})`;
  st.transform = tf;
  st.transformBox = 'fill-box';
  st.transformOrigin = s.origin ?? 'center';
  st.clipPath = s.clip ? `inset(${s.clip.map((v) => `${v}%`).join(' ')})` : '';
  if (s.fill) st.fill = s.fill;
  if (s.stroke) st.stroke = s.stroke;
}

const cache = new Map<string, string>();

export const SvgArt: React.FC<{
  src: string; // path under public/, e.g. "art/3B_cooperative.svg"
  layers?: Record<string, LayerStyle>;
  paths?: Record<string, string>; // id -> new "d" (morphs)
  text?: Record<string, string>; // id -> new text content (type on/off, counters)
  showMeta?: boolean;
  style?: React.CSSProperties;
}> = ({src, layers = {}, paths = {}, text = {}, showMeta = false, style}) => {
  const [svg, setSvg] = useState<string | null>(cache.get(src) ?? null);
  const [handle] = useState(() => (cache.has(src) ? null : delayRender(`SVG ${src}`)));
  const ref = useRef<HTMLDivElement>(null);
  const released = useRef(false);

  useEffect(() => {
    if (svg !== null) return;
    fetch(staticFile(src))
      .then((r) => {
        if (!r.ok) throw new Error(`${src}: HTTP ${r.status}. Run npm run prep?`);
        return r.text();
      })
      .then((txt) => {
        cache.set(src, txt);
        setSvg(txt);
      })
      .catch((e) => cancelRender(e));
  }, [src, svg]);

  const html = useMemo(() => ({__html: svg ?? ''}), [svg]);

  useLayoutEffect(() => {
    const root = ref.current?.querySelector('svg');
    if (!root) return;
    root.setAttribute('width', '100%');
    root.setAttribute('height', '100%');
    root.style.display = 'block';
    const meta = find(root, 'Meta/BeatID');
    if (meta) (meta as SVGElement).style.display = showMeta ? '' : 'none';
    for (const [name, s] of Object.entries(layers)) {
      const el = find(root, name);
      if (!el) throw new Error(`${src}: no layer "${name}"`);
      apply(target(el), s);
    }
    for (const [id, d] of Object.entries(paths)) find(root, id)?.setAttribute('d', d);
    for (const [id, s] of Object.entries(text)) {
      const el = find(root, id);
      if (el) el.textContent = s;
    }
    if (handle !== null && svg !== null && !released.current) {
      released.current = true;
      continueRender(handle);
    }
  });

  return <div ref={ref} style={{position: 'absolute', inset: 0, ...style}} dangerouslySetInnerHTML={html} />;
};
