// check_frames.jsx — Oxygen Hemoglobin Curve: PNGs of the master comp in the open project, 0.9 s after every sync point
// (where each move has landed), to build/ae_check/landed/. Reads ae_check_times.json from build_ae.jsx. Changes nothing.
#target aftereffects
(function () {
    var buildDir = File($.fileName).parent.fsName;
    var tf = File(buildDir + "/ae_check_times.json"); tf.encoding = "UTF-8"; tf.open("r");
    var times = eval("(" + tf.read() + ")"); tf.close();
    var master = null;
    for (var i = 1; i <= app.project.numItems; i++) if (app.project.item(i) instanceof CompItem && app.project.item(i).name === "Oxygen Hemoglobin Curve") master = app.project.item(i);
    if (!master) return "no master comp";
    var dir = Folder(buildDir + "/ae_check/landed"); if (!dir.exists) dir.create();
    master.resolutionFactor = [2, 2];
    var n = 0;
    for (i = 0; i < times.length; i++) {
        if (times[i][1].indexOf("_start") > 0) continue;
        var t = Math.min(master.duration - 0.04, times[i][0] + 0.9);
        master.saveFrameToPng(t, File(dir.fsName + "/" + ("000" + t.toFixed(2)).slice(-6) + "_" + times[i][1].replace(/[^A-Za-z0-9]+/g, "") + ".png")); n++;
    }
    master.resolutionFactor = [1, 1];
    return "saved " + n;
})();
