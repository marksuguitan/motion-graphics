// build_ae.jsx — Oxygen Hemoglobin Curve, Stage 4 first build.
// Adapted from library/scripts/adobe/ae_engine.jsx (Pulsus Paradoxus): same import and layer-copy approach, new actions.
// Run in After Effects (File > Scripts > Run Script File...) after prep_ai.py, build_ai.jsx (Illustrator) and plan.py.
// Needs Settings > Scripting & Expressions > "Allow Scripts to Write Files and Access Network".
// Builds a new project from 4-animation/ai/<beat>.ai (imported as Composition – Retain Layer Sizes) and 3-board/audio/full.mp3:
//   Beats/<beat>          one precomp per beat, layers named as in the SVGs, every move keyed to its sync point
//   Scenes/Scene N · …    beat precomps at their start_in_full_s, full.mp3 laid in, a marker at every sync point
//   Oxygen Hemoglobin Curve   master comp, scenes in order (audio comes through the scenes), the same markers
// then saves 4-animation/Oxygen Hemoglobin Curve_v<N>.aep, a PNG of every beat start and sync point to build/ae_check/
// and build/ae_build_report.json. The plan is build/ae_plan.json (from plan.py): edit plan.py, not this file.
#target aftereffects
#include "../../../../library/scripts/adobe/comma_easing.jsx"
(function () {
    var buildDir = File($.fileName).parent.fsName;
    var animDir = Folder(buildDir).parent.fsName;                       // .../4-animation
    var videoDir = Folder(animDir).parent.fsName;
    var pf = File(buildDir + "/ae_plan.json"); pf.encoding = "UTF-8"; pf.open("r");
    var PLAN = eval("(" + pf.read() + ")"); pf.close();
    var VERSION = 8;                                        // v2: whole-frame starts; v3: red-purple cells; v4: 1B icons; v5: 1B→1C transition; v6: playful; v7: Comma Clinical; v8: no RBC squish, Mark's arm icon
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
    // Motion defaults: entrances ease out, moves across the frame ease in-out, exits ease in.
    var EASE = { out: [10, 85], inout: [60, 60], "in": [85, 10] };
    // Comma Clinical (Mark 2026-11-02): curves from library/scripts/adobe/comma_easing.jsx, amounts and durations from plan.py MOTION
    var MO = PLAN.motion;
    function cm(prop, list, kind) { return CommaEase.move(prop, list, kind || "snap"); }
    function isText(n) { return /^(Label|Title|Header|Note|Footnote|Takeaway|Zone)\//.test(n) || n === "Panel/Lines"; }
    function isCard(n) { return /^Panel\//.test(n) && n !== "Panel/Lines"; }
    function isShape(n) { return /^(Cell|Hb)\//.test(n) || /^(Cell\/Released|Marker\/P50)$/.test(n); }   // shapes: overshoot and squash allowed
    function cutIn(l, t) { if (t > 0.001) l.inPoint = Math.min(l.containingComp.duration - 1 / PLAN.fps, t); }
    function cutOut(l, t) { if (!l) return; if (t <= 0.001) { l.remove(); return; } l.outPoint = Math.min(l.containingComp.duration, t); }
    function keys(prop, list, kind) {                         // list: [[t, v], ...]; eases only the keys it sets
        for (var i = 0; i < list.length; i++) prop.setValueAtTime(list[i][0], list[i][1]);
        var e = EASE[kind || "inout"];
        var n = (prop.propertyValueType === PropertyValueType.TwoD_SPATIAL || prop.propertyValueType === PropertyValueType.ThreeD_SPATIAL ||
                 prop.propertyValueType === PropertyValueType.SHAPE) ? 1 : (prop.value instanceof Array ? prop.value.length : 1);
        for (i = 0; i < list.length; i++) {
            var k = prop.nearestKeyIndex(list[i][0]), a = [], b = [];
            for (var j = 0; j < n; j++) { a.push(new KeyframeEase(0, i === 0 ? 33 : e[1])); b.push(new KeyframeEase(0, i === list.length - 1 ? 33 : e[0])); }
            try { prop.setTemporalEaseAtKey(k, a, b); } catch (x) {}
        }
    }
    function rect(l) {                                        // comp-space bounds at rest (scale 100 %)
        var r = l.sourceRectAtTime(0, false), p = POS(l).value, a = ANC(l).value;
        return [p[0] - a[0] + r.left, p[1] - a[1] + r.top, p[0] - a[0] + r.left + r.width, p[1] - a[1] + r.top + r.height];
    }
    function setPivot(l, c) {                                 // anchor to comp point c without moving the art
        var a = ANC(l).value, p = POS(l).value;
        ANC(l).setValue([a[0] + c[0] - p[0], a[1] + c[1] - p[1]]); POS(l).setValue([c[0], c[1]]);
    }
    function centre(r) { return [(r[0] + r[2]) / 2, (r[1] + r[3]) / 2]; }
    function boxShape(x0, y0, x1, y1) {
        var s = new Shape(); s.vertices = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]];
        s.inTangents = [[0, 0], [0, 0], [0, 0], [0, 0]]; s.outTangents = [[0, 0], [0, 0], [0, 0], [0, 0]]; s.closed = true; return s;
    }
    function addMask(l, name) {
        var m = l.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
        m.name = name; m.property("ADBE Mask Feather").setValue([4, 4]);
        return m.property("ADBE Mask Shape");
    }
    function toLayer(l, x, y, p) { var a = ANC(l).value; return [x - p[0] + a[0], y - p[1] + a[1]]; }   // comp -> layer, at position p

    var CUR = null;                                          // the beat being built (for messages)
    var TOPS = [];                                           // layers that ride above the rest of their beat
    function copyLayer(key, name, pre, newName) {
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
        return n;
    }

    // ---------- actions ----------
    function fadeOut(o, t, d) { cutOut(o, t); }              // no crossfades between ideas: what leaves, cuts
    function wipe(l, a) {
        var r = rect(l), P = 6, x0 = r[0] - P, y0 = r[1] - P, x1 = r[2] + P, y1 = r[3] + P, p = POS(l).value;
        var stops = a.stops || [[a.t, null, a.d || 0.8]];
        var dir = a.dir, edge = { ltr: x0, rtl: x1, ttb: y0, btt: y1 }[dir];
        var mp = addMask(l, "Wipe");
        function shapeAt(e) {
            var A, B;
            if (dir === "ltr") { A = toLayer(l, x0, y0, p); B = toLayer(l, e, y1, p); }
            else if (dir === "rtl") { A = toLayer(l, e, y0, p); B = toLayer(l, x1, y1, p); }
            else if (dir === "ttb") { A = toLayer(l, x0, y0, p); B = toLayer(l, x1, e, p); }
            else { A = toLayer(l, x0, e, p); B = toLayer(l, x1, y1, p); }
            return boxShape(A[0], A[1], B[0], B[1]);
        }
        var list = [], last = edge;
        for (var i = 0; i < stops.length; i++) {
            var horiz = dir === "ltr" || dir === "rtl", to;
            if (stops[i][1] === null || i === stops.length - 1) to = { ltr: x1, rtl: x0, ttb: y1, btt: y0 }[dir];   // the last stop always finishes the reveal
            else to = horiz ? Math.max(x0, Math.min(x1, stops[i][1])) : Math.max(y0, Math.min(y1, stops[i][1]));
            list.push([stops[i][0], shapeAt(last)], [stops[i][0] + stops[i][2], shapeAt(to)]);
            last = to;
        }
        if (list[0][0] > 0) list.unshift([0, shapeAt(edge)]);
        cm(mp, list, "snap");
        return list[list.length - 1][0];
    }
    function clipKeys(l, clip, times, kind) {                      // a mask fixed in comp space while the layer moves
        var mp = addMask(l, "Graph clip"), list = [];
        for (var i = 0; i < times.length; i++) {
            var p = POS(l).valueAtTime(times[i], false);
            var A = toLayer(l, clip[0], clip[1], p), B = toLayer(l, clip[2], clip[3], p);
            list.push([times[i], boxShape(A[0], A[1], B[0], B[1])]);
        }
        cm(mp, list, kind || "snap");
    }


    // ---------- 1B -> 1C: the cells merge, the capillary grows into the card, the cell becomes a dot that writes the title ----------
    // Mark 2026-11-02 ("a sleek transition from scene 1 to the title"). Motion only; the art is unchanged. The title starts on its
    // measured cue ("oxyhemoglobin"); everything before it runs from the 1C start.
    function squash(l, t, d, dx, dy) {                      // shapes only: stretch along the move, 75/125 squash on impact, recover
        if (!MO.squash && !MO.stretch) return;
        var horiz = Math.abs(dx) >= Math.abs(dy), st = MO.stretch;
        var b = SC(l).numKeys ? SC(l).valueAtTime(t + d, false) : [100, 100];
        var S1 = horiz ? [b[0] * (1 + st), b[1] * (1 - st)] : [b[0] * (1 - st), b[1] * (1 + st)];
        cm(SC(l), [[t + 0.5 * d, S1]], "snap");
        CommaEase.squash(SC(l), t + d, b, horiz ? 0 : 1, MO.squash);
    }
    function shapeLayer(pre, name, kind, size, pos, fill, stroke, sw, round) {
        var l = pre.layers.addShape(); l.name = name;
        var root = function () { return l.property("ADBE Root Vectors Group"); };
        root().addProperty("ADBE Vector Group");
        var vs = function () { return root().property(1).property("ADBE Vectors Group"); };
        vs().addProperty(kind === "rect" ? "ADBE Vector Shape - Rect" : "ADBE Vector Shape - Ellipse");
        vs().addProperty("ADBE Vector Graphic - Fill");
        if (stroke) vs().addProperty("ADBE Vector Graphic - Stroke");
        var sh = vs().property(1);
        sh.property(kind === "rect" ? "ADBE Vector Rect Size" : "ADBE Vector Ellipse Size").setValue(size);
        if (kind === "rect") sh.property("ADBE Vector Rect Roundness").setValue(round);
        vs().property(2).property("ADBE Vector Fill Color").setValue(fill);
        if (stroke) { vs().property(3).property("ADBE Vector Stroke Color").setValue(stroke); vs().property(3).property("ADBE Vector Stroke Width").setValue(sw); }
        ANC(l).setValue([0, 0]); POS(l).setValue(pos);
        return { layer: l, shape: function () { return vs().property(1); }, fill: function () { return vs().property(2); }, stroke: function () { return vs().property(3); } };
    }
    function hex(h) { return [parseInt(h.substr(1, 2), 16) / 255, parseInt(h.substr(3, 2), 16) / 255, parseInt(h.substr(5, 2), 16) / 255]; }
    function title1c(pre, bt, a) {
        var c = a.t, M = a.merge, CAP = a.capsule, DOT = a.dot, W = a.write;     // times (beat-local) from the plan
        var mid = [960, 540];
        // capsule -> card (replaces the capillary art at the same size and colours): accelerates into the swap, settles out of it
        var cap = shapeLayer(pre, "Capillary → card", "rect", [1640, 220], mid, hex("#F6E7E4"), hex("#E7C9C3"), 4, 110);
        var C0 = CAP[0], C1 = CAP[0] + CAP[1];
        cm(cap.shape().property("ADBE Vector Rect Size"), [[C0, [1640, 220]], [C1, [1728, 780]]], "snap");
        cm(cap.shape().property("ADBE Vector Rect Roundness"), [[C0, 110], [C1, 24]], "snap");
        cm(cap.fill().property("ADBE Vector Fill Color"), [[C0, hex("#F6E7E4")], [C1, [1, 1, 1]]], "snap");
        cm(cap.stroke().property("ADBE Vector Stroke Opacity"), [[C0, 100], [C1, 0]], "snap");
        cap.layer.outPoint = Math.min(pre.duration, C1 + 0.1);
        // the two cells cross to the centre and become one: the red-purple one is swapped out as they overlap
        var cells = [["Cell/Tissues", 0.75], ["Cell/Lungs", 1]];
        for (var i = 0; i < cells.length; i++) {
            var cl = copyLayer(bt.prev_ai, cells[i][0], pre, cells[i][0] + " (merging)");
            if (!cl) continue;
            var cc = centre(rect(cl)); setPivot(cl, cc);
            cm(POS(cl), [[M[0], cc], [M[0] + M[1], mid]], "cross");
            cm(SC(cl), [[M[0], [100, 100]], [M[0] + M[1], [80, 80]]], "cross");
            cutOut(cl, M[0] + M[1] * cells[i][1]);
        }
        // title lines: two copies of Title/Text, each masked to one line; line 1 is written by the dot, line 2 cuts on whole
        var t1 = copyLayer(bt.ai, "Title/Text", pre, "Title/Text line 1"), t2 = copyLayer(bt.ai, "Title/Text", pre, "Title/Text line 2");
        if (!t1 || !t2) return t1;
        var R = rect(t1), split = (R[1] + R[3]) / 2, P = 8, y1 = (R[1] + split) / 2;
        var p1 = POS(t1).value, A = toLayer(t1, R[0] - P, R[1] - P, p1), B = toLayer(t1, R[2] + P, split, p1);
        addMask(t1, "Line 1").setValue(boxShape(A[0], A[1], B[0], B[1]));
        wipe(t1, { dir: "ltr", t: c, d: W });
        t1.property("ADBE Mask Parade").property(2).maskMode = MaskMode.INTERSECT;
        var p2 = POS(t2).value, C2 = toLayer(t2, R[0] - P, split, p2), D2 = toLayer(t2, R[2] + P, R[3] + P, p2);
        addMask(t2, "Line 2").setValue(boxShape(C2[0], C2[1], D2[0], D2[1]));
        cutIn(t2, c + a.line2);
        // the merged cell shrinks to a 14 px dot at the start of line 1, waits, then leads the wipe and is gone as the line completes
        var x0 = R[0] - 18, x1 = R[2] + 6;
        var dot = shapeLayer(pre, "Cell → dot", "ellipse", [176, 112], mid, hex("#C94A44"));
        cutIn(dot.layer, M[0] + M[1]);
        if (MO.squash) CommaEase.squash(SC(dot.layer), M[0] + M[1], [100, 100], 0, MO.squash);   // the two cells land as one
        cm(dot.shape().property("ADBE Vector Ellipse Size"), [[DOT[0], [176, 112]], [DOT[0] + DOT[1], [14, 14]]], "snap");
        cm(POS(dot.layer), [[DOT[0], mid], [DOT[0] + DOT[1], [x0, y1]]], "cross");
        cm(POS(dot.layer), [[c, [x0, y1]], [c + W, [x1, y1]]], "snap");
        cutOut(dot.layer, c + W);
        return t2;
    }

    function buildBeat(bt) {
        CUR = bt.id;
        var pre = proj.items.addComp(bt.id + " · " + bt.key.substr(bt.key.indexOf("_") + 1), PLAN.w, PLAN.h, 1, bt.dur, PLAN.fps);
        pre.parentFolder = fBeats;
        var by = {}, gone = [], i, j;
        for (i = 0; i < bt.acts.length; i++) {
            var a = bt.acts[i];
            (by[a.layer] = by[a.layer] || []).push(a);
        }
        // layers that leave in this beat sit where they were in the previous beat's stack
        var after = {}, inCur = {};
        for (i = 0; i < bt.order.length; i++) inCur[bt.order[i]] = true;
        var lastKept = "__bottom__";
        for (i = 0; i < bt.prev_order.length; i++) {
            var pn = bt.prev_order[i];
            if (inCur[pn]) { lastKept = pn; continue; }
            var outs = by[pn] || [];
            for (j = 0; j < outs.length; j++) if (outs[j]["do"] === "out") (after[lastKept] = after[lastKept] || []).push(outs[j]);
        }
        function placeGone(k) {
            var g = after[k] || [];
            for (var q = 0; q < g.length; q++) {
                try { fadeOut(copyLayer(bt.prev_ai, g[q].layer, pre, g[q].layer + " (out)"), g[q].t, g[q].d || 0.4); }
                catch (x) { err(bt.id + " out " + g[q].layer + ": " + x); }
            }
        }
        placeGone("__bottom__");
        for (i = 0; i < bt.order.length; i++) {
            var name = bt.order[i], acts = by[name] || [{ layer: name, "do": "hold" }], l = null;
            for (j = 0; j < acts.length; j++) {
                try { l = doAct(pre, bt, acts[j], l); } catch (x) { err(bt.id + " " + name + " (" + acts[j]["do"] + "): " + String(x.message) + " line " + String(x.line)); l = null; }
            }
            placeGone(name);
        }
        for (i = TOPS.length - 1; i >= 0; i--) TOPS[i].moveToBeginning();
        TOPS = [];
        report.beats.push({ beat: bt.id, layers: pre.numLayers });
        return pre;
    }

    function doAct(pre, bt, a, l) {
        var t = a.t || 0, d, p, o, r;
        switch (a["do"]) {
        case "hold":
            return copyLayer(bt.ai, a.layer, pre);
        case "in":
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            d = a.d || MO.snap_d;
            if (isText(a.layer)) { cutIn(l, t); return l; }                    // text cuts on whole on its sync word
            if (isCard(a.layer)) {                                             // cards unfold from their left edge, already in frame
                r = rect(l); setPivot(l, [r[0], (r[1] + r[3]) / 2]);
                cutIn(l, t); cm(SC(l), [[t, [0, 100]], [t + d, [100, 100]]], "snap");
                return l;
            }
            if (/^(Cell\/Released|Marker\/P50|Readout\/)/.test(a.layer)) {   // small things grow from a point
                setPivot(l, centre(rect(l))); cutIn(l, t);
                if (isShape(a.layer)) CommaEase.overshoot(SC(l), t, [0, 0], [100, 100], d, MO.land_over, MO.land_back);
                else cm(SC(l), [[t, [0, 0]], [t + d, [100, 100]]], "snap");
                return l;
            }
            cm(OP(l), [[t, 0], [t + d, 100]], "snap");                         // graph pieces and areas: plain snap and settle
            return l;
        case "pop":
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            if (isText(a.layer)) { cutIn(l, t); return l; }
            d = a.d || MO.snap_d;
            setPivot(l, centre(rect(l))); cutIn(l, t);
            CommaEase.overshoot(SC(l), t, [0, 0], [100, 100], d, MO.land_over, MO.land_back);   // grows from a point, lands with one rebound
            return l;
        case "wipe":
            d = 0;
            if (a.keep) o = copyLayer(bt.prev_ai, a.layer, pre, a.layer + " (prev)");
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            var tEnd = wipe(l, a);
            if (o) o.outPoint = Math.min(pre.duration, tEnd + 0.04);
            return l;
        case "xfade":                                        // no crossfades between ideas: a clean cut on the cue
            o = copyLayer(bt.prev_ai, a.layer, pre, a.layer + " (prev)");
            cutOut(o, t);
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            cutIn(l, t);
            return l;
        case "leave":                                        // a layer of this beat collapses before the cut, accelerating into it
            if (!l) return l;
            d = a.d || MO.accel_d;
            var ls = SC(l).valueAtTime(t, false);
            setPivot(l, centre(rect(l)));
            cm(SC(l), [[t, ls], [t + d, [0, 0]]], "accel");
            cutOut(l, t + d);
            return l;
        case "bob":                                          // gentle idle bob while a cell sits still (fades in and out of the window)
            if (!l) return l;
            var t0 = a.t, t1 = a.t_end;
            POS(l).expression = "var t0=" + t0 + ", t1=" + t1 + ", A=" + MO.bob_px + ", T=" + MO.bob_period + ";\n" +
                "var k = Math.max(0, Math.min(1, (time - t0) / 0.4, (t1 - time) / 0.4));\n" +
                "value + [0, A * k * Math.sin(2 * Math.PI * (time - t0) / T)];";
            return l;
        case "ping":                                         // emphasis: one short ring snap at a point (the art itself is not scaled)
            var ring = shapeLayer(pre, (a.layer || "") + " ping", "ellipse", [a.r * 2, a.r * 2], a.c, [1, 1, 1], hex(a.col || "#F0645A"), 4);
            ring.fill().property("ADBE Vector Fill Opacity").setValue(0);
            cm(SC(ring.layer), [[t, [100, 100]], [t + MO.ping_d, [100 * MO.ring, 100 * MO.ring]]], "snap");
            cm(OP(ring.layer), [[t, 100], [t + MO.ping_d, 0]], "snap");
            ring.layer.inPoint = Math.max(0, t); ring.layer.outPoint = Math.min(pre.duration, t + MO.ping_d + 0.04);
            return l;
        case "drop":                                         // factor chips grow from their slot, one per cue
            var first = null;
            for (var ri = 0; ri < a.rows.length; ri++) {
                var row = copyLayer(bt.ai, a.layer, pre, a.layer + " row " + (ri + 1));
                if (!row) continue;
                var RR = rect(row), rp = POS(row).value, y0 = a.rows[ri][1], y1 = a.rows[ri][2], tr = a.rows[ri][0];
                var U = toLayer(row, RR[0] - 8, y0, rp), V = toLayer(row, RR[2] + 8, y1, rp);
                addMask(row, "Row").setValue(boxShape(U[0], U[1], V[0], V[1]));
                setPivot(row, [RR[0], (y0 + y1) / 2]);                                       // the chip's slot starts at the card's text edge
                cutIn(row, tr);
                cm(SC(row), [[tr, [0, 0]], [tr + MO.snap_d, [100, 100]]], "snap");
                if (!first) first = row;
            }
            return first;
        case "gone":                                         // left in the previous beat or handed to a custom move: nothing to copy
            return l;
        case "title1c":
            return title1c(pre, bt, a);
        case "out":                                          // same name: the previous version leaves (cut), a new one follows
            fadeOut(copyLayer(bt.prev_ai, a.layer, pre, a.layer + " (out)"), t);
            return l;
        case "carry":                                        // travels and resizes onto its new form; the copies swap mid-move
            d = a.d || MO.cross_d;
            o = copyLayer(bt.prev_ai, a.prev || a.layer, pre, (a.prev || a.layer) + " (carried)");
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            if (!o) return l;
            var R0 = rect(o), R1 = rect(l), c0 = centre(R0), c1 = centre(R1);
            var sx = (R1[2] - R1[0]) / (R0[2] - R0[0]), sy = (R1[3] - R1[1]) / (R0[3] - R0[1]);
            if (a.fit === "w") sy = sx;
            else if (a.uniform !== false) { sx = sy = Math.min(sx, sy); }
            if (a.top) TOPS.push(o, l);
            setPivot(o, c0); setPivot(l, c1);
            var tm = t, dx = c1[0] - c0[0], dy = c1[1] - c0[1], len = Math.sqrt(dx * dx + dy * dy) || 1;
            if (a.anticipate) {                              // a short counter-move before a big move
                var back = [c0[0] - dx / len * MO.anticipation_px, c0[1] - dy / len * MO.anticipation_px];
                cm(POS(o), [[t, c0], [t + MO.anticipation_d, back]], "anti");
                cm(POS(l), [[t, c0], [t + MO.anticipation_d, back]], "anti");
                tm = t + MO.anticipation_d;
            }
            var startO = a.anticipate ? [c0[0] - dx / len * MO.anticipation_px, c0[1] - dy / len * MO.anticipation_px] : c0;
            cm(POS(o), [[tm, startO], [tm + d, c1]], "cross"); cm(SC(o), [[tm, [100, 100]], [tm + d, [sx * 100, sy * 100]]], "cross");
            cm(POS(l), [[tm, startO], [tm + d, c1]], "cross"); cm(SC(l), [[tm, [100 / sx, 100 / sy]], [tm + d, [100, 100]]], "cross");
            cutOut(o, tm + d * 0.5); cutIn(l, tm + d * 0.5);
            if (a.squash) squash(l, tm, d, dx, dy);
            return l;
        case "slidein":                                      // starts in frame (overlapping what it grows from) and moves into place
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            d = a.d || MO.snap_d; p = POS(l).value;
            var kind = a.squash ? "cross" : "snap";
            cm(POS(l), [[t, [p[0] + a.dx, p[1] + a.dy]], [t + d, p]], kind);
            cutIn(l, t);
            if (a.squash) squash(l, t, d, a.dx, a.dy);
            if (a.clip) clipKeys(l, a.clip, [t, t + d], kind);
            return l;
        case "nudge":
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            p = POS(l).value;
            var nk = [], nt = [];
            for (var k = 0; k < a.keys.length; k++) { nk.push([a.keys[k][0], [p[0] + a.keys[k][1], p[1]]]); nt.push(a.keys[k][0]); }
            cm(POS(l), nk, "snap");
            if (a.clip) clipKeys(l, a.clip, nt, "snap");
            return l;
        case "draw":                                         // stroke draw-on: vector layer -> shape layer + Trim Paths
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            d = a.d || 0.6;
            pre.openInViewer();
            var sl = pre.selectedLayers;
            for (var si = 0; si < sl.length; si++) sl[si].selected = false;
            l.selected = true;
            app.executeCommand(app.findMenuCommandId("Create Shapes from Vector Layer"));
            var sh = pre.selectedLayers.length ? pre.selectedLayers[0] : null;
            if (!sh || !(sh instanceof ShapeLayer)) { err(bt.id + " " + a.layer + ": no shape layer made; fading in instead"); keys(OP(l), [[t, 0], [t + d, 100]], "out"); return l; }
            sh.selected = false;
            l.remove();
            sh.name = a.layer;
            var tr = sh.property("ADBE Root Vectors Group").addProperty("ADBE Vector Filter - Trim");
            cm(tr.property("ADBE Vector Trim End"), [[t, 0], [t + d, 100]], "snap");
            return sh;
        case "bump":
            if (!l) return l;
            r = rect(l);
            var sp = SC(l), base = sp.numKeys ? sp.valueAtTime(t, false) : [100, 100];
            if (!sp.numKeys) setPivot(l, centre(r));
            var bs = a.pulse ? MO.pulse_scale : (a.s || 1.03), bd = a.pulse ? MO.pulse_d : (a.d || 0.4);
            cm(sp, [[t, base], [t + bd * 0.4, [base[0] * bs, base[1] * bs]], [t + bd, base]], "snap");
            return l;
        }
        err(bt.id + " unknown action " + a["do"]);
        return l;
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
            if (M.t >= S.start && M.t < S.end) mark(sc, M.t - S.start, M.beat + " · " + M.cue + (M.flag ? " (" + M.flag + ")" : ""));
        }
        var ml = master.layers.add(sc); ml.startTime = S.start; ml.moveToEnd();
        sceneComps.push(sc);
    }
    for (var m2 = 0; m2 < PLAN.markers.length; m2++) {
        var M2 = PLAN.markers[m2];
        mark(master, M2.t, M2.beat + " · " + M2.cue + (M2.flag ? " (" + M2.flag + ")" : ""));
    }
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

    // ---------- check frames: every beat start and sync point ----------
    var chk = Folder(buildDir + "/ae_check");
    if (!chk.exists) chk.create();
    var times = [];
    for (s = 0; s < PLAN.scenes.length; s++) for (b = 0; b < PLAN.scenes[s].beats.length; b++) times.push([PLAN.scenes[s].beats[b].start, PLAN.scenes[s].beats[b].id + "_start"]);
    for (m = 0; m < PLAN.markers.length; m++) times.push([PLAN.markers[m].t, PLAN.markers[m].beat + "_" + PLAN.markers[m].cue]);
    report.check_times = times.length;
    var tf = File(buildDir + "/ae_check_times.json"); tf.encoding = "UTF-8"; tf.open("w");
    var tl = []; for (var c = 0; c < times.length; c++) tl.push('[' + times[c][0] + ',"' + times[c][1] + '"]');
    tf.write("[" + tl.join(",\n") + "]"); tf.close();

    master.resolutionFactor = [2, 2];
    for (c = 0; c < times.length; c++) {
        var fn = ("000" + times[c][0].toFixed(2)).slice(-6) + "_" + times[c][1].replace(/[^A-Za-z0-9]+/g, "") + ".png";
        try { master.saveFrameToPng(times[c][0], File(chk.fsName + "/" + fn)); report.checks.push(fn); }
        catch (x) { err("frame " + times[c][0] + ": " + x); }
    }
    master.resolutionFactor = [1, 1];
    proj.save(aep);
    sceneComps[0].openInViewer();
    function q(x) { return '"' + String(x).replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"'; }
    function arr(a) { var o = []; for (var i = 0; i < a.length; i++) o.push(typeof a[i] === "string" ? q(a[i]) : '{"beat":' + q(a[i].beat) + ',"layers":' + a[i].layers + '}'); return "[" + o.join(",") + "]"; }
    var out = File(buildDir + "/ae_build_report.json"); out.encoding = "UTF-8"; out.open("w");
    out.write('{"aep":' + q(aep.fsName) + ',"errors":' + arr(report.errors) + ',"missing":' + arr(report.missing) + ',"beats":' + arr(report.beats) + ',"gaps":' + arr(report.gaps) + "}\n");
    out.close();
    return "built " + report.beats.length + " beats in " + PLAN.scenes.length + " scenes; errors " + report.errors.length + ", missing " + report.missing.length;
})();
