#target aftereffects
// Renders the four Pulsus Paradoxus Instagram Story comps to <working folder>/Stories/<comp name>.mp4 (H.264), via the AE render queue.
(function () {
    var proj = app.project;
    if (!proj || !proj.file) { alert("Open Pulsus Paradoxus.aep first."); return; }
    var root = File($.fileName).parent.parent.fsName, out = Folder(root + "/Stories"); if (!out.exists) out.create();
    var names = ["Story 1 - Hook", "Story 2 - Definition", "Story 3 - Tamponade", "Story 4 - Watch"], rq = proj.renderQueue, log = [];
    for (var q = rq.numItems; q >= 1; q--) { var it0 = rq.item(q); if (it0.status !== RQItemStatus.DONE && it0.comp && /^Story \d/.test(it0.comp.name)) it0.remove(); }
    for (var n = 0; n < names.length; n++) {
        var comp = null;
        for (var i = 1; i <= proj.numItems; i++) if (proj.item(i) instanceof CompItem && proj.item(i).name === names[n]) comp = proj.item(i);
        if (!comp) { log.push("missing " + names[n]); continue; }
        var it = rq.items.add(comp), om = it.outputModule(1), tpl = null, t = om.templates;
        for (var k = 0; k < t.length; k++) if (/^H\.264/.test(t[k]) && /Match Render Settings/.test(t[k]) && /15/.test(t[k])) tpl = t[k];
        if (!tpl) for (k = 0; k < t.length; k++) if (/^H\.264/.test(t[k])) tpl = t[k];
        if (tpl) om.applyTemplate(tpl); else log.push("no H.264 template; using default output module");
        om.file = File(out.fsName + "/" + names[n] + (tpl ? ".mp4" : ".mov"));
        log.push(names[n] + " -> " + om.file.fsName + " [" + (tpl || "default") + "]");
    }
    rq.render();
    var rep = File(root + "/build/stories_render_report.txt"); rep.open("w"); rep.write(log.join("\n")); rep.close();
})();
