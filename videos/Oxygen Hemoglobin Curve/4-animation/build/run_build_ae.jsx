// run_build_ae.jsx — runs build_ae.jsx unattended: no After Effects dialogs. The result (or the error with its line and file)
// goes to build/ae_build_result.txt; the steps after the master is saved go to build/ae_build_log.txt.
// Run: osascript -e 'tell application "Adobe After Effects 2026" to DoScriptFile "<this file>"'  (under caffeinate -i)
#target aftereffects
(function () {
    var dir = File($.fileName).parent.fsName, r;
    app.beginSuppressDialogs();
    try { r = $.evalFile(File(dir + "/build_ae.jsx")); }
    catch (e) { r = "ERR " + e + " | line " + e.line + " | " + (e.fileName || ""); }
    finally { app.endSuppressDialogs(false); }
    var f = File(dir + "/ae_build_result.txt"); f.encoding = "UTF-8"; f.open("w"); f.write(String(r)); f.close();
})();
