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
    var VERSION = 22;                                        // v2: whole-frame starts; v3: red-purple cells; v4: 1B icons; v5: 1B→1C transition; v6: playful; v7: Comma Clinical; v8: no RBC squish, Mark's arm icon; v9: Scene 2 notes; v10: Scene 3 notes; v11: 3->4 pause; v12: point wipe stops; v13: side-card roll; v14: card pauses; v15: 3B-3D; v16: shorter 3D pause; v17: 6B labels; v18: 7A arrows; v19: Mark's markers, Scene 10 sync; v20: 9D locks; v21: charcoal locks; v22: end screen B
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
    function rollLayer(L, t, clip) {                         // rolls up out of a card's inner area, accelerating, clipped
        var rp0 = POS(L).valueAtTime(t, false), d = Math.max(0.1, MO.card_out_d - 0.05);
        cm(POS(L), [[t, rp0], [t + d, [rp0[0], rp0[1] - MO.card_rise]]], "accel");
        var nm = L.property("ADBE Mask Parade").numProperties;
        clipKeys(L, [clip[0] + 3, clip[1] + 3, clip[0] + clip[2] - 3, clip[1] + clip[3] - 3], [t, t + d], "accel");
        if (nm > 0) L.property("ADBE Mask Parade").property(nm + 1).maskMode = MaskMode.INTERSECT;
        cutOut(L, t + d);
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
                try {
                    var go = copyLayer(bt.prev_ai, g[q].layer, pre, g[q].layer + " (out)");
                    if (go && g[q].grey) {                    // it left the previous beat greyed: keep it grey
                        var gfx = go.property("ADBE Effect Parade").addProperty("ADBE Tint"); gfx.name = "Grey";
                        gfx.property("ADBE Tint-0001").setValue(hex("#B9B5AE").concat([1])); gfx.property("ADBE Tint-0002").setValue(hex("#B9B5AE").concat([1]));
                        gfx.property("ADBE Tint-0003").setValue(100);
                    }
                    if (go && g[q].shift) {                   // held where the previous beat left it (e.g. an O2 that travelled and bound)
                        var gp = POS(go).value, gr = rect(go);
                        if (g[q].label_y !== undefined) {    // its label was switched off on landing: keep it off
                            var GU = toLayer(go, gr[0] - 10, gr[1] - 10, gp), GV = toLayer(go, gr[2] + 10, g[q].label_y, gp);
                            var gm = go.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
                            gm.maskMode = MaskMode.SUBTRACT; gm.property("ADBE Mask Shape").setValue(boxShape(GU[0], GU[1], GV[0], GV[1]));
                        }
                        POS(go).setValue([gp[0] + g[q].shift[0], gp[1] + g[q].shift[1]]);
                    }
                    if (go && g[q].retract) {                 // retracts the way it drew on, accelerating into the cut
                        var rr = rect(go), rp0 = POS(go).value, P0 = 6, D = g[q].retract;
                        var x0 = rr[0] - P0, y0 = rr[1] - P0, x1 = rr[2] + P0, y1 = rr[3] + P0;
                        var shut = { rtl: [x0, y0, x0, y1], ltr: [x1, y0, x1, y1], ttb: [x0, y1, x1, y1], btt: [x0, y0, x1, y0] }[D];
                        var A0 = toLayer(go, x0, y0, rp0), B0 = toLayer(go, x1, y1, rp0), A1 = toLayer(go, shut[0], shut[1], rp0), B1 = toLayer(go, shut[2], shut[3], rp0);
                        cm(addMask(go, "Retract"), [[g[q].t, boxShape(A0[0], A0[1], B0[0], B0[1])], [g[q].t + MO.accel_d, boxShape(A1[0], A1[1], B1[0], B1[1])]], "accel");
                        cutOut(go, g[q].t + MO.accel_d);
                    } else if (go && g[q].roll) {             // lived in the side card: rolls out with the card's old rows
                        rollLayer(go, g[q].t, g[q].roll);
                    } else if (go && g[q].to) {               // collapses into a point, accelerating into the cut
                        setPivot(go, g[q].to);
                        cm(SC(go), [[g[q].t, [100, 100]], [g[q].t + MO.accel_d, [0, 0]]], "accel");
                        cutOut(go, g[q].t + MO.accel_d);
                    } else fadeOut(go, g[q].t, g[q].d || 0.4);
                }
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
        if (bt.post) for (i = 0; i < bt.post.length; i++) {   // moves on several finished layers at once (after the stack is built)
            try { doAct(pre, bt, bt.post[i], null); } catch (x) { err(bt.id + " post " + bt.post[i]["do"] + ": " + String(x.message) + " line " + String(x.line)); }
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
            if (isText(a.layer) || a.cut || /^O2\/Label/.test(a.layer)) { cutIn(l, t); if (a.t_out) cutOut(l, a.t_out); return l; }   // text cuts on whole on its sync word
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
            if (a.plain) { cm(SC(l), [[t, [0, 0]], [t + d, [100, 100]]], "snap"); return l; }   // diagrams grow without overshoot
            CommaEase.overshoot(SC(l), t, [0, 0], [100, 100], d, a.over === undefined ? MO.land_over : a.over, MO.land_back);   // grows from a point, lands with one rebound
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
        case "rings":                                        // quick circles that draw on around points, then draw themselves out
            for (var gi = 0; gi < a.c.length; gi++) {
                var tg = t + gi * a.stagger, rg = shapeLayer(pre, "Ring " + (gi + 1), "ellipse", [a.r * 2, a.r * 2], a.c[gi], [1, 1, 1], hex(a.col), a.w || 6);
                rg.fill().property("ADBE Vector Fill Opacity").setValue(0);
                var tm = rg.layer.property("ADBE Root Vectors Group").addProperty("ADBE Vector Filter - Trim");
                cm(tm.property("ADBE Vector Trim End"), [[tg, 0], [tg + a.d, 100]], "snap");
                cm(tm.property("ADBE Vector Trim Start"), [[a.t_off + gi * a.stagger, 0], [a.t_off + gi * a.stagger + a.d, 100]], "accel");
                rg.layer.inPoint = tg; rg.layer.outPoint = Math.min(pre.duration, a.t_off + gi * a.stagger + a.d + 0.04);
            }
            return l;
        case "fly":                                          // appears at `from`, then travels to its place in the art (scaling to 100 %)
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            var fc = centre(rect(l)); setPivot(l, fc); cutIn(l, t);
            POS(l).setValue(a.from); SC(l).setValue([a.s0 * 100, a.s0 * 100]);
            cm(POS(l), [[a.t_go, a.from], [a.t_go + a.d, fc]], "cross");
            cm(SC(l), [[a.t_go, [a.s0 * 100, a.s0 * 100]], [a.t_go + a.d, [100, 100]]], "cross");
            return l;
        case "flyto":                                        // copies of another beat's layer travel from `from` to each target, one after another
            for (var fi = 0; fi < a.to.length; fi++) {
                var fl = copyLayer(a.src_ai, a.src_layer, pre, a.src_layer + " " + (fi + 2));
                if (!fl) continue;
                var fcc = centre(rect(fl)); setPivot(fl, fcc);
                var tf = t + fi * a.stagger; cutIn(fl, tf);
                POS(fl).setValue(a.from); SC(fl).setValue([a.s0 * 100, a.s0 * 100]);
                cm(POS(fl), [[tf, a.from], [tf + a.d, a.to[fi]]], "snap");
                cm(SC(fl), [[tf, [a.s0 * 100, a.s0 * 100]], [tf + a.d, [100, 100]]], "snap");
            }
            return l;
        case "o2":                                           // an O2 grows in at its spot, then travels to `to` (molecule centre); its label is masked off on landing
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            setPivot(l, a.mol); cutIn(l, t);
            cm(SC(l), [[t, [0, 0]], [t + MO.snap_d * 0.6, [100, 100]]], "snap");
            var pm = POS(l).value, tgt = [pm[0] + a.to[0] - a.mol[0], pm[1] + a.to[1] - a.mol[1]];
            cm(POS(l), [[a.t_go, pm], [a.t_go + a.d, tgt]], a.kind || "cross");
            if (a.label_y !== undefined) {                   // everything above label_y is the label: a subtract mask switches on at landing
                var rl = rect(l), U2 = toLayer(l, rl[0] - 10, rl[1] - 10, pm), V2 = toLayer(l, rl[2] + 10, a.label_y, pm);
                var mk = l.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
                mk.name = "Label off"; mk.maskMode = MaskMode.SUBTRACT;
                var ms = mk.property("ADBE Mask Shape");                    // empty until landing, then covers the label (hold keys)
                ms.setValueAtTime(0, boxShape(U2[0], U2[1], U2[0] + 0.01, U2[1] + 0.01));
                ms.setValueAtTime(a.t_go + a.d, boxShape(U2[0], U2[1], V2[0], V2[1]));
                ms.setInterpolationTypeAtKey(1, KeyframeInterpolationType.HOLD, KeyframeInterpolationType.HOLD);
            }
            return l;
        case "cardswap":                                     // side-card content rolls: old rows up and out, new rows up and in, clipped to the card
            var CS = MO.card_stagger, RISE = MO.card_rise;
            var OR = a.old.rect, NR = a.new.rect, nOld = a.old.rows.length, nNew = a.new.rows.length;
            var outD = Math.max(0.1, MO.card_out_d - (nOld - 1) * CS);
            var tDone = a.t_new + (nNew - 1) * CS + MO.card_in_d;
            function ctr(R) { return [R[0] + R[2] / 2, R[1] + R[3] / 2]; }
            // the card itself: a plain white card (and its soft shadow) under the moving rows; its height morphs old -> new
            var shd = shapeLayer(pre, "Card shadow (swap)", "rect", [OR[2], OR[3]], [ctr(OR)[0], ctr(OR)[1] + 8], hex("#222222"), null, 0, 24);
            OP(shd.layer).setValue(8);
            shd.layer.property("ADBE Effect Parade").addProperty("ADBE Gaussian Blur 2").property(1).setValue(24);
            var bse = shapeLayer(pre, "Card (swap)", "rect", [OR[2], OR[3]], ctr(OR), [1, 1, 1], null, 0, 24);
            var parts = [shd, bse], tBase0 = a.phase === "in" ? 0 : a.t, tBase1 = a.phase === "out" ? pre.duration : tDone;
            for (var bi = 0; bi < parts.length; bi++) {
                var dyb = bi === 0 ? 8 : 0;
                if (a.phase !== "out" && (OR[3] !== NR[3] || OR[1] !== NR[1])) {
                    cm(parts[bi].shape().property("ADBE Vector Rect Size"), [[a.t_new, [OR[2], OR[3]]], [a.t_new + MO.card_in_d, [NR[2], NR[3]]]], "snap");
                    cm(POS(parts[bi].layer), [[a.t_new, [ctr(OR)[0], ctr(OR)[1] + dyb]], [a.t_new + MO.card_in_d, [ctr(NR)[0], ctr(NR)[1] + dyb]]], "snap");
                }
                parts[bi].layer.inPoint = Math.max(0, tBase0); parts[bi].layer.outPoint = Math.min(pre.duration, tBase1);
            }
            function rowCopy(src, R, band, label) {
                var rc = copyLayer(src, "Panel/Card", pre, "Panel/Card " + label); if (!rc) return null;
                var rp = POS(rc).value, A1 = toLayer(rc, R[0] + 2, band[0], rp), B1 = toLayer(rc, R[0] + R[2] - 2, band[1], rp);
                addMask(rc, "Row").setValue(boxShape(A1[0], A1[1], B1[0], B1[1]));
                return rc;
            }
            function clipRow(rc, R, t0, t1, kind) {
                clipKeys(rc, [R[0] + 3, R[1] + 3, R[0] + R[2] - 3, R[1] + R[3] - 3], [t0, t1], kind);
                rc.property("ADBE Mask Parade").property(2).maskMode = MaskMode.INTERSECT;
            }
            if (a.phase !== "in") {                          // old rows leave
                if (a.phase === "out") { if (l) cutOut(l, a.t); }
                else { var oldFull = copyLayer(a.old_ai, "Panel/Card", pre, "Panel/Card (old)"); if (oldFull) cutOut(oldFull, a.t); }
                for (var oi = 0; oi < nOld; oi++) {
                    var ro = rowCopy(a.old_ai, OR, a.old.rows[oi], "old row " + (oi + 1)); if (!ro) continue;
                    var to0 = a.t + oi * CS, rpo = POS(ro).value;
                    cutIn(ro, a.t);
                    cm(POS(ro), [[to0, rpo], [to0 + outD, [rpo[0], rpo[1] - RISE]]], "accel");
                    clipRow(ro, OR, to0, to0 + outD, "accel");
                    cutOut(ro, to0 + outD);
                }
            }
            if (a.phase === "out") return null;
            for (var ni = 0; ni < nNew; ni++) {              // new rows arrive from below
                var rn = rowCopy(a.new_ai, NR, a.new.rows[ni], "new row " + (ni + 1)); if (!rn) continue;
                var tn0 = a.t_new + ni * CS, rpn = POS(rn).value;
                POS(rn).setValue([rpn[0], rpn[1] + RISE]);
                cm(POS(rn), [[tn0, [rpn[0], rpn[1] + RISE]], [tn0 + MO.card_in_d, rpn]], "snap");
                clipRow(rn, NR, tn0, tn0 + MO.card_in_d, "snap");
                cutIn(rn, tn0); cutOut(rn, tDone);
            }
            var nf = copyLayer(a.new_ai, "Panel/Card", pre); if (nf) cutIn(nf, tDone);
            return nf;
        case "rollout":                                      // a layer that lives in the side card rolls out with the card's rows
            var rl = [];                                     // the layer itself, or each of its rows (chips that dropped in one per cue)
            for (var ri2 = 1; ri2 <= pre.numLayers; ri2++) {
                var Lr = pre.layer(ri2);
                if (Lr.name === a.layer || Lr.name.indexOf(a.layer + " row ") === 0) rl.push(Lr);
            }
            function rowNo(L) { var m = L.name.match(/ row (\d+)$/); return m ? parseInt(m[1], 10) : 0; }
            rl.sort(function (x, y) { return rowNo(x) - rowNo(y); });   // rows are numbered top to bottom
            for (ri2 = 0; ri2 < rl.length; ri2++) rollLayer(rl[ri2], t + ri2 * MO.card_stagger, a.clip);
            return l;
        case "gather":                                       // several layers shrink together into one point (a null parent, identity until it scales)
            var gn = pre.layers.addNull(pre.duration); gn.name = "Gather " + a.c.join(",");
            ANC(gn).setValue(a.c); POS(gn).setValue(a.c);
            for (var gk = 1; gk <= pre.numLayers; gk++) {
                var GL = pre.layer(gk);
                if (GL === gn) continue;
                for (var gp = 0; gp < a.prefixes.length; gp++) if (GL.name.indexOf(a.prefixes[gp]) === 0 && GL.outPoint > t) { GL.parent = gn; break; }
            }
            cm(SC(gn), [[t, [100, 100]], [t + a.d, [0, 0]]], "accel");
            return null;
        case "axisdraw":                                     // the axes draw on as in 2A/2B: x axis left to right, then the y axis bottom to top
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            var ar = rect(l), ap = POS(l).value, AP = 6, ax0 = ar[0] - AP, ay0 = ar[1] - AP, ax1 = ar[2] + AP, ay1 = ar[3] + AP, yb = a.y_split;
            function abox(x0, y0, x1, y1) { var P1 = toLayer(l, x0, y0, ap), P2 = toLayer(l, x1, y1, ap); return boxShape(P1[0], P1[1], P2[0], P2[1]); }
            cm(addMask(l, "Axes draw"), [[t, abox(ax0, yb, ax0 + 0.5, ay1)], [t + a.dx, abox(ax0, yb, ax1, ay1)], [t + a.dx + a.dy, abox(ax0, ay0, ax1, ay1)]], "snap");
            return l;
        case "centrewipe":                                   // appears at a point, then opens sideways from it (arrows drawing outward)
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            var cr = rect(l), cpp = POS(l).value, CP = 6;
            function cbox(x0, x1) { var Q1 = toLayer(l, x0, cr[1] - CP, cpp), Q2 = toLayer(l, x1, cr[3] + CP, cpp); return boxShape(Q1[0], Q1[1], Q2[0], Q2[1]); }
            cutIn(l, t);
            cm(addMask(l, "Open"), [[t, cbox(a.c[0] - a.half, a.c[0] + a.half)], [t + (a.d || MO.snap_d), cbox(cr[0] - CP, cr[2] + CP)]], "snap");
            return l;
        case "skip":                                         // left out of this beat (it arrives later on its own cue)
            return null;
        case "grey":                                         // a curve turns a muted grey (or back) on its cue: Tint to grey, ~0.3 s
            if (!l) return l;
            var fx = l.property("ADBE Effect Parade").property("Grey");
            if (!fx) {
                fx = l.property("ADBE Effect Parade").addProperty("ADBE Tint"); fx.name = "Grey";
                fx.property("ADBE Tint-0001").setValue(hex(a.col || "#B9B5AE").concat([1]));   // map black to grey
                fx.property("ADBE Tint-0002").setValue(hex(a.col || "#B9B5AE").concat([1]));   // map white to grey
            }
            cm(fx.property("ADBE Tint-0003"), [[t, a.from], [t + (a.d || 0.3), a.to]], "snap");   // amount to tint, %
            return l;
        case "clamp":                                        // the molecule tightens its grip: it draws in, and rings snap in around its bound O2s
            if (!l) return l;
            var pv = POS(l).value, k0 = SC(l).valueAtTime(t, false);
            cm(SC(l), [[t, k0], [t + MO.snap_d * 0.6, [k0[0] * a.s, k0[1] * a.s]]], "snap");
            for (var qi = 0; qi < a.pts.length; qi++) {
                var qp = [pv[0] + a.s * (a.pts[qi][0] - pv[0]), pv[1] + a.s * (a.pts[qi][1] - pv[1])];
                var cr2 = shapeLayer(pre, "Grip " + (qi + 1), "ellipse", [a.r * 2, a.r * 2], qp, [1, 1, 1], hex(a.col || "#F0645A"), 4);
                cr2.fill().property("ADBE Vector Fill Opacity").setValue(0);
                var tq = t + qi * MO.card_stagger * 2;
                cutIn(cr2.layer, tq);
                cm(SC(cr2.layer), [[tq, [220, 220]], [tq + MO.snap_d * 0.6, [100, 100]]], "snap");
                if (a.locks && a.locks[qi]) {                // a small lock snaps on at the ring's edge once the ring has landed
                    var lk = copyLayer(bt.ai, a.locks[qi], pre); if (!lk) continue;
                    var lc = centre(rect(lk)); setPivot(lk, lc);
                    POS(lk).setValue([qp[0] + a.badge[qi][0], qp[1] + a.badge[qi][1]]);
                    var tl = tq + MO.snap_d * 0.6 + qi * 2 / PLAN.fps;
                    cutIn(lk, tl);
                    cm(SC(lk), [[tl, [0, 0]], [tl + 0.3, [100, 100]]], "snap");
                }
            }
            return l;
        case "growdraw":                                     // grows from its centre while its outline traces on (end-screen slots)
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            d = a.d || MO.snap_d;
            pre.openInViewer();
            var gsl = pre.selectedLayers; for (var gs = 0; gs < gsl.length; gs++) gsl[gs].selected = false;
            l.selected = true;
            app.executeCommand(app.findMenuCommandId("Create Shapes from Vector Layer"));
            var gsh = pre.selectedLayers.length ? pre.selectedLayers[0] : null;
            if (!gsh || !(gsh instanceof ShapeLayer)) { err(bt.id + " " + a.layer + ": no shape layer made"); gsh = l; }
            else { gsh.selected = false; l.remove(); gsh.name = a.layer; }
            var gc = centre(rect(gsh)); setPivot(gsh, gc); cutIn(gsh, t);
            cm(SC(gsh), [[t, [0, 0]], [t + d, [100, 100]]], "snap");
            if (gsh instanceof ShapeLayer) {
                var gtr = gsh.property("ADBE Root Vectors Group").addProperty("ADBE Vector Filter - Trim");
                cm(gtr.property("ADBE Vector Trim End"), [[t, 0], [t + d, 100]], "snap");
            }
            return gsh;
        case "textlines":                                    // one text layer's lines cut on one after another (each line a masked copy)
            var firstLine = null;
            for (var tli = 0; tli < a.lines.length; tli++) {
                var tl2 = copyLayer(bt.ai, a.layer, pre, a.layer + " line " + (tli + 1)); if (!tl2) continue;
                var tr2 = rect(tl2), tp2 = POS(tl2).value, U3 = toLayer(tl2, tr2[0] - 10, a.lines[tli][0], tp2), V3 = toLayer(tl2, tr2[2] + 10, a.lines[tli][1], tp2);
                addMask(tl2, "Line").setValue(boxShape(U3[0], U3[1], V3[0], V3[1]));
                cutIn(tl2, a.lines[tli][2]);
                if (!firstLine) firstLine = tl2;
            }
            return firstLine;
        case "undraw":                                       // a held layer draws itself out (mask retract, accelerating) and is gone
            if (!l) return l;
            var ur = rect(l), up = POS(l).value, UP = 6, ux0 = ur[0] - UP, uy0 = ur[1] - UP, ux1 = ur[2] + UP, uy1 = ur[3] + UP;
            var ushut = { rtl: [ux0, uy0, ux0, uy1], ltr: [ux1, uy0, ux1, uy1], ttb: [ux0, uy1, ux1, uy1], btt: [ux0, uy0, ux1, uy0] }[a.dir];
            var UA0 = toLayer(l, ux0, uy0, up), UB0 = toLayer(l, ux1, uy1, up), UA1 = toLayer(l, ushut[0], ushut[1], up), UB1 = toLayer(l, ushut[2], ushut[3], up);
            cm(addMask(l, "Draw out"), [[t, boxShape(UA0[0], UA0[1], UB0[0], UB0[1])], [t + (a.d || MO.snap_d), boxShape(UA1[0], UA1[1], UB1[0], UB1[1])]], "accel");
            cutOut(l, t + (a.d || MO.snap_d));
            return l;
        case "swell":                                        // grows about a point, holds, then settles back (the T -> R schematic)
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            cutIn(l, t); setPivot(l, a.c);
            cm(SC(l), [[t, [100, 100]], [t + a.d, [100 * a.s, 100 * a.s]]], "snap");
            cm(SC(l), [[a.t_back, [100 * a.s, 100 * a.s]], [a.t_back + a.back_d, [100, 100]]], "snap");
            return l;
        case "pairturn":                                     // a subunit turns about the tetramer centre and draws in (T -> R schematic)
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            cutIn(l, t);
            setPivot(l, a.c);
            cm(TR(l).property("ADBE Rotate Z"), [[t, 0], [t + a.d, a.deg]], "snap");
            cm(POS(l), [[t, a.c], [t + a.d, [a.c[0] + a.move[0], a.c[1] + a.move[1]]]], "snap");
            return l;
        case "turn":                                         // a held layer turns and resizes about a point (the T -> R schematic)
            if (!l) return l;
            setPivot(l, a.c);
            var RZ = TR(l).property("ADBE Rotate Z");
            cm(RZ, [[t, 0], [t + a.d, a.deg]], "snap");
            cm(SC(l), [[t, [100, 100]], [t + a.d, [100 * a.s, 100 * a.s]]], "snap");
            return l;
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
            cutIn(sh, t);
            if (a.t_off !== undefined) {                     // draws itself off again
                cm(tr.property("ADBE Vector Trim Start"), [[a.t_off, 0], [a.t_off + d, 100]], "accel");
                cutOut(sh, a.t_off + d);
            }
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
        if (full && !S.no_audio) {                           // audio is shifted with any gap before this scene; a gap stays silent
            var al = sc.layers.add(full); al.name = "VO full.mp3"; al.startTime = -(S.start - (S.audio_shift || 0)); al.inPoint = 0;
            al.outPoint = Math.min(sc.duration, (S.audio_end || S.end) - S.start);
        }
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
