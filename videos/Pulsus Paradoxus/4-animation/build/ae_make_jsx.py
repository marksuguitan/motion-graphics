"""Write build_ae.jsx (full build) and build_scene1..5.jsx (update one scene) from engine.jsx + plan.json + checks.json."""
import json, sys
D = "/tmp/claude-0/ae"
eng = open(f"{D}/engine.jsx").read()
plan = json.load(open(f"{D}/plan.json")); checks = json.load(open(f"{D}/checks.json"))
cueb = json.load(open(sys.argv[1]))["cueB"]["starts_at_video_s"]
def out(name, only):
    s = (eng.replace("__PLAN__", json.dumps(plan)).replace("__CHECKS__", json.dumps(checks))
            .replace("__CUEB__", repr(cueb)).replace("__ONLY__", json.dumps(only)))
    assert "__" not in "".join(x for x in ("__PLAN__", "__CHECKS__", "__CUEB__", "__ONLY__") if x in s)
    open(f"{D}/{name}", "w").write(s)
out("build_ae.jsx", None)
for i in range(1, 6): out(f"build_scene{i}.jsx", [f"Scene {i}"])
print("ok")
