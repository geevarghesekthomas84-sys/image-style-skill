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
import re as _re
_tpl = (ROOT / "src" / "expander.template.html").read_text(encoding="utf-8").replace(
    "__DATA__", json.dumps(data, ensure_ascii=False))
_MARK = _re.compile(r"<!--/?FULL-->|/\*/?FULL\*/")
_BLOCK = _re.compile(r"<!--FULL-->.*?<!--/FULL-->|/\*FULL\*/.*?/\*/FULL\*/", _re.S)
_SMARK = _re.compile(r"<!--/?SITE-->|/\*/?SITE\*/")
_SBLOCK = _re.compile(r"<!--SITE-->.*?<!--/SITE-->|/\*SITE\*/.*?/\*/SITE\*/", _re.S)
html = _MARK.sub("", _SBLOCK.sub("", _tpl))        # downloadable version: everything except the website-only examples
hosted_html = _SMARK.sub("", _BLOCK.sub("", _tpl)) # website version: no helper, no copy-and-open, no image generation; has the examples
(PF / "flow-kling-anywhere" / "expander.html").write_text(html, encoding="utf-8")
(PF / "flow-kling-anywhere" / "SETUP.txt").write_text(
    "Google Flow and Kling have no skills or plugins.\n"
    "Open expander.html in any browser (works offline), type your request with /commands, pick the target, click Copy,\n"
    "and paste into the tool's prompt box. Put the Negative prompt line into Kling's negative-prompt field.\n", encoding="utf-8")
print("platforms built; instructions.txt chars:", len(COMPACT))


# ---- printable cheat sheet ----
import html as _html

def _e(x):
    return _html.escape(x)

names_all = [r[0] for r in rows] + [a[0] for a in aspects] + [n[0] for n in negs] + [m[0] for m in models] + [x[0] for x in presets]
secs = []
for c, items in cats.items():
    li = "".join(f"<li><b>/{_e(n)}</b> {_e(p)}</li>" for n, p in items)
    secs.append(f"<section><h2>{_e(c)} <small>{len(items)}</small></h2><ul>{li}</ul></section>")
secs.append("<section><h2>aspect ratios</h2><ul>" + "".join(
    f"<li><b>/{_e(n)}</b> {_e(r)} · {_e(px)} {_e(note)}</li>" for n, r, px, note in aspects) + "</ul></section>")
secs.append("<section><h2>avoid-lists</h2><ul>" + "".join(
    f"<li><b>/{_e(n)}</b> {_e(t)}</li>" for n, t in negs) + "</ul></section>")
secs.append("<section><h2>presets</h2><ul>" + "".join(
    f"<li><b>/{_e(n)}</b> {_e(label)}: {_e(toks)} · /{_e(ar)}</li>" for n, label, toks, ar in presets) + "</ul></section>")
secs.append("<section><h2>target models</h2><ul>" + "".join(
    f"<li><b>/{_e(n)}</b> {_e(label)}</li>" for n, label, how in models) + "</ul></section>")
