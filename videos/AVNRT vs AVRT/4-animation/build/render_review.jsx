// render_review.jsx — AVNRT vs AVRT: the review render for a Stage 4 pass.
// Run in After Effects after build_ae.jsx, with the version's .aep open (or set VERSION below and it opens it).
// Adds a comp "AVNRT vs AVRT · review" (the master with the master timecode and the beat ID burned in, bottom left) and renders it,
// half resolution, H.264, to 5-finish/renders/AVNRT vs AVRT review v<N>.mp4 (gitignored). The master comp is left untouched.
#target aftereffects
(function () {
    var VERSION = 2;
    var buildDir = File($.fileName).parent.fsName, animDir = Folder(buildDir).parent.fsName, videoDir = Folder(animDir).parent.fsName;
    var pf = File(buildDir + "/ae_plan.json"); pf.encoding = "UTF-8"; pf.open("r");
    var PLAN = eval("(" + pf.read() + ")"); pf.close();
    var aep = File(animDir + "/" + PLAN.title + "_v" + VERSION + ".aep");
    if (!(app.project && app.project.file && app.project.file.fsName === aep.fsName)) {
        if (!aep.exists) return "no " + aep.fsName;
        app.open(aep);
    }
    var proj = app.project, master = null, i;
    for (i = 1; i <= proj.numItems; i++) if (proj.item(i) instanceof CompItem && proj.item(i).name === PLAN.title) master = proj.item(i);
    if (!master) return "no master comp";
    var name = PLAN.title + " · review";
    for (i = proj.numItems; i >= 1; i--) if (proj.item(i) instanceof CompItem && proj.item(i).name === name) proj.item(i).remove();
    var rc = proj.items.addComp(name, PLAN.w, PLAN.h, 1, master.duration, PLAN.fps);
    rc.layers.add(master);
    var starts = [], ids = [];
    for (var s = 0; s < PLAN.scenes.length; s++) for (var b = 0; b < PLAN.scenes[s].beats.length; b++) { starts.push(PLAN.scenes[s].beats[b].start); ids.push('"' + PLAN.scenes[s].beats[b].id + '"'); }
    var bg = rc.layers.addSolid([0.13, 0.13, 0.13], "Burn-in plate", 360, 52, 1);
    bg.property("ADBE Transform Group").property("ADBE Position").setValue([24 + 180, PLAN.h - 24 - 26]);
    bg.property("ADBE Transform Group").property("ADBE Opacity").setValue(70);
    var tl = rc.layers.addText("0:00:00:00 · 1A");
    var td = tl.property("ADBE Text Properties").property("ADBE Text Document"), doc = td.value;
    doc.fontSize = 28; doc.fillColor = [1, 1, 1]; doc.applyFill = true; doc.applyStroke = false;
    try { doc.font = "Inter-SemiBold"; } catch (x) {}
    doc.justification = ParagraphJustification.LEFT_JUSTIFY; td.setValue(doc);
    tl.property("ADBE Transform Group").property("ADBE Position").setValue([40, PLAN.h - 40]);
    td.expression = "var S=[" + starts.join(",") + "], I=[" + ids.join(",") + "], k=0;\n" +
        "for (var i=0;i<S.length;i++) if (time >= S[i] - 0.0005) k=i;\n" +
        "timeToTimecode(time, 30, false) + '  ·  ' + I[k];";
    var out = Folder(videoDir + "/5-finish/renders");
    if (!out.exists) out.create();
    var f = File(out.fsName + "/" + PLAN.title + " review v" + VERSION + ".mp4");
    var rq = proj.renderQueue;
    while (rq.numItems > 0) rq.item(1).remove();
    var it = rq.items.add(rc);
    try { it.setSetting("Resolution", "Half"); } catch (x) {}
    var om = it.outputModule(1), tpl = null, names = om.templates;
    for (i = 0; i < names.length; i++) if (/^H\.264/.test(names[i]) && !tpl) tpl = names[i];
    if (tpl) om.applyTemplate(tpl);
    om.file = f;
    proj.save();
    rq.render();
    master.openInViewer();
    proj.save();
    return "rendered " + f.fsName + (tpl ? " (" + tpl + ")" : " (default output module: not H.264!)");
})();
