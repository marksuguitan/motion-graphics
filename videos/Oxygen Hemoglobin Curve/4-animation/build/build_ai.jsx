// build_ai.jsx — Oxygen Hemoglobin Curve: layered SVG -> layered .ai, one per beat.
// Adapted from library/scripts/adobe/build_ai.jsx (Pulsus Paradoxus). Run prep_ai.py first.
// Run in Illustrator (File > Scripts > Other Script...). Reads build/ai_src/*.svg and build/ai_src/layers.json,
// writes 4-animation/ai/<beat>.ai, a PNG check of each to build/ai_check/, and build/ai_build_report.json.
// Only beats whose source SVG is newer than their .ai are rebuilt (delete an .ai to force it).
// Each top-level group L001... becomes one Illustrator layer named as in the SVG (Group/Sublayer).
#target illustrator
(function () {
    var buildDir = File($.fileName).parent;            // .../4-animation/build
    var srcDir = Folder(buildDir + "/ai_src");
    var outDir = Folder(buildDir.parent + "/ai");
    var chkDir = Folder(buildDir + "/ai_check");
    if (!outDir.exists) outDir.create();
    if (!chkDir.exists) chkDir.create();
    var jf = File(srcDir + "/layers.json"); jf.encoding = "UTF-8"; jf.open("r");
    var MAP = eval("(" + jf.read() + ")"); jf.close();
    var FACES = { "Inter-Regular": 1, "Inter-Medium": 1, "Inter-SemiBold": 1, "Inter-Bold": 1, "Manrope-SemiBold": 1, "Manrope-Bold": 1 };
    app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;
    var report = [];
    for (var beat in MAP) {
        var entry = { beat: beat, ok: false, layers: [], missing: [], fonts: [], badfonts: [], error: "" };
        try {
            var f = File(srcDir + "/" + beat + ".svg");
            if (!f.exists) { entry.error = "no source svg"; report.push(entry); continue; }
            var aiFile = File(outDir + "/" + beat + ".ai");
            if (aiFile.exists && aiFile.modified > f.modified) {   // unchanged since the last build: keep it
                entry.ok = true; entry.error = "skipped (up to date)"; report.push(entry); continue;
            }
            var doc = app.open(f);
            var first = doc.layers[0];
            var spec = MAP[beat].layers;
            for (var i = 0; i < spec.length; i++) {
                var item = null;
                try { item = doc.groupItems.getByName(spec[i].id); } catch (e) { item = null; }
                if (!item) { entry.missing.push(spec[i].id + " " + spec[i].name); continue; }
                var lyr = doc.layers.add();                 // new layer goes on top: walking L001 up keeps z-order
                lyr.name = spec[i].name;
                item.move(lyr, ElementPlacement.PLACEATBEGINNING);
                item.name = spec[i].name.split("/").pop();
            }
            var leftover = first.pageItems.length > 0;
            if (!leftover) { first.remove(); }
            else { first.name = "Unassigned (check)"; entry.error = "unassigned items left on the import layer"; }
            for (var k = 0; k < doc.layers.length; k++) entry.layers.push(doc.layers[k].name);
            // every face used, so a substituted font can't slip through
            var seen = {};
            for (var t = 0; t < doc.textFrames.length; t++) {
                var runs = doc.textFrames[t].textRanges;
                for (var r = 0; r < runs.length; r++) {
                    var nm = runs[r].characterAttributes.textFont.name;
                    if (!seen[nm]) { seen[nm] = 1; entry.fonts.push(nm); if (!FACES[nm]) entry.badfonts.push(nm); }
                }
            }
            var png = new ExportOptionsPNG24(); png.horizontalScale = 50; png.verticalScale = 50; png.artBoardClipping = true; png.antiAliasing = true;
            doc.exportFile(File(chkDir + "/" + beat + ".png"), ExportType.PNG24, png);
            var opts = new IllustratorSaveOptions(); opts.pdfCompatible = true; opts.embedICCProfile = false; opts.compressed = true;
            doc.saveAs(aiFile, opts);
            doc.close(SaveOptions.DONOTSAVECHANGES);
            entry.ok = entry.missing.length === 0 && entry.badfonts.length === 0 && !leftover;
        } catch (err) { entry.error = String(err) + " line " + err.line; }
        report.push(entry);
    }
    function q(s) { return '"' + String(s).replace(/\\/g, "\\\\").replace(/"/g, "'") + '"'; }
    function arr(a) { var o = []; for (var i = 0; i < a.length; i++) o.push(q(a[i])); return "[" + o.join(",") + "]"; }
    var s = "[\n", nok = 0;
    for (var r2 = 0; r2 < report.length; r2++) {
        var e = report[r2]; if (e.ok) nok++;
        s += '{"beat":' + q(e.beat) + ',"ok":' + e.ok + ',"error":' + q(e.error) + ',"missing":' + arr(e.missing) + ',"badfonts":' + arr(e.badfonts) +
             ',"fonts":' + arr(e.fonts) + ',"layers":' + arr(e.layers) + "}" + (r2 < report.length - 1 ? ",\n" : "\n");
    }
    var out = File(buildDir + "/ai_build_report.json");
    out.encoding = "UTF-8"; out.open("w"); out.write(s + "]\n"); out.close();
    app.userInteractionLevel = UserInteractionLevel.DISPLAYALERTS;
    return "built " + report.length + " beats, ok " + nok;
})();
