// run_build_ae.jsx — runs build_ae.jsx unattended: no After Effects dialogs. The result (or the error with its line and file)
// goes to build/ae_build_result.txt. Copied 2026-11-18 from Oxygen Hemoglobin Curve.
// Run: caffeinate -i osascript -e 'tell application "Adobe After Effects 2026" to DoScriptFile "<this file>"'
#target aftereffects
(function () {
    var dir = File($.fileName).parent.fsName, r;
    app.beginSuppressDialogs();
    try { r = $.evalFile(File(dir + "/build_ae.jsx")); }
    catch (e) { r = "ERR " + e + " | line " + e.line + " | " + (e.fileName || ""); }
    finally { app.endSuppressDialogs(false); }
    var f = File(dir + "/ae_build_result.txt"); f.encoding = "UTF-8"; f.open("w"); f.write(String(r)); f.close();
})();
