"""Build outputs from src/modifiers.txt:
  dist/image-style/SKILL.md      -> Claude skill (copy folder to ~/.claude/skills/)
  dist/image-style/modifiers.json
  dist/portable-prompt.md        -> paste into any other AI (ChatGPT, Gemini, ...) as instructions
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
rows = []
for line in (ROOT / "src" / "modifiers.txt").read_text(encoding="utf-8").splitlines():
    if line.strip():
        name, cat, phrase = line.split("|", 2)
        rows.append((name, cat, phrase))

names = [r[0] for r in rows]
assert len(names) == len(set(names)), "duplicate modifier"

cats = {}
for n, c, p in rows:
    cats.setdefault(c, []).append((n, p))

table = []
for c, items in cats.items():
    table.append(f"\n### {c}\n")
    table += [f"- `/{n}` → {p}" for n, p in items]
table = "\n".join(table)

RULES = """\
## How it works

The user writes an image request and adds one or more slash modifiers, e.g.
`a lone lighthouse /storm /dramaticlighting /8k /wideangle`.

0. **Plain English works too.** If the user writes no slashes ("Create me a cinematic album double exposure, size 16:9 and 9:16"),
   treat style words/phrases that match a command name (cinematic, double exposure, golden hour, 8k...) and ratios (16:9, 9:16) as
   those commands, remove them from the subject, and drop filler ("create me a", "size", "ratio", "frame", "both"). Do not treat
   ordinary subject words (forest, space, rain, beach) as styles unless written with a slash. Several ratios = one prompt per ratio.
1. **Extract** every `/token` from the message. Normalize: lowercase, remove spaces, hyphens and
   underscores (`/Rule Of Thirds`, `/rule-of-thirds` → `ruleofthirds`; `/freeezeaction` → `freezeaction`).