sheet = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SlashFrame Cheat Sheet: 400+ AI Image Prompt Commands</title>
<meta name="description" content="Every SlashFrame slash command on one searchable page: camera and lens, lighting, weather, style, color, aspect ratios and presets for Midjourney, Flux and Stable Diffusion prompts.">
<link rel="canonical" href="https://glogee.online/cheatsheet.html">
<meta name="robots" content="index,follow">
<meta property="og:title" content="SlashFrame Cheat Sheet">
<meta property="og:url" content="https://glogee.online/cheatsheet.html">
<meta property="og:image" content="https://glogee.online/social-preview.png">
<link rel="icon" type="image/svg+xml" href="favicon.svg">
<style>
:root{{--bg:#fff;--fg:#1c1c22;--mut:#6c6b75;--line:#e2e0da;--acc:#5b4bff}}
@media(prefers-color-scheme:dark){{:root{{--bg:#131316;--fg:#ececf1;--mut:#92919c;--line:#2d2d34;--acc:#9a8dff}}}}
@media print{{:root{{--bg:#fff;--fg:#000;--mut:#444;--line:#bbb;--acc:#000}}body{{font-size:8.5pt}}}}
*{{box-sizing:border-box}}body{{margin:0;padding:20px;background:var(--bg);color:var(--fg);font:13px/1.45 system-ui,sans-serif}}
h1{{margin:0 0 4px;font-size:22px}}p{{margin:0 0 16px;color:var(--mut)}}
input{{width:100%;max-width:420px;padding:9px 12px;margin-bottom:16px;border:1px solid var(--line);border-radius:8px;background:transparent;color:var(--fg);font:inherit}}
@media print{{input{{display:none}}}}
main{{column-width:300px;column-gap:22px}}
section{{break-inside:avoid-column;margin-bottom:16px}}
h2{{margin:0 0 6px;font-size:13px;text-transform:uppercase;letter-spacing:.07em;color:var(--acc);border-bottom:1px solid var(--line);padding-bottom:3px}}
h2 small{{color:var(--mut);font-weight:400}}
ul{{list-style:none;margin:0;padding:0}}li{{padding:2px 0;color:var(--mut)}}li b{{color:var(--fg);font-family:ui-monospace,Consolas,monospace;margin-right:5px}}
li.hide{{display:none}}
</style></head><body>
<h1>SlashFrame Cheat Sheet</h1><p><a href="https://glogee.online/">&larr; Back to SlashFrame, the free prompt builder</a></p>
<p>{len(names_all)} commands. Add them to any image request, e.g. <code>a lighthouse /storm /85mm /16:9 /mj</code>. Print with Ctrl+P.</p>
<input id="q" placeholder="Filter commands…" autocomplete="off">
<main>{''.join(secs)}</main>
<script>document.getElementById("q").oninput=e=>{{const q=e.target.value.toLowerCase();document.querySelectorAll("li").forEach(l=>l.classList.toggle("hide",q&&!l.textContent.toLowerCase().includes(q)));document.querySelectorAll("section").forEach(s=>s.style.display=s.querySelector("li:not(.hide)")?"":"none")}}</script>
</body></html>"""
(ROOT / "dist" / "cheatsheet.html").write_text(sheet, encoding="utf-8")
print("cheat sheet written")


# ---- GitHub Pages site (served from /docs) ----
import datetime as _dt
DOCS = ROOT / "docs"
SITE_URL = "https://glogee.online/"
SITE_TITLE = "SlashFrame: Free AI Image Prompt Generator for Midjourney & Flux"
SITE_DESC = ("Free AI image prompt generator: type an idea plus /storm, /85mm or /16:9 and get a finished prompt "
             "for Midjourney, Flux, Gemini and more. No account.")

FAQ = [
    ("What is SlashFrame?",
     "SlashFrame is a free tool that turns a short idea plus slash commands (like /storm, /85mm or /16:9) into a finished, well-structured prompt for AI image and video tools."),
    ("Is SlashFrame free?",
     "Yes. It is free and open source under the MIT license. There is no account, no sign-up and nothing to install to use the website."),
    ("Which AI tools does it work with?",
     "It formats prompts for Midjourney, Stable Diffusion, Flux, DALL-E, Gemini, Google Flow and Kling. It also ships as a Claude skill and plugin, ChatGPT and Gemini instruction packs, and ComfyUI nodes."),
    ("How do the slash commands work?",
     "Each command stands for a piece of prompt wording. For example /storm adds violent storm, dark roiling clouds, lightning and wind, and /24mm adds a wide 24mm field of view. SlashFrame puts the pieces in a sensible order, resolves clashes and keeps the prompt short."),
    ("Does SlashFrame generate images?",
     "No. The website builds the prompt for you to copy into your image tool. It does not generate pictures itself."),
    ("Is my text sent anywhere?",
     "No. Your request is processed in your browser. The page only asks GitHub for the public star count."),
    ("How many commands are there?",
     "There are over 400: camera and lens, lighting, weather, style, color, portrait, product, aspect ratios, negative prompt lists and ready-made presets."),
]


def _faq_html():
    items = "".join(
        "<details class=\"qa\"><summary>%s</summary><p>%s</p></details>" % (_html.escape(a), _html.escape(b)) for a, b in FAQ)
    return items


def _jsonld():
    app = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "SlashFrame",
        "alternateName": "image-style",
        "url": SITE_URL,
        "description": SITE_DESC,
        "applicationCategory": "DesignApplication",
        "operatingSystem": "Any (web browser)",
        "browserRequirements": "Requires JavaScript",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
        "image": SITE_URL + "social-preview.png",
        "license": "https://opensource.org/licenses/MIT",
        "sameAs": ["https://github.com/geevarghesekthomas84-sys/image-style-skill"],
    }
    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": a,
                        "acceptedAnswer": {"@type": "Answer", "text": b}} for a, b in FAQ],
    }
    return "".join('<script type="application/ld+json">%s</script>\n' % json.dumps(x, ensure_ascii=False) for x in (app, faq))


site = hosted_html.replace("<!--FAQ-->", _faq_html())
site = _re.sub(r"<title>[^<]*</title>", "<title>%s</title>" % _html.escape(SITE_TITLE), site, count=1)
_img = SITE_URL + "social-preview.png"
meta = "\n".join([
    '<meta name="description" content="%s">' % _html.escape(SITE_DESC, quote=True),
    '<link rel="canonical" href="%s">' % SITE_URL,
    '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">',
    '<meta name="theme-color" content="#2a2163">',
    '<meta property="og:type" content="website">',
    '<meta property="og:site_name" content="SlashFrame">',
    '<meta property="og:title" content="%s">' % _html.escape(SITE_TITLE, quote=True),
    '<meta property="og:description" content="%s">' % _html.escape(SITE_DESC, quote=True),
    '<meta property="og:url" content="%s">' % SITE_URL,
    '<meta property="og:image" content="%s">' % _img,
    '<meta property="og:image:width" content="1280">',
    '<meta property="og:image:height" content="640">',
    '<meta property="og:image:alt" content="SlashFrame: slash commands that turn a short idea into an AI image prompt">',
    '<meta name="twitter:card" content="summary_large_image">',
    '<meta name="twitter:title" content="%s">' % _html.escape(SITE_TITLE, quote=True),
    '<meta name="twitter:description" content="%s">' % _html.escape(SITE_DESC, quote=True),
    '<meta name="twitter:image" content="%s">' % _img,
    '<link rel="icon" type="image/svg+xml" href="favicon.svg">',
    '<script>if(location.protocol==="http:"&&location.hostname==="glogee.online")location.replace("https://glogee.online"+location.pathname+location.search+location.hash)</script>',
]) + "\n" + _jsonld()
_t = _re.search(r"<title>[^<]*</title>", site).group(0)
site = site.replace(_t, _t + chr(10) + meta, 1)
(DOCS / "index.html").write_text(site, encoding="utf-8")
(DOCS / "cheatsheet.html").write_text((ROOT / "dist" / "cheatsheet.html").read_text(encoding="utf-8"), encoding="utf-8")
(DOCS / ".nojekyll").write_text("", encoding="utf-8")
shutil.copy(ROOT / ".github" / "social-preview.png", DOCS / "social-preview.png")
_today = _dt.date.today().isoformat()
(DOCS / "robots.txt").write_text("User-agent: *\nAllow: /\n\nSitemap: " + SITE_URL + "sitemap.xml\n", encoding="utf-8")
(DOCS / "sitemap.xml").write_text(
    '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join("  <url><loc>%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>\n" % (u, _today, c, p)
              for u, c, p in ((SITE_URL, "weekly", "1.0"), (SITE_URL + "cheatsheet.html", "monthly", "0.7")))
    + "</urlset>\n", encoding="utf-8")
(DOCS / "llms.txt").write_text(
    "# SlashFrame\n\n> Free, open-source tool that turns a short idea plus slash commands (/storm, /85mm, /16:9) into a finished prompt "
    "for Midjourney, Flux, Stable Diffusion, Gemini, DALL-E, Google Flow and Kling.\n\n"
    "- [Website](" + SITE_URL + "): build prompts in the browser, no account\n"
    "- [Cheat sheet](" + SITE_URL + "cheatsheet.html): all commands on one page\n"
    "- [Source code](https://github.com/geevarghesekthomas84-sys/image-style-skill): MIT license, Claude plugin, ComfyUI nodes\n", encoding="utf-8")
print("pages site written to docs/")


# ---- ComfyUI node data (single source of truth: the same src/*.txt files) ----
_CN = ROOT / "comfyui" / "ComfyUI-ImageStyle"
(_CN / "data").mkdir(parents=True, exist_ok=True)
(_CN / "data" / "imagestyle.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
shutil.copy(ROOT / "LICENSE", _CN / "LICENSE")
(_CN / "pyproject.toml").write_text(
    '[project]\nname = "comfyui-imagestyle"\n'
    f'version = "{VERSION}"\n'
    'description = "Turn short /commands (e.g. /storm /24mm /16:9) into full prompts, negative prompts and sizes."\n'
    'license = { text = "MIT" }\nreadme = "README.md"\n'
    'requires-python = ">=3.9"\n\n'
    '[project.urls]\nRepository = "https://github.com/geevarghesekthomas84-sys/image-style-skill"\n',
    encoding="utf-8")
print("comfyui node data written")


# zip of the ComfyUI node (no tests or caches) for easy install
(PF / "comfyui").mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(PF / "comfyui" / "ComfyUI-ImageStyle.zip", "w", zipfile.ZIP_DEFLATED) as _z:
    for _f in sorted(_CN.rglob("*")):
        if _f.is_file() and "__pycache__" not in _f.parts and "tests" not in _f.relative_to(_CN).parts:
            _z.write(_f, "ComfyUI-ImageStyle/" + _f.relative_to(_CN).as_posix())
(PF / "comfyui" / "SETUP.txt").write_text(
    "ComfyUI: unzip ComfyUI-ImageStyle.zip into ComfyUI/custom_nodes (ComfyUI Desktop: <install>/ComfyUI/custom_nodes), restart ComfyUI, "
    "then add node: image-style > Image Style Prompt. See the README inside the folder.", encoding="utf-8")
print("comfyui zip written")
