# Executed at the end of build.py (shares its variables).
import zipfile

PF = ROOT / "dist" / "platforms"
if PF.exists():
    for child in PF.iterdir():
        shutil.rmtree(child) if child.is_dir() else child.unlink()
for d in ("claude-ai", "chatgpt", "gemini", "flow-kling-anywhere"):
    (PF / d).mkdir(parents=True, exist_ok=True)

# Claude.ai: upload zip (Settings > Capabilities > Skills)
with zipfile.ZipFile(PF / "claude-ai" / "image-style.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for f in ("SKILL.md", "modifiers.json", "extras.json"):
        z.write(out / f, f"image-style/{f}")
(PF / "claude-ai" / "SETUP.txt").write_text(
    "Claude.ai: Settings > Capabilities > Skills > Upload skill > choose image-style.zip.\n"
    "Then ask for an image with /commands. (Claude.ai has no built-in image generator: it returns the final prompt to paste into an image tool.)\n",
    encoding="utf-8")

tables_md = f"# Image Style Modifier Tables\n{table}\n{EXTRA_RULES}"
COMPACT = RULES.replace("in the table below", "in the attached knowledge file image-style-knowledge.md") + (
    "\n## Aspect, negative and model commands\nAlso defined in image-style-knowledge.md. "
    "Ratios: /16:9 /9:16 /1:1 (/square) /4:3 /3:2 /21:9 /2:3 /3:4 /4:5 /3:1.\n"
    "Negatives (/clean /nodeform /sharpclean /nopeople /notext /nocrop /nooversat /noai) build an avoid-list.\n"
    "Model commands: " + ", ".join("/" + m[0] for m in models) + " - format the prompt for that tool.\n"
    "When the platform has native image generation (DALL-E in ChatGPT, Imagen in Gemini), generate directly with the composed prompt.\n")

SETUP = {
    "chatgpt": "ChatGPT: Explore GPTs > Create. Paste instructions.txt into Instructions, upload image-style-knowledge.md under Knowledge, enable Image Generation.\n"
               "No GPT access? Paste custom-instructions-short.txt into Settings > Personalization > Custom instructions (1500-char limit).\n",
    "gemini": "Gemini: gemini.google.com > Gem manager > New Gem. Paste instructions.txt into Instructions, add image-style-knowledge.md under Knowledge.\n",
}
for d, text in SETUP.items():
    (PF / d / "image-style-knowledge.md").write_text(tables_md, encoding="utf-8")
    (PF / d / "instructions.txt").write_text(COMPACT, encoding="utf-8")
    (PF / d / "SETUP.txt").write_text(text, encoding="utf-8")

short = ("When I write an image request with /commands (e.g. /8k /goldenhour /droneview /16:9 /clean /mj), expand each into rich prompt wording "
         "(8k = extreme detail, goldenhour = warm low sun, droneview = high aerial angle), put the subject first then camera, light, style, quality, "
         "drop the earlier of any conflicting pair, and generate the image. /16:9 /9:16 /square set the aspect ratio. /clean /nodeform /nopeople mean avoid "
         "text, bad hands, people. /mj /sd /flux /kling /flow /gemini /dalle format the prompt for that tool. Always show the final prompt.\n")
assert len(short) <= 1500
(PF / "chatgpt" / "custom-instructions-short.txt").write_text(short, encoding="utf-8")

data = {"mods": {n: {"category": c, "phrase": p} for n, c, p in rows},
        "aspect": aspects, "negatives": negs, "models": models, "categories": list(cats.keys()), "presets": presets}
html = (ROOT / "src" / "expander.template.html").read_text(encoding="utf-8").replace(
    "__DATA__", json.dumps(data, ensure_ascii=False))
(PF / "flow-kling-anywhere" / "expander.html").write_text(html, encoding="utf-8")
(PF / "flow-kling-anywhere" / "SETUP.txt").write_text(
    "Google Flow and Kling have no skills or plugins.\n"
    "Open expander.html in any browser (works offline), type your request with /commands, pick the target, click Copy,\n"
    "and paste into the tool's prompt box. Put the Negative prompt line into Kling's negative-prompt field.\n", encoding="utf-8")
print("platforms built; instructions.txt chars:", len(COMPACT))