2. **Look up** each token in the table below. Unknown token → treat it as free text (keep the word,
   don't invent a meaning) and mention it in one short line.
3. **Strip** the tokens from the subject text; what remains is the *subject*. If no subject is given
   but a previous image prompt exists in the conversation, reuse that subject.
4. **Compose** one final prompt: `subject, <modifier phrases in order given>`.
   - Put the subject first, then camera/angle, then lighting/weather, then style/color/quality last.
   - If two modifiers conflict (e.g. `/blackandwhite` + `/vibrantcolors`, `/highkeylighting` + `/lowkeylighting`),
     keep the one that appears **last** and say which was dropped.
   - **Cap at 8 style modifiers** (reference commands don't count). Models ignore long stacks. If more are given, keep subject, genre/style, angle, camera, light first and drop quality/era/color extras last; say what was dropped.
   - **One winner per slot:** resolution (/hdreal /4k /8k /8ktextures), realism (/photorealistic /hyperrealistic /ultrarealistic /rawphoto), focal length (/14mm../200mm) and aperture (/f1.4 /f2.8 /f8): keep the last given.
   - Deduplicate overlapping phrases (`/8k` + `/4k` → keep the last resolution).
5. **Generate**: if an image-generation tool is available, call it with the composed prompt.
   Otherwise output the composed prompt in a code block, ready to paste into an image model.
   Always show the final prompt used.
6. If the user sends only modifiers with no subject and no prior prompt, ask what to draw.
7. Camera/lens commands (/85mm /f1.4 /tiltshift) matter more for realism than style words. Motion commands (/dolly /orbit /handheld /slowmotion) are for video tools (Kling, Flow); for a still image ignore them and say so.
8. **Subject controls** (category `subject`: /age30s /smile /walking /suit /longhair ...) describe the person and are placed right after the subject. One winner per group: age, expression, pose, gaze (/lookingatcamera vs /lookingaway), hair length.
9. **Reference commands** (/sameface /samestyle /samepose /samecomposition /samecolors /samelighting) need a reference image the user attached or linked. If none is present, ask for one. Midjourney: /sameface -> `--cref <url>`, /samestyle -> `--sref <url>`; other tools: say "use the attached reference". Only use reference images the user owns or has permission to use; never use them to imitate a private person without consent.
10. `/styles` or `/modifiers` → list the available categories (and a category's tokens if named).

Do not add extra creative elements the user didn't ask for; modifiers only change *how* the image
looks, never *what* is in it.
"""


# ---- aspect / negatives / models ----
def load(f):
    return [l.split("|") for l in (ROOT/"src"/f).read_text(encoding="utf-8").splitlines() if l.strip()]
aspects, negs, models = load("aspect.txt"), load("negatives.txt"), load("models.txt")
presets = load("presets.txt")
pre_tbl = chr(10).join(
    f"- `/{n}` ({label}) = " + " ".join("/" + t for t in toks.split()) + f" (default ratio /{ar})"
    for n, label, toks, ar in presets)
_known = set(names) | {a[0] for a in aspects} | {a[1] for a in aspects} | {x[0] for x in negs}
for n, label, toks, ar in presets:
    for t in toks.split():
        assert t in _known, f"preset {n}: unknown token {t}"
    assert ar in _known, f"preset {n}: unknown ratio {ar}"
asp_tbl = chr(10).join(f"- `/{n}` -> {r} ({px} px) {note}" for n, r, px, note in aspects)
neg_tbl = chr(10).join(f"- `/{n}` -> avoid: {t}" for n, t in negs)
mod_tbl = chr(10).join(f"- `/{n}` -> **{label}**: {how}" for n, label, how in models)

EXTRA_RULES = f"""
## Aspect-ratio commands
Accept ratios written as `/16:9`, `/16x9` or `/16-9`, plus the named aliases below. If several
are given, produce ONE prompt per ratio (labelled), not just the last. The pixel size is for models that need it (sd, flux).
{asp_tbl}

## Negative commands (things to avoid)
These do NOT add to the image; they build the "avoid" list. Merge every negative command used
into one list, deduplicated. Show it as a separate `Negative:` / `--no` / sentence per the model.
{neg_tbl}

## Presets (one command = a tested bundle)
Expand a preset into its commands, then process as normal. The user's own ratio overrides the preset's default ratio; user commands that conflict with the preset win.
{pre_tbl}

## Output-format commands (target model)
At most one. If none is given, use `/generic`. Adapt the final prompt to the model's style:
{mod_tbl}

Final answer layout when you cannot generate directly:
```
<prompt in the target model's format>
<negative / size / flags lines if the model uses them>
```
"""

skill = f"""---
name: image-style
description: Slash-command style modifiers for AI image generation. Use whenever the user writes an image/picture/photo/art request containing slash tokens such as /8k /cinematic /goldenhour /droneview /macro /cyberpunk /oilpainting /chiaroscuro (any of {len(rows)} style tokens), aspect ratios (/16:9 /9:16 /square), avoid-commands (/clean /nodeform) or a target model (/mj /sd /flux /dalle /gemini), or asks for /styles. Expands each token into precise prompt language, composes one final prompt, and generates the image.
---

# Image Style Modifiers ({len(rows)} style + {len(aspects)} aspect + {len(negs)} negative + {len(models)} model commands)

{RULES}
## Modifier table
{table}
{EXTRA_RULES}"""

out = ROOT / "dist" / "image-style"
out.mkdir(parents=True, exist_ok=True)
(out / "SKILL.md").write_text(skill, encoding="utf-8")
(out / "modifiers.json").write_text(
    json.dumps({n: {"category": c, "phrase": p} for n, c, p in rows}, indent=1, ensure_ascii=False),
    encoding="utf-8")
(out / "extras.json").write_text(json.dumps({"aspect":aspects,"negatives":negs,"models":models},indent=1),encoding="utf-8")

portable = f"""# Image Style Modifiers — instructions for any AI

Paste this whole file into the AI's custom instructions / system prompt / first message.

{RULES}
## Modifier table
{table}
{EXTRA_RULES}"""
(ROOT / "dist" / "portable-prompt.md").write_text(portable, encoding="utf-8")
print(f"{len(aspects)} aspect {len(negs)} neg {len(models)} models;",f"{len(rows)} modifiers, {len(cats)} categories")

# ---- plugin + marketplace ----
import shutil
MP = ROOT / "dist" / "marketplace"
PL = MP / "image-style"
MP.mkdir(parents=True, exist_ok=True)
for child in MP.iterdir():
    shutil.rmtree(child) if child.is_dir() else child.unlink()
(PL / ".claude-plugin").mkdir(parents=True)
(PL / "skills" / "image-style").mkdir(parents=True)
(PL / "commands").mkdir()
shutil.copy(out / "SKILL.md", PL / "skills" / "image-style" / "SKILL.md")
shutil.copy(out / "modifiers.json", PL / "skills" / "image-style" / "modifiers.json")
shutil.copy(out / "extras.json", PL / "skills" / "image-style" / "extras.json")

VERSION = "1.13.0"
(PL / ".claude-plugin" / "plugin.json").write_text(json.dumps({
    "name": "image-style",
    "version": VERSION,
    "description": f"{len(rows)} slash-command image style modifiers plus aspect ratios, negative prompts and per-model output (Midjourney, SD, Flux, DALL-E, Gemini).",
    "author": {"name": "GG"},
    "keywords": ["image", "prompt", "midjourney", "stable-diffusion", "photography"],
}, indent=2), encoding="utf-8")
(MP / ".claude-plugin").mkdir(exist_ok=True)
(MP / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
    "name": "image-style-market",
    "owner": {"name": "GG"},
    "description": "Image prompt style modifiers as slash commands",
    "plugins": [{"name": "image-style", "source": "./image-style",
                 "description": "Slash-command image style modifiers", "version": VERSION}],
}, indent=2), encoding="utf-8")

def cmd(name, desc, rule):
    body = f"""---
description: {json.dumps(desc)}
argument-hint: {json.dumps('<what to draw> [more /modifiers]')}
---
Use the image-style skill. Subject and any extra /modifiers: $ARGUMENTS

Apply this modifier: {rule}

Then follow the image-style skill: expand any other /tokens in the arguments, merge, resolve
conflicts, and generate the image (or output the final prompt if no image tool is available).
"""
    (PL / "commands" / f"{name}.md").write_text(body, encoding="utf-8")

n_cmds = 0
for n, c, p in rows:
    cmd(n, f"[{c}] {p[:90]}", f"`{p}`"); n_cmds += 1
for n, r, px, note in aspects:
    fn = n.replace(":", "x")
    cmd(fn, f"Aspect ratio {r} ({px})", f"aspect ratio {r}, {px} px for SD/Flux"); n_cmds += 1
for n, t in negs:
    cmd(n, f"Avoid: {t[:80]}", f"add to the avoid-list: {t}"); n_cmds += 1
for n, label, toks, ar in presets:
    cmd(n, f"Preset: {label}", "preset = " + " ".join("/" + t for t in toks.split()) + f" with default ratio /{ar}"); n_cmds += 1
for n, label, how in models:
    cmd(n, f"Format output for {label}", f"target model {label}. {how}"); n_cmds += 1
print(f"plugin: {n_cmds} commands")

exec(open(ROOT / "platforms.py", encoding="utf-8").read())

# ---- root-level marketplace so `claude plugin marketplace add <owner>/<repo>` works from GitHub ----
(ROOT / ".claude-plugin").mkdir(exist_ok=True)
(ROOT / ".claude-plugin" / "marketplace.json").write_text(json.dumps({
    "name": "image-style-market",
    "owner": {"name": "GG"},
    "description": "Image prompt style modifiers as slash commands",
    "plugins": [{"name": "image-style", "source": "./dist/marketplace/image-style",
                 "description": "Slash-command image style modifiers", "version": VERSION}],
}, indent=2), encoding="utf-8")


# ---- animated README demo (docs/demo.svg) ----
import subprocess as _sp, sys as _sys
_sp.run([_sys.executable, str(ROOT / "gen_demo_svg.py")], check=True)
