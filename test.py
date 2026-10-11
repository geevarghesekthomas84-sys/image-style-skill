"""Sanity tests for the image-style data and build outputs. Run: python test.py"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent
fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


def load(f):
    return [l.split("|") for l in (ROOT / "src" / f).read_text(encoding="utf-8").splitlines() if l.strip()]


styles, aspects, negs, models, presets = (load(f) for f in
    ("modifiers.txt", "aspect.txt", "negatives.txt", "models.txt", "presets.txt"))

# shape
for r in styles:
    check(len(r) == 3 and all(x.strip() for x in r), f"bad style row: {r[:1]}")
    check(re.fullmatch(r"[a-z0-9.]+", r[0]), f"style name must be lowercase a-z0-9.: {r[0]}")
    check(len(r[2]) <= 140, f"phrase too long: {r[0]}")

# no name clashes across every command namespace
names = [r[0] for r in styles] + [r[0].replace(":", "x") for r in aspects] \
    + [r[0] for r in negs] + [r[0] for r in models] + [r[0] for r in presets]
dupes = {n for n in names if names.count(n) > 1}
check(not dupes, f"duplicate command names: {dupes}")

# presets must only use real commands
known = {r[0] for r in styles} | {r[0] for r in negs}
for n, label, toks, ar in presets:
    for t in toks.split():
        check(t in known, f"preset {n}: unknown token {t}")
    check(any(ar == a[0] or ar == a[1] for a in aspects), f"preset {n}: unknown ratio {ar}")
    check(len(toks.split()) <= 8, f"preset {n}: more than 8 modifiers")

# policy: no living-artist / real-person style commands
blocked = ("by greg", "in the style of", "rutkowski", "ghibli", "disney", "pixar", "marvel")
for r in styles:
    check(not any(b in r[2].lower() for b in blocked), f"artist/IP reference in {r[0]}")

# build outputs
d = ROOT / "dist"
skill = (d / "image-style" / "SKILL.md").read_text(encoding="utf-8")
check(skill.startswith("---\nname: image-style\n"), "SKILL.md frontmatter")
for r in styles:
    check(f"`/{r[0]}`" in skill, f"missing from SKILL.md: {r[0]}")
check((d / "platforms" / "claude-ai" / "image-style.zip").exists(), "zip missing")
check(len(list((d / "marketplace" / "image-style" / "commands").glob("*.md")))
      == len(names), "plugin command count != command count")
check(len((d / "platforms" / "chatgpt" / "custom-instructions-short.txt").read_text(encoding="utf-8")) <= 1500,
      "ChatGPT short instructions over 1500 chars")

# expander JS parses
html = (d / "platforms" / "flow-kling-anywhere" / "expander.html").read_text(encoding="utf-8")
js = html.split("<script>")[1].split("</script>")[0]
tmp = ROOT / "_t.js"
tmp.write_text(js, encoding="utf-8")
try:
    r = subprocess.run(["node", "--check", str(tmp)], capture_output=True, text=True)
    check(r.returncode == 0, "expander JS syntax: " + r.stderr[:200])
except FileNotFoundError:
    print("node not found: skipped JS syntax check")
finally:
    tmp.unlink(missing_ok=True)

import py_compile
try:
    py_compile.compile(str(ROOT / "imagegen.py"), doraise=True, cfile=str(ROOT / "_ig.pyc"))
except py_compile.PyCompileError as e:
    fails.append("imagegen.py: " + str(e)[:200])
(ROOT / "_ig.pyc").unlink(missing_ok=True)

import xml.dom.minidom as _md
_demo = (ROOT / "docs" / "demo.svg").read_text(encoding="utf-8")
try:
    _md.parseString(_demo)
except Exception as e:
    fails.append("docs/demo.svg is not valid XML: " + str(e)[:120])
for bad in ("<script", "onload", "xlink:href", "http://", "https://", "<image", "<foreignObject"):
    if bad in _demo and not (bad == "http://" and "http://www.w3.org/2000/svg" in _demo and _demo.count("http://") == 1):
        fails.append("docs/demo.svg contains disallowed content: " + bad)

_ct = subprocess.run([sys.executable, str(ROOT / "comfyui" / "ComfyUI-ImageStyle" / "tests" / "test_core.py")],
                     capture_output=True, text=True)
if _ct.returncode != 0:
    fails.append("ComfyUI node tests failed: " + (_ct.stderr or _ct.stdout)[-600:])

print(f"{len(names)} commands checked, {len(fails)} problems")
for f in fails:
    print(" -", f)
sys.exit(1 if fails else 0)
