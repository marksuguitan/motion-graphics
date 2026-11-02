// comma_easing.jsx: Comma Clinical easing for After Effects build scripts (ExtendScript).
// The values come from the Motion Style Guide, section "Comma Clinical", table "After Effects settings".
// If the guide and this file disagree, the guide wins: update this file to match.
//
// Use: #include "comma_easing.jsx" (or paste it in), then
//   CommaEase.move(prop, [[t0, v0], [t1, v1]], "snap");              // two keys + the named curve
//   CommaEase.ease(prop, k1, k2, "accel");                             // curve between existing keys
//   CommaEase.overshoot(prop, t0, from, to, 0.6, 0.08);               // snap past target, settle back
//   CommaEase.squash(scaleProp, tImpact, [100, 100], 1);               // 75/125 on impact, recover
//   CommaEase.stagger(i)                                               // seconds of offset for item i
// Curves: "snap" (default, snap and settle), "cross" (move across the frame), "accel" (accelerate
// into a swap), "anti" (anticipation). Speed 0 everywhere except where the guide says 6x average.

var CommaEase = (function () {
    var FPS_STAGGER = 2 / 30;                      // 2 frames at 30 fps
    var CURVES = {                                 // [outInfluence, outSpeedFactor, inInfluence, inSpeedFactor]
        snap:  [16, 6, 70, 0],
        cross: [33, 0, 85, 0],
        accel: [70, 0, 16, 6],
        anti:  [50, 0, 50, 0],
        back:  [50, 0, 70, 0]                      // the return leg of an overshoot
    };

    function dims(prop) {
        var t = prop.propertyValueType;
        if (t === PropertyValueType.TwoD_SPATIAL || t === PropertyValueType.ThreeD_SPATIAL || t === PropertyValueType.SHAPE) return 1;
        var v = prop.keyValue(1);
        return (v instanceof Array) ? v.length : 1;
    }
    function spatial(prop) {
        var t = prop.propertyValueType;
        return t === PropertyValueType.TwoD_SPATIAL || t === PropertyValueType.ThreeD_SPATIAL;
    }
    // average speed per dimension (or along the path for spatial properties), units per second
    function avgSpeed(prop, k1, k2) {
        var dt = prop.keyTime(k2) - prop.keyTime(k1);
        if (dt <= 0) return [0];
        var a = prop.keyValue(k1), b = prop.keyValue(k2), out = [], i, d = 0;
        if (prop.propertyValueType === PropertyValueType.SHAPE) return [0];
        if (!(a instanceof Array)) return [Math.abs(b - a) / dt];
        if (spatial(prop)) { for (i = 0; i < a.length; i++) d += (b[i] - a[i]) * (b[i] - a[i]); return [Math.sqrt(d) / dt]; }
        for (i = 0; i < a.length; i++) out.push(Math.abs(b[i] - a[i]) / dt);
        return out;
    }

    // set the curve between keys k1 and k2, leaving the outer sides of both keys as they were
    function ease(prop, k1, k2, kind) {
        var c = CURVES[kind || "snap"], n = dims(prop), sp = avgSpeed(prop, k1, k2), i;
        var o1 = [], i1 = prop.keyInTemporalEase(k1), o2 = prop.keyOutTemporalEase(k2), in2 = [];
        for (i = 0; i < n; i++) {
            var s = sp[Math.min(i, sp.length - 1)];
            o1.push(new KeyframeEase(c[1] * s, c[0]));
            in2.push(new KeyframeEase(c[3] * s, c[2]));
        }
        prop.setInterpolationTypeAtKey(k1, prop.keyInInterpolationType(k1), KeyframeInterpolationType.BEZIER);
        prop.setInterpolationTypeAtKey(k2, KeyframeInterpolationType.BEZIER, prop.keyOutInterpolationType(k2));
        prop.setTemporalEaseAtKey(k1, i1, o1);
        prop.setTemporalEaseAtKey(k2, in2, o2);
        if (spatial(prop)) { try { prop.setSpatialAutoBezierAtKey(k1, false); prop.setSpatialAutoBezierAtKey(k2, false); } catch (e) {} }
    }

    // list: [[t, v], ...]; every leg gets the same curve
    function move(prop, list, kind) {
        var ks = [], i;
        for (i = 0; i < list.length; i++) { prop.setValueAtTime(list[i][0], list[i][1]); }
        for (i = 0; i < list.length; i++) ks.push(prop.nearestKeyIndex(list[i][0]));
        for (i = 0; i + 1 < ks.length; i++) ease(prop, ks[i], ks[i + 1], kind);
        return ks;
    }

    function scaleBy(v, f, from) {                 // from + (v - from) * f, per dimension
        if (!(v instanceof Array)) return from + (v - from) * f;
        var r = []; for (var i = 0; i < v.length; i++) r.push(from[i] + (v[i] - from[i]) * f); return r;
    }
    // snap past the target by `over` (0.05-0.10), then settle back over 0.15-0.25 s
    function overshoot(prop, t0, from, to, d, over, back) {
        var t1 = t0 + 0.5 * d, t2 = t1 + (back || 0.2);
        var peak = scaleBy(to, 1 + (over === undefined ? 0.08 : over), from);
        prop.setValueAtTime(t0, from); prop.setValueAtTime(t1, peak); prop.setValueAtTime(t2, to);
        var a = prop.nearestKeyIndex(t0), b = prop.nearestKeyIndex(t1), c = prop.nearestKeyIndex(t2);
        ease(prop, a, b, "snap"); ease(prop, b, c, "back");
    }
    // squash a Scale property on impact: axis 0 = x is the impact axis, 1 = y
    function squash(scale, tImpact, rest, axis, amount) {
        var a = amount || 0.25, s = [rest[0], rest[1]];
        s[axis] = rest[axis] * (1 - a); s[1 - axis] = rest[1 - axis] * (1 + a);
        if (rest.length > 2) s.push(rest[2]);
        move(scale, [[tImpact, s], [tImpact + 0.2, rest]], "snap");
    }
    function stagger(i) { return i * FPS_STAGGER; }

    return { CURVES: CURVES, ease: ease, move: move, overshoot: overshoot, squash: squash, stagger: stagger,
             HOLD_MIN: 0.4, SNAP_DUR: [0.5, 0.7], CROSS_DUR: [0.6, 0.9], ACCEL_DUR: [0.2, 0.3] };
})();
