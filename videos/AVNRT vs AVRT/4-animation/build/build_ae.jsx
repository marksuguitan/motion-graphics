// build_ae.jsx — AVNRT vs AVRT, Stage 4 build.
// Adapted from Oxygen Hemoglobin Curve's build_ae.jsx (same import, layer-copy and Comma Clinical easing), with the
// actions this video needs: loops that draw on and pulses that lap them, waves that ride the pathways, strips that print.
// Run in After Effects (File > Scripts > Run Script File...) after prep_ai.py, build_ai.jsx (Illustrator) and plan.py.
// Needs Settings > Scripting & Expressions > "Allow Scripts to Write Files and Access Network".
// Builds a new project from 4-animation/ai/<beat>.ai (imported as Composition – Retain Layer Sizes) and 3-board/audio/full.mp3:
//   Beats/<beat>      one precomp per beat, layers named as in the SVGs, every move keyed to its word
//   Scenes/Scene N    beat precomps at their starts, full.mp3 laid in, a marker at every sync point
//   AVNRT vs AVRT     master comp, scenes in order, the same markers
// then saves 4-animation/AVNRT vs AVRT_v<N>.aep, a PNG of every beat start and sync point (and 0.9 s after each) to
// build/ae_check/ and build/ae_build_report.json. The plan is build/ae_plan.json (from plan.py): edit plan.py, not this file.
#target aftereffects
#include "../../../../library/scripts/adobe/comma_easing.jsx"
(function () {
    var buildDir = File($.fileName).parent.fsName;
    var animDir = Folder(buildDir).parent.fsName;                       // .../4-animation
    var videoDir = Folder(animDir).parent.fsName;
    var pf = File(buildDir + "/ae_plan.json"); pf.encoding = "UTF-8"; pf.open("r");
    var PLAN = eval("(" + pf.read() + ")"); pf.close();
    var VERSION = 3;                                         // v1: first build; v2: 6C adenosine label, pulses under the labels; v3: glows not clipped to a box
    var report = { errors: [], missing: [], beats: [], checks: [] };
    function err(msg) { report.errors.push(msg); }
    if (app.preferences.getPrefAsLong("Main Pref Section", "Pref_SCRIPTING_FILE_NETWORK_SECURITY") !== 1) {
        return "Turn on Settings > Scripting & Expressions > Allow Scripts to Write Files and Access Network";
    }
    var aep = File(animDir + "/" + PLAN.title + "_v" + VERSION + ".aep");
    if (aep.exists) return "not built: " + aep.fsName + " already exists (save the next build as a new version)";
    if (app.project && app.project.numItems > 0) app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
    app.newProject();
    var proj = app.project;
    var fAI = proj.items.addFolder("AI"), fAud = proj.items.addFolder("Audio"), fBeats = proj.items.addFolder("Beats"), fScenes = proj.items.addFolder("Scenes");
    var MO = PLAN.motion, FR = 1 / PLAN.fps;

    // ---------- import ----------
    var AI = {};
    function importAI(key) {
        if (AI[key]) return AI[key];
        var f = File(animDir + "/ai/" + key + ".ai");
        if (!f.exists) { err("missing " + f.fsName); return null; }
        // AE caches a parsed .ai by path for the whole session: import a copy whose path carries the file's modification time
        var dir = Folder(animDir + "/ai/_fresh/" + key + "_" + f.modified.getTime());
        if (!dir.exists) dir.create();
        var f2 = File(dir.fsName + "/" + key + ".ai");
        if (!f2.exists && !f.copy(f2.fsName)) f2 = f;
        var io = new ImportOptions(f2);
        if (!io.canImportAs(ImportAsType.COMP_CROPPED_LAYERS)) { err("cannot import " + key + " as layered comp"); return null; }
        io.importAs = ImportAsType.COMP_CROPPED_LAYERS;
        var c = null;
        try { c = proj.importFile(io); } catch (x) { $.sleep(500); try { c = proj.importFile(io); } catch (x2) { err("import " + key + ": " + x2); return null; } }
        c.parentFolder = fAI; c.frameRate = PLAN.fps;
        for (var i = 1; i <= proj.numItems; i++) {
            var it = proj.item(i);
            if (it instanceof FolderItem && it.name.indexOf(key) === 0 && it.parentFolder.id === proj.rootFolder.id) it.parentFolder = fAI;
        }
        AI[key] = c;
        return c;
    }

    // ---------- helpers ----------
    function TR(l) { return l.property("ADBE Transform Group"); }
    function OP(l) { return TR(l).property("ADBE Opacity"); }
    function POS(l) { return TR(l).property("ADBE Position"); }
    function SC(l) { return TR(l).property("ADBE Scale"); }
    function ANC(l) { return TR(l).property("ADBE Anchor Point"); }
    function cm(prop, list, kind) { return CommaEase.move(prop, list, kind || "snap"); }
    function lin(prop, list) {                               // constant-rate keys (conduction, printing, laps)
        for (var i = 0; i < list.length; i++) prop.setValueAtTime(list[i][0], list[i][1]);
        for (i = 0; i < list.length; i++) {
            var k = prop.nearestKeyIndex(list[i][0]);
            prop.setInterpolationTypeAtKey(k, KeyframeInterpolationType.LINEAR, KeyframeInterpolationType.LINEAR);
        }
    }
    function cutIn(l, t) { if (t > 0.001) l.inPoint = Math.min(l.containingComp.duration - FR, t); }
    function cutOut(l, t) { if (!l) return; if (t <= 0.001) { l.remove(); return; } l.outPoint = Math.min(l.containingComp.duration, t); }
    function rect(l) {                                        // comp-space bounds at rest (scale 100 %)
        var p = POS(l).value, a = ANC(l).value;
        if (l.comment && l.comment.indexOf("rect:") === 0) {  // a glow in its own comp-size precomp: the art's bounds, kept when it was made
            var v = l.comment.substr(5).split(",");
            return [+v[0] + p[0] - a[0], +v[1] + p[1] - a[1], +v[2] + p[0] - a[0], +v[3] + p[1] - a[1]];
        }
        var r = l.sourceRectAtTime(0, false);
        return [p[0] - a[0] + r.left, p[1] - a[1] + r.top, p[0] - a[0] + r.left + r.width, p[1] - a[1] + r.top + r.height];
    }
    function setPivot(l, c) {                                 // anchor to comp point c without moving the art
        var a = ANC(l).value, p = POS(l).value;
        ANC(l).setValue([a[0] + c[0] - p[0], a[1] + c[1] - p[1]]); POS(l).setValue([c[0], c[1]]);
    }
    function centre(r) { return [(r[0] + r[2]) / 2, (r[1] + r[3]) / 2]; }
    function pivotPoint(r, how) {
        if (how === "left") return [r[0], (r[1] + r[3]) / 2];
        if (how === "right") return [r[2], (r[1] + r[3]) / 2];
        if (how === "top") return [(r[0] + r[2]) / 2, r[1]];
        return centre(r);
    }
    function boxShape(x0, y0, x1, y1) {
        var s = new Shape(); s.vertices = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]];
        s.inTangents = [[0, 0], [0, 0], [0, 0], [0, 0]]; s.outTangents = [[0, 0], [0, 0], [0, 0], [0, 0]]; s.closed = true; return s;
    }
    function addMask(l, name) {
        var m = l.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
        m.name = name; m.property("ADBE Mask Feather").setValue([2, 2]);
        return m.property("ADBE Mask Shape");
    }
    function toLayer(l, x, y, p) { var a = ANC(l).value; return [x - p[0] + a[0], y - p[1] + a[1]]; }   // comp -> layer, at position p
    function hex(h) { return [parseInt(h.substr(1, 2), 16) / 255, parseInt(h.substr(3, 2), 16) / 255, parseInt(h.substr(5, 2), 16) / 255]; }
    function addFx(l, fx) {                                   // the filters prep_ai.py took out of the SVG, as effects
        if (!fx || !l) return;
        var ep = l.property("ADBE Effect Parade");
        if (fx.shadow) {                                      // feDropShadow dy 8, stdDeviation 12, #222222 at 10 %
            var ds = ep.addProperty("ADBE Drop Shadow");
            ds.property("ADBE Drop Shadow-0001").setValue(hex("#222222"));
            var op = ds.property("ADBE Drop Shadow-0002");
            op.setValue(op.hasMax && op.maxValue > 100 ? 25.5 : 10);
            ds.property("ADBE Drop Shadow-0003").setValue(180);
            ds.property("ADBE Drop Shadow-0004").setValue(8);
            ds.property("ADBE Drop Shadow-0005").setValue(30);
        }
        if (fx.blur) {                                        // feGaussianBlur: AE's blurriness is about 2.5 x the SVG stdDeviation
            var gb = ep.addProperty("ADBE Gaussian Blur 2");
            gb.property(1).setValue(Math.round(fx.blur * 2.5));
        }
    }

    var CUR = null;                                          // the beat being built (for messages)
    function copyLayer(key, name, pre, newName, fx) {
        var c = importAI(key);
        if (!c) return null;
        var l = null;
        for (var i = 1; i <= c.numLayers; i++) if (c.layer(i).name === name) { l = c.layer(i); break; }
        if (!l) { report.missing.push(CUR + ": " + key + " :: " + name); return null; }
        var sel = pre.selectedLayers;
        for (var s = 0; s < sel.length; s++) sel[s].selected = false;
        l.copyToComp(pre);
        var n = pre.layer(1);
        n.name = newName || name; n.enabled = true;
        n.startTime = 0; n.inPoint = 0; n.outPoint = pre.duration;
        if (fx && fx.blur) n = roomy(pre, n);
        addFx(n, fx);
        return n;
    }
    var fGlow = null;
    function roomy(pre, l) {                                  // a cropped Illustrator layer clips its own blur to its box (v2's square glows):
        var r = rect(l), idx = l.index, nm = l.name;          // move it into a comp-size precomp and blur that instead
        var pc = pre.layers.precompose([idx], CUR + " " + nm.replace(/\//g, " ") + " glow", true);
        if (!fGlow) { fGlow = proj.items.addFolder("Glows"); fGlow.parentFolder = fBeats; }
        pc.parentFolder = fGlow;
        var n = pre.layer(idx);
        n.name = nm; n.comment = "rect:" + r.join(",");
        n.startTime = 0; n.inPoint = 0; n.outPoint = pre.duration;
        return n;
    }
    function toShapes(pre, l) {                               // vector layer -> shape layer (for Trim Paths); null if AE can't
        pre.openInViewer();
        var sl = pre.selectedLayers;
        for (var si = 0; si < sl.length; si++) sl[si].selected = false;
        l.selected = true;
        app.executeCommand(app.findMenuCommandId("Create Shapes from Vector Layer"));
        var sh = pre.selectedLayers.length ? pre.selectedLayers[0] : null;
        if (!sh || !(sh instanceof ShapeLayer)) return null;
        sh.selected = false;
        sh.name = l.name; sh.inPoint = l.inPoint; sh.outPoint = l.outPoint;
        l.remove();
        return sh;
    }
    function trim(sh) { return sh.property("ADBE Root Vectors Group").addProperty("ADBE Vector Filter - Trim"); }

    // ---------- actions ----------
    function wipe(l, a) {                                     // reveal with a mask that fits the layer
        var r = rect(l), P = 2, x0 = r[0] - P, y0 = r[1] - P, x1 = r[2] + P, y1 = r[3] + P, p = POS(l).value;
        var dir = a.dir || "ltr", t = a.t || 0, d = a.d || MO.snap_d;
        function shapeAt(e) {
            var A, B;
            if (dir === "ltr") { A = toLayer(l, x0, y0, p); B = toLayer(l, e, y1, p); }
            else if (dir === "rtl") { A = toLayer(l, e, y0, p); B = toLayer(l, x1, y1, p); }
            else if (dir === "ttb") { A = toLayer(l, x0, y0, p); B = toLayer(l, x1, e, p); }
            else { A = toLayer(l, x0, e, p); B = toLayer(l, x1, y1, p); }
            return boxShape(A[0], A[1], B[0], B[1]);
        }
        var from = { ltr: x0, rtl: x1, ttb: y0, btt: y1 }[dir], to = { ltr: x1, rtl: x0, ttb: y1, btt: y0 }[dir];
        var mp = addMask(l, "Wipe"), list = [[t, shapeAt(from)]];
        if (a.stops) {                                        // [[t, x], ...]: the edge reaches x at t (a strip printing up to a beat)
            var last = t, lastE = from, rate = 0;
            for (var i = 0; i < a.stops.length; i++) {
                list.push([a.stops[i][0], shapeAt(a.stops[i][1])]);
                rate = (a.stops[i][1] - lastE) / Math.max(0.05, a.stops[i][0] - last); last = a.stops[i][0]; lastE = a.stops[i][1];
            }
            list.push([last + Math.max(0.1, (to - lastE) / Math.max(1, rate)), shapeAt(to)]);
        } else list.push([t + d, shapeAt(to)]);
        if (a.linear) lin(mp, list); else cm(mp, list, "snap");
        cutIn(l, t);
        return list[list.length - 1][0];
    }
    function grow(l, a, t, d) {
        setPivot(l, pivotPoint(rect(l), a.pivot));
        cutIn(l, t);
        if (a.linear) lin(SC(l), [[t, [0, 0]], [t + d, [100, 100]]]);
        else if (a.over) CommaEase.overshoot(SC(l), t, [0, 0], [100, 100], d, MO.land_over, MO.land_back);
        else cm(SC(l), [[t, [0, 0]], [t + d, [100, 100]]], "snap");
    }
    function shrinkOut(l, t, d) {                             // collapses into its centre, accelerating into the cut
        setPivot(l, centre(rect(l)));
        cm(SC(l), [[t, [100, 100]], [t + d, [0, 0]]], "accel");
        cutOut(l, t + d);
    }
    function draw(pre, l, a, t, d) {                          // strokes draw on (rev: from the path's end), or off (off: true)
        var sh = toShapes(pre, l);
        if (!sh) { err(CUR + " " + a.layer + ": no shape layer made; cut on instead"); cutIn(l, t); return l; }
        var tr = trim(sh), S = tr.property("ADBE Vector Trim Start"), E = tr.property("ADBE Vector Trim End");
        var ease = a.linear ? function (p, lst) { lin(p, lst); } : function (p, lst) { cm(p, lst, a.off ? "accel" : "snap"); };
        if (a.off) {                                         // draws itself off, the way it drew on
            ease(S, [[t, 0], [t + d, 100]]);
            cutOut(sh, t + d);
        } else if (a.rev) { E.setValue(100); ease(S, [[t, 100], [t + d, 0]]); cutIn(sh, t); }
        else { ease(E, [[t, 0], [t + d, 100]]); cutIn(sh, t); }
        return sh;
    }
    function pulseLayer(pre, name, heart) {                   // the travelling pulse: amber dot in a soft amber halo (as the art's Diagram/Wave)
        var l = pre.layers.addShape(); l.name = name;
        var root = l.property("ADBE Root Vectors Group");
        var rr = [heart ? MO.halo_r_heart : MO.halo_r, heart ? MO.pulse_r_heart : MO.pulse_r], cols = [["#E3A33B", 35], ["#C9861F", 100]];
        for (var i = 0; i < 2; i++) {
            var g = root.addProperty("ADBE Vector Group"), vs = g.property("ADBE Vectors Group");
            vs.addProperty("ADBE Vector Shape - Ellipse").property("ADBE Vector Ellipse Size").setValue([rr[i] * 2, rr[i] * 2]);
            var f = vs.addProperty("ADBE Vector Graphic - Fill");
            f.property("ADBE Vector Fill Color").setValue(hex(cols[i][0])); f.property("ADBE Vector Fill Opacity").setValue(cols[i][1]);
        }
        ANC(l).setValue([0, 0]);
        return l;
    }
    function polyKeys(pts, t0, t1) {                          // times along a polyline at constant speed
        var L = [0], i;
        for (i = 1; i < pts.length; i++) { var dx = pts[i][0] - pts[i - 1][0], dy = pts[i][1] - pts[i - 1][1]; L.push(L[i - 1] + Math.sqrt(dx * dx + dy * dy)); }
        var tot = L[L.length - 1] || 1, ts = [], vs = [], step = Math.max(1, Math.floor(pts.length / Math.max(2, Math.round((t1 - t0) * PLAN.fps))));
        for (i = 0; i < pts.length; i += step) { ts.push(t0 + (t1 - t0) * L[i] / tot); vs.push(pts[i]); }
        if (ts[ts.length - 1] < t1 - 1e-4) { ts.push(t1); vs.push(pts[pts.length - 1]); }
        return [ts, vs];
    }
    function setLinear(prop, ts, vs) {
        prop.setValuesAtTimes(ts, vs);
        for (var k = 1; k <= prop.numKeys; k++) {
            prop.setInterpolationTypeAtKey(k, KeyframeInterpolationType.LINEAR, KeyframeInterpolationType.LINEAR);
            try { prop.setSpatialAutoBezierAtKey(k, false); prop.setSpatialContinuousAtKey(k, false); } catch (x) {}
        }
    }
    function lap(pre, a) {                                    // a pulse laps a loop at a constant rate, from t to t_end
        var l = pulseLayer(pre, a.name, a.heart), per = a.period, t0 = a.t - (a.offset || 0) * per;
        var kv = polyKeys(a.pts, t0, t0 + per);
        setLinear(POS(l), kv[0], kv[1]);
        POS(l).expression = 'loopOut("cycle")';
        l.inPoint = Math.max(0, a.t); l.outPoint = Math.min(pre.duration, a.t_end);
        if (a.t > 0.001) cm(SC(l), [[a.t, [0, 0]], [a.t + 0.3, [100, 100]]], "snap");     // the pulse grows on where the loop closes
        return l;
    }
    function travel(l, a) {                                   // the layer rides along paths (legs: [[pts, t0, t1], ...]) at a constant rate
        var c = centre(rect(l)), p0 = POS(l).value, ts = [], vs = [];
        for (var i = 0; i < a.legs.length; i++) {
            var kv = polyKeys(a.legs[i][0], a.legs[i][1], a.legs[i][2]);
            for (var j = 0; j < kv[0].length; j++) {
                if (ts.length && kv[0][j] <= ts[ts.length - 1] + 1e-4) continue;
                ts.push(kv[0][j]); vs.push([p0[0] + kv[1][j][0] - c[0], p0[1] + kv[1][j][1] - c[1]]);
            }
        }
        setLinear(POS(l), ts, vs);
        return l;
    }
    function carry(pre, bt, a) {                              // the previous version travels and resizes onto this one; the copies swap mid-move
        var d = a.d || MO.cross_d, t = a.t || 0;
        var o = copyLayer(bt.prev_ai, a.layer, pre, a.layer + " (carried)", a.fx);
        var l = copyLayer(bt.ai, a.layer, pre, null, a.fx); if (!l) return null;
        if (!o) return l;
        var R0 = rect(o), R1 = rect(l), c0 = centre(R0), c1 = centre(R1);
        var sx = (R1[2] - R1[0]) / Math.max(1, R0[2] - R0[0]), sy = (R1[3] - R1[1]) / Math.max(1, R0[3] - R0[1]);
        sx = sy = Math.min(sx, sy);
        setPivot(o, c0); setPivot(l, c1);
        cm(POS(o), [[t, c0], [t + d, c1]], "cross"); cm(SC(o), [[t, [100, 100]], [t + d, [sx * 100, sy * 100]]], "cross");
        cm(POS(l), [[t, c0], [t + d, c1]], "cross"); cm(SC(l), [[t, [100 / sx, 100 / sy]], [t + d, [100, 100]]], "cross");
        cutOut(o, t + d * 0.5); cutIn(l, t + d * 0.5);
        return l;
    }

    function doAct(pre, bt, a, l) {
        var t = a.t || 0, d;
        switch (a["do"]) {
        case "hold":
            return copyLayer(bt.ai, a.layer, pre, null, a.fx);
        case "cut":                                          // text cuts on whole on its word (and off at t_off: a 0.2 s fade for small labels)
            l = copyLayer(bt.ai, a.layer, pre, null, a.fx); if (!l) return null;
            cutIn(l, t);
            if (a.t_off !== undefined) { cm(OP(l), [[a.t_off, 100], [a.t_off + 0.2, 0]], "snap"); cutOut(l, a.t_off + 0.2); }
            return l;
        case "fade":                                         // small things only (leader lines): opacity over 0.2 s
            l = copyLayer(bt.ai, a.layer, pre, null, a.fx); if (!l) return null;
            cutIn(l, t); cm(OP(l), [[t, 0], [t + 0.2, 100]], "snap");
            return l;
        case "unfold":                                       // a card unfolds from its left edge, already in frame
            l = copyLayer(bt.ai, a.layer, pre, null, a.fx); if (!l) return null;
            d = a.d || MO.card_d;
            setPivot(l, pivotPoint(rect(l), "left")); cutIn(l, t);
            cm(SC(l), [[t, [0, 100]], [t + d, [100, 100]]], "snap");
            return l;
        case "grow":
            l = copyLayer(bt.ai, a.layer, pre, null, a.fx); if (!l) return null;
            grow(l, a, t, a.d || MO.grow_d);
            return l;
        case "wipe":
            l = copyLayer(bt.ai, a.layer, pre, null, a.fx); if (!l) return null;
            wipe(l, a);
            return l;
        case "draw":
            l = copyLayer(bt.ai, a.layer, pre, null, a.fx); if (!l) return null;
            return draw(pre, l, a, t, a.d || 0.6);
        case "swap":                                         // the previous version cuts to this one on t (no crossfade)
            var o = copyLayer(bt.prev_ai, a.layer, pre, a.layer + " (prev)", a.fx);
            cutOut(o, t);
            l = copyLayer(bt.ai, a.layer, pre, null, a.fx); if (!l) return null;
            cutIn(l, t);
            return l;
        case "carry":
            return carry(pre, bt, a);
        case "out":                                          // a layer of the previous beat leaves: cut, shrink into its centre, or draw off
        case "stay":                                         // ... or stays until t_end first
            var tt = a["do"] === "stay" ? a.t_end : t;
            o = copyLayer(bt.prev_ai, a.layer, pre, a.layer + " (out)", a.fx); if (!o) return l;
            if (a.how === "shrink") shrinkOut(o, tt, a.d || MO.accel_d);
            else if (a.how === "drawoff") draw(pre, o, { layer: a.layer, off: true }, tt, a.d || 0.3);
            else cutOut(o, tt);
            return l;
        case "opacity":
            if (!l) return l;
            var ks = [];
            for (var k = 0; k < a.keys.length; k++) ks.push([a.keys[k][0], a.keys[k][1]]);
            cm(OP(l), ks, "snap");
            return l;
        case "travel":
            l = l || copyLayer(bt.ai, a.layer, pre, null, a.fx); if (!l) return null;
            return travel(l, a);
        }
        err(bt.id + " unknown action " + a["do"]);
        return l;
    }

    function buildBeat(bt) {
        CUR = bt.id;
        var pre = proj.items.addComp(bt.id + " · " + bt.key.substr(bt.key.indexOf("_") + 1), PLAN.w, PLAN.h, 1, bt.dur, PLAN.fps);
        pre.parentFolder = fBeats;
        var by = {}, laps = [], i;
        for (i = 0; i < bt.acts.length; i++) {
            var a = bt.acts[i];
            if (a["do"] === "lap") { laps.push(a); continue; }
            (by[a.layer] = by[a.layer] || []).push(a);
        }
        // stack: each copy lands on top, so walking the art order bottom to top builds the stack. A layer of the previous beat
        // that leaves here goes in where it was in the previous beat's stack (just above the last layer both beats share)
        function run(name, list) {
            var l = null;
            for (var q = 0; q < list.length; q++) {
                try { l = doAct(pre, bt, list[q], l); } catch (x) { err(bt.id + " " + name + " (" + list[q]["do"] + "): " + String(x.message || x) + " line " + String(x.line)); l = null; }
            }
        }
        function leaving(list) { var o = [], r = []; for (var q = 0; q < list.length; q++) ((list[q]["do"] === "out" || list[q]["do"] === "stay") ? o : r).push(list[q]); return [o, r]; }
        var inCur = {}, after = {}, lastKept = "__bottom__";
        for (i = 0; i < bt.order.length; i++) inCur[bt.order[i]] = true;
        for (i = 0; i < bt.prev_order.length; i++) {
            var pn = bt.prev_order[i];
            if (inCur[pn]) { lastKept = pn; continue; }
            (after[lastKept] = after[lastKept] || []).push(pn);
        }
        function placeGone(k) { var g = after[k] || []; for (var q = 0; q < g.length; q++) run(g[q], leaving(by[g[q]] || [])[0]); }
        placeGone("__bottom__");
        for (i = 0; i < bt.order.length; i++) {
            var name = bt.order[i], parts = leaving(by[name] || []);
            if (parts[0].length) run(name, parts[0]);         // the previous version leaving, under the new one
            run(name, parts[1].length ? parts[1] : [{ layer: name, "do": "hold" }]);
            placeGone(name);
        }
        // pulses ride just above the loops they lap, under the node, tags and labels
        var top = null;
        for (i = pre.numLayers; i >= 1; i--) if (/^(Diagram\/(Halo|Channels|Slow|Fast|Stem|His|Active)|Heart\/(Base|Loop|AccessoryPathway|SmallLoop|FibrousRing))/.test(pre.layer(i).name)) top = pre.layer(i);
        for (i = 0; i < laps.length; i++) {
            try { var pl0 = lap(pre, laps[i]); if (top) pl0.moveBefore(top); else pl0.moveToBeginning(); }
            catch (x) { err(bt.id + " lap " + laps[i].name + ": " + String(x.message || x) + " line " + String(x.line)); }
        }
        report.beats.push({ beat: bt.id, layers: pre.numLayers });
        return pre;
    }

    // ---------- scenes and master ----------
    var full = null;
    try { full = proj.importFile(new ImportOptions(File(videoDir + "/3-board/audio/full.mp3"))); full.parentFolder = fAud; }
    catch (x) { err("audio full.mp3: " + x); }
    function mark(comp, t, label) { comp.markerProperty.setValueAtTime(t, new MarkerValue(label)); }
    var master = proj.items.addComp(PLAN.title, PLAN.w, PLAN.h, 1, PLAN.total, PLAN.fps);
    var sceneComps = [];
    for (var s = 0; s < PLAN.scenes.length; s++) {
        var S = PLAN.scenes[s];
        var sc = proj.items.addComp(S.name, PLAN.w, PLAN.h, 1, S.end - S.start, PLAN.fps);
        sc.parentFolder = fScenes;
        for (var b = 0; b < S.beats.length; b++) {
            var bt = S.beats[b], pre = buildBeat(bt), pl = sc.layers.add(pre);
            pl.startTime = bt.start - S.start;
            pl.moveToEnd();
        }
        if (full) { var al = sc.layers.add(full); al.name = "VO full.mp3"; al.startTime = -S.start; al.inPoint = 0; al.outPoint = sc.duration; }
        for (var m = 0; m < PLAN.markers.length; m++) {
            var M = PLAN.markers[m];
            if (M.t >= S.start && M.t < S.end) mark(sc, M.t - S.start, M.beat + " · " + M.cue);
        }
        var ml = master.layers.add(sc); ml.startTime = S.start; ml.moveToEnd();
        sceneComps.push(sc);
    }
    for (var m2 = 0; m2 < PLAN.markers.length; m2++) mark(master, PLAN.markers[m2].t, PLAN.markers[m2].beat + " · " + PLAN.markers[m2].cue);
    // every frame of the master shows a scene, and every frame of a scene shows a beat (no black frames at the cuts)
    report.gaps = [];
    function gaps(comp) {
        var n = Math.round(comp.duration * comp.frameRate);
        for (var fr = 0; fr < n; fr++) {
            var tt = fr / comp.frameRate, on = false;
            for (var li = 1; li <= comp.numLayers && !on; li++) { var L = comp.layer(li); if (L.hasVideo && L.activeAtTime(tt)) on = true; }
            if (!on) report.gaps.push(comp.name + " frame " + fr + " (" + tt.toFixed(3) + " s)");
        }
    }
    gaps(master);
    for (s = 0; s < sceneComps.length; s++) gaps(sceneComps[s]);
    proj.save(aep);

    // ---------- check frames: every beat start and sync point, and 0.9 s after each (where the move has landed) ----------
    var chk = Folder(buildDir + "/ae_check");
    if (!chk.exists) chk.create();
    var times = [];
    for (s = 0; s < PLAN.scenes.length; s++) for (b = 0; b < PLAN.scenes[s].beats.length; b++) {
        var B = PLAN.scenes[s].beats[b];
        times.push([B.start + 2 * FR, B.id + "_start"]); times.push([B.start + B.dur - 2 * FR, B.id + "_end"]);
    }
    for (m = 0; m < PLAN.markers.length; m++) { times.push([PLAN.markers[m].t, PLAN.markers[m].beat + "_" + PLAN.markers[m].cue]); times.push([PLAN.markers[m].t + 0.9, PLAN.markers[m].beat + "_" + PLAN.markers[m].cue + "_landed"]); }
    report.check_times = times.length;
    master.resolutionFactor = [2, 2];
    for (var c = 0; c < times.length; c++) {
        var tc = Math.min(PLAN.total - FR, times[c][0]);
        var fn = ("000" + tc.toFixed(2)).slice(-6) + "_" + times[c][1].replace(/[^A-Za-z0-9]+/g, "") + ".png";
        try { master.saveFrameToPng(tc, File(chk.fsName + "/" + fn)); report.checks.push(fn); }
        catch (x) { err("frame " + tc + ": " + x); }
    }
    master.resolutionFactor = [1, 1];
    proj.save(aep);
    master.openInViewer();
    function q(x) { return '"' + String(x).replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"'; }
    function arr(a) { var o = []; for (var i = 0; i < a.length; i++) o.push(typeof a[i] === "string" ? q(a[i]) : '{"beat":' + q(a[i].beat) + ',"layers":' + a[i].layers + '}'); return "[" + o.join(",") + "]"; }
    var out = File(buildDir + "/ae_build_report.json"); out.encoding = "UTF-8"; out.open("w");
    out.write('{"aep":' + q(aep.fsName) + ',"errors":' + arr(report.errors) + ',"missing":' + arr(report.missing) + ',"beats":' + arr(report.beats) + ',"gaps":' + arr(report.gaps) + ',"checks":' + report.checks.length + "}\n");
    out.close();
    return "built " + report.beats.length + " beats in " + PLAN.scenes.length + " scenes; errors " + report.errors.length + ", missing " + report.missing.length + ", gaps " + report.gaps.length;
})();
