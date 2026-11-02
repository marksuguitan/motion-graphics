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
(function () {
    var buildDir = File($.fileName).parent.fsName;
    var animDir = Folder(buildDir).parent.fsName;                       // .../4-animation
    var videoDir = Folder(animDir).parent.fsName;
    var pf = File(buildDir + "/ae_plan.json"); pf.encoding = "UTF-8"; pf.open("r");
    var PLAN = eval("(" + pf.read() + ")"); pf.close();
    var VERSION = 1;
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
    function keys(prop, list, kind) {                         // list: [[t, v], ...]
        for (var i = 0; i < list.length; i++) prop.setValueAtTime(list[i][0], list[i][1]);
        var e = EASE[kind || "inout"];
        for (var k = 1; k <= prop.numKeys; k++) {
            var n = (prop.propertyValueType === PropertyValueType.TwoD_SPATIAL || prop.propertyValueType === PropertyValueType.ThreeD_SPATIAL ||
                     prop.propertyValueType === PropertyValueType.SHAPE) ? 1 : (prop.value instanceof Array ? prop.value.length : 1);
            var a = [], b = [];
            for (var j = 0; j < n; j++) { a.push(new KeyframeEase(0, k === 1 ? 33 : e[1])); b.push(new KeyframeEase(0, k === prop.numKeys ? 33 : e[0])); }
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
    function fadeOut(o, t, d) { if (!o) return; keys(OP(o), [[t, 100], [t + d, 0]], "in"); o.outPoint = Math.min(o.containingComp.duration, t + d + 0.04); }
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
        keys(mp, list, "inout");
        return list[list.length - 1][0];
    }
    function clipKeys(l, clip, times) {                      // a mask fixed in comp space while the layer moves
        var mp = addMask(l, "Graph clip"), list = [];
        for (var i = 0; i < times.length; i++) {
            var p = POS(l).valueAtTime(times[i], false);
            var A = toLayer(l, clip[0], clip[1], p), B = toLayer(l, clip[2], clip[3], p);
            list.push([times[i], boxShape(A[0], A[1], B[0], B[1])]);
        }
        keys(mp, list, "inout");
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
                try { l = doAct(pre, bt, acts[j], l); } catch (x) { err(bt.id + " " + name + " (" + acts[j]["do"] + "): " + x + " line " + x.line); }
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
            d = a.d || 0.5;
            keys(OP(l), [[t, 0], [t + d, 100]], "out");
            var rise = a.rise === undefined ? 20 : a.rise;
            if (rise) { p = POS(l).value; keys(POS(l), [[t, [p[0], p[1] + rise]], [t + d, p]], "out"); }
            return l;
        case "pop":
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            d = a.d || 0.6;
            setPivot(l, centre(rect(l)));
            var f = (a.from === undefined ? 0 : a.from) * 100, over = a.from ? 102 : 108;
            keys(SC(l), [[t, [f, f]], [t + 0.7 * d, [over, over]], [t + d, [100, 100]]], "inout");
            keys(OP(l), [[t, 0], [t + 0.3 * d, 100]], "out");
            return l;
        case "wipe":
            d = 0;
            if (a.keep) o = copyLayer(bt.prev_ai, a.layer, pre, a.layer + " (prev)");
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            var tEnd = wipe(l, a);
            if (o) o.outPoint = Math.min(pre.duration, tEnd + 0.04);
            return l;
        case "xfade":
            d = a.d || 0.5;
            o = copyLayer(bt.prev_ai, a.layer, pre, a.layer + " (prev)");
            if (o) { keys(OP(o), [[t, 100], [t + d, 0]], "inout"); o.outPoint = Math.min(pre.duration, t + d + 0.04); }
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            keys(OP(l), [[t, 0], [t + d, 100]], "inout");
            return l;
        case "out":                                          // same name: the previous version leaves, a new one follows
            fadeOut(copyLayer(bt.prev_ai, a.layer, pre, a.layer + " (out)"), t, a.d || 0.4);
            return l;
        case "carry":
            d = a.d || 0.8;
            o = copyLayer(bt.prev_ai, a.prev || a.layer, pre, (a.prev || a.layer) + " (carried)");
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            if (!o) return l;
            var R0 = rect(o), R1 = rect(l), c0 = centre(R0), c1 = centre(R1);
            var sx = (R1[2] - R1[0]) / (R0[2] - R0[0]), sy = (R1[3] - R1[1]) / (R0[3] - R0[1]);
            if (a.fit === "w") sy = sx;
            else if (a.uniform !== false) { sx = sy = Math.min(sx, sy); }
            if (a.top) TOPS.push(o, l);                          // raised once the whole beat is stacked
            setPivot(o, c0); setPivot(l, c1);
            keys(POS(o), [[t, c0], [t + d, c1]], "inout"); keys(SC(o), [[t, [100, 100]], [t + d, [sx * 100, sy * 100]]], "inout");
            keys(OP(o), [[t, 100], [t + d, 0]], "inout"); o.outPoint = Math.min(pre.duration, t + d + 0.04);
            keys(POS(l), [[t, c0], [t + d, c1]], "inout"); keys(SC(l), [[t, [100 / sx, 100 / sy]], [t + d, [100, 100]]], "inout");
            keys(OP(l), [[t, 0], [t + d, 100]], "inout");
            return l;
        case "slidein":
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            d = a.d || 1.0; p = POS(l).value;
            keys(POS(l), [[t, [p[0] + a.dx, p[1] + a.dy]], [t + d, p]], "inout");
            keys(OP(l), [[t, 0], [t + Math.min(0.4, d), 100]], "out");
            if (a.clip) clipKeys(l, a.clip, [t, t + d]);
            return l;
        case "nudge":
            l = copyLayer(bt.ai, a.layer, pre); if (!l) return null;
            p = POS(l).value;
            var nk = [], nt = [];
            for (var k = 0; k < a.keys.length; k++) { nk.push([a.keys[k][0], [p[0] + a.keys[k][1], p[1]]]); nt.push(a.keys[k][0]); }
            keys(POS(l), nk, "inout");
            if (a.clip) clipKeys(l, a.clip, nt);
            return l;
        case "bump":
            if (!l) return l;
            r = rect(l);
            var sp = SC(l), base = sp.numKeys ? sp.valueAtTime(t, false) : [100, 100];
            if (!sp.numKeys) setPivot(l, centre(r));
            keys(sp, [[t, base], [t + 0.15, [base[0] * 1.03, base[1] * 1.03]], [t + 0.4, base]], "inout");
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
    out.write('{"aep":' + q(aep.fsName) + ',"errors":' + arr(report.errors) + ',"missing":' + arr(report.missing) + ',"beats":' + arr(report.beats) + "}\n");
    out.close();
    return "built " + report.beats.length + " beats in " + PLAN.scenes.length + " scenes; errors " + report.errors.length + ", missing " + report.missing.length;
})();
