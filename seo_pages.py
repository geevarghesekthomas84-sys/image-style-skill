"""Builds the public website pages for SEO: home, one landing page per AI tool, a guide, sitemap, robots, llms.txt.

Called from platforms.py. The shared engine and layout come from src/expander.template.html (hosted version).
Texts here must stay truthful: they describe what the page really does.
"""
import datetime
import html as _h
import json
import re
import shutil

SITE_URL = "https://glogee.online/"
REPO = "https://github.com/geevarghesekthomas84-sys/image-style-skill"
INDEXNOW_KEY = "5b3fd61a9c0e4d27b8a1f6c3e2d94a70"
BRAND = "SlashFrame"

REQ = "a lone lighthouse on a cliff /storm /dramaticlighting /24mm /16:9 /clean"
EX = {
    "mj": "a lone lighthouse on a cliff, wide 24mm field of view, environmental context with natural perspective, violent storm, dark roiling clouds, lightning, wind, dramatic lighting, strong contrast between light and shadow --ar 16:9 --no text, watermark, logo, signature, caption, username",
    "sd": "Prompt: a lone lighthouse on a cliff, wide 24mm field of view, environmental context with natural perspective, violent storm, dark roiling clouds, lightning, wind, dramatic lighting, strong contrast between light and shadow\nNegative prompt: lowres, blurry, bad anatomy, watermark, text, watermark, logo, signature, caption, username\nSize: 1344x768",
    "flux": "a lone lighthouse on a cliff. Wide 24mm field of view, environmental context with natural perspective. Violent storm, dark roiling clouds, lightning, wind. Dramatic lighting, strong contrast between light and shadow. Clean image without text, watermark, logo, signature, caption, username.\nSize: 1344x768",
    "dalle": "a lone lighthouse on a cliff. Wide 24mm field of view, environmental context with natural perspective. Violent storm, dark roiling clouds, lightning, wind. Dramatic lighting, strong contrast between light and shadow. With no text, watermark, logo, signature, caption, username.\nSize: 1792x1024",
    "gemini": "a lone lighthouse on a cliff. Wide 24mm field of view, environmental context with natural perspective. Violent storm, dark roiling clouds, lightning, wind. Dramatic lighting, strong contrast between light and shadow. Avoid text, watermark, logo, signature, caption, username.\nAspect ratio: 16:9",
    "flow": "a lone lighthouse on a cliff. Wide 24mm field of view, environmental context with natural perspective. Violent storm, dark roiling clouds, lightning, wind. Dramatic lighting, strong contrast between light and shadow. Avoid text, watermark, logo, signature, caption, username.\nSet aspect ratio to 16:9",
    "kling": "a lone lighthouse on a cliff. Wide 24mm field of view, environmental context with natural perspective. Violent storm, dark roiling clouds, lightning, wind. Dramatic lighting, strong contrast between light and shadow.\nNegative prompt: text, watermark, logo, signature, caption, username\nAspect ratio: 16:9",
}

HOME_TITLE = "Free AI Image Prompt Generator: Midjourney, Flux | SlashFrame"
HOME_DESC = ("Free AI image prompt generator. Type an idea plus slash commands and get a finished prompt "
             "for Midjourney, Flux, Stable Diffusion, Gemini and more.")

HOME_FAQ = [
    ("What is SlashFrame?",
     "SlashFrame is a free prompt generator for AI images. You type a short idea plus slash commands (like /storm, /85mm or /16:9) and it builds a finished, well-structured prompt for your image or video tool."),
    ("Is SlashFrame a free prompt generator?",
     "Yes. It is free and open source under the MIT license. There is no account, no sign-up and nothing to install to use the website."),
    ("Which AI tools does it work with?",
     "It formats prompts for Midjourney, Stable Diffusion, Flux, DALL-E and ChatGPT, Gemini, Google Flow and Kling. It also ships as a Claude skill and plugin, ChatGPT and Gemini instruction packs, and ComfyUI nodes."),
    ("How do the slash commands work?",
     "Each command stands for a piece of prompt wording. For example /storm adds violent storm, dark roiling clouds, lightning and wind, and /24mm adds a wide 24mm field of view. SlashFrame puts the pieces in a sensible order, resolves clashes and keeps the prompt short."),
    ("Does SlashFrame generate images?",
     "No. The website builds the prompt for you to copy into your image tool. It does not generate pictures itself."),
    ("Is my text sent anywhere?",
     "No. Your request is processed in your browser. The page only asks GitHub for the public star count."),
    ("How many commands are there?",
     "There are over 400: camera and lens, lighting, weather, style, color, portrait, product, aspect ratios, negative prompt lists and ready-made presets."),
    ("Is there a free prompt generator for Midjourney, Flux and Stable Diffusion in one place?",
     "Yes. Pick your tool in step 2 and the same request comes out in that tool's format: Midjourney parameters, Flux sentences, or a Stable Diffusion prompt with a negative prompt and size."),
    ("Can I use the prompts commercially?",
     "SlashFrame only writes the prompt text for you. What you may do with the images depends on the terms of the image tool you paste the prompt into."),
]

# slug, tool key, short name, h1, em line, lead, about heading, paragraphs, extra faq
TARGETS = [
    dict(slug="midjourney-prompt-generator", key="mj", name="Midjourney",
         title="Free Midjourney Prompt Generator (--ar, --no) | SlashFrame",
         desc="Free Midjourney prompt generator. Turn a short idea plus slash commands into a finished Midjourney prompt with --ar and --no already added. No sign-up.",
         h1="Free Midjourney prompt generator.", em="Prompts with --ar and --no built in.",
         lead="Type your idea and a few slash commands. SlashFrame writes a Midjourney-style prompt (comma-separated phrases) and adds the <b>--ar</b> aspect ratio and a <b>--no</b> list at the end. Free, runs in your browser, no sign-up.",
         about="How the Midjourney prompt format works",
         paras=["Midjourney prompts are read as a list of descriptive phrases, with the subject first and the details after it. Settings such as the aspect ratio (<code>--ar 16:9</code>) and things to leave out (<code>--no text, watermark</code>) go at the end of the prompt.",
                "SlashFrame builds exactly that. A command like <code>/goldenhour</code> becomes the phrase \"golden hour, warm low-angle sunlight, long soft shadows\", a ratio command such as <code>/16:9</code> becomes <code>--ar 16:9</code>, and an avoid-list such as <code>/clean</code> becomes a <code>--no</code> list.",
                "Using <code>/sameface</code> or <code>/samestyle</code> adds the placeholders <code>--cref [face image URL]</code> and <code>--sref [style image URL]</code>, so you only paste your own image links."],
         faq=[("Does the Midjourney prompt generator add --ar for me?", "Yes. Add a ratio command like /16:9 or /9:16 and the prompt ends with the matching --ar value. If you ask for several ratios, you get one prompt per ratio."),
              ("How do I leave things out in Midjourney?", "Use an avoid command such as /clean, /nopeople or /notext. SlashFrame writes the matching words after --no.")]),
    dict(slug="flux-prompt-generator", key="flux", name="Flux",
         title="Free Flux Prompt Generator (natural sentences) | SlashFrame",
         desc="Free Flux prompt generator. Turn a short idea plus slash commands into clear natural-language Flux prompts with the image size included. No sign-up.",
         h1="Free Flux prompt generator.", em="Clear sentences, with the size included.",
         lead="Flux follows natural sentences well. Type your idea and a few slash commands and SlashFrame writes a sentence-style Flux prompt and a recommended image size such as 1344x768. Free, in your browser, no sign-up.",
         about="Writing prompts for Flux",
         paras=["Flux and similar newer models respond well to short, natural sentences more than to long lists of keywords. They also have no separate negative prompt box in the usual setup, so unwanted things are better phrased inside the prompt.",
                "SlashFrame writes each command as its own sentence, puts the subject first, and turns avoid-commands into one closing sentence such as \"Clean image without text, watermark, logo\". It also gives a size that matches your ratio, for example 1344x768 for 16:9.",
                "The same output works for other sentence-based models, for example Flux-style workflows in ComfyUI. SlashFrame also ships ComfyUI nodes that do this inside your workflow."],
         faq=[("Does Flux need a negative prompt?", "In the standard Flux setup there is no negative prompt box. SlashFrame writes avoid-commands as a closing sentence, such as \"Clean image without text, watermark.\""),
              ("What size does the Flux prompt generator suggest?", "It matches your ratio command, for example 1344x768 for /16:9 and 768x1344 for /9:16, at about one megapixel.")]),
    dict(slug="stable-diffusion-prompt-generator", key="sd", name="Stable Diffusion",
         title="Free Stable Diffusion Prompt Generator | SlashFrame",
         desc="Free Stable Diffusion prompt generator. Build a prompt, a negative prompt and an image size from a short idea plus slash commands. No sign-up.",
         h1="Free Stable Diffusion prompt generator.", em="Prompt, negative prompt and size in one go.",
         lead="Type your idea and a few slash commands. SlashFrame writes the <b>Prompt</b>, a ready <b>Negative prompt</b> and the <b>Size</b> in the layout Stable Diffusion tools expect. Free, in your browser, no sign-up.",
         about="Prompt and negative prompt for Stable Diffusion",
         paras=["Stable Diffusion tools such as Automatic1111, Forge and ComfyUI take a prompt and a separate negative prompt, plus an image size. Keyword-style prompts with commas are the traditional format.",
                "SlashFrame outputs three lines: <code>Prompt:</code>, <code>Negative prompt:</code> and <code>Size:</code>. The negative prompt starts with common basics (lowres, blurry, bad anatomy, watermark) and adds more when you use avoid-commands like /nodeform or /notext.",
                "If you work in ComfyUI, the free SlashFrame nodes give you the positive prompt, negative prompt, width and height as separate outputs you can wire straight into your workflow."],
         faq=[("Does it write a negative prompt for Stable Diffusion?", "Yes. Every result includes a negative prompt with the usual basics, and avoid-commands add more terms."),
              ("Can I use it with SDXL and Pony models?", "Yes. The keyword-style output suits SD 1.5, SDXL and Pony-style models. Check the size your model prefers and set a matching ratio command.")]),
    dict(slug="chatgpt-image-prompt-generator", key="dalle", name="ChatGPT and DALL-E",
         title="Free ChatGPT & DALL-E Image Prompt Generator | SlashFrame",
         desc="Free image prompt generator for ChatGPT and DALL-E. Turn a short idea plus slash commands into a clear prompt with the right size. No sign-up.",
         h1="Free ChatGPT & DALL-E image prompt generator.", em="Clear sentences and the right size.",
         lead="Type your idea and a few slash commands. SlashFrame writes a clear, sentence-style prompt for ChatGPT and DALL-E, with a size such as 1792x1024 for wide pictures. Free, in your browser, no sign-up.",
         about="Prompts for ChatGPT and DALL-E images",
         paras=["ChatGPT and DALL-E understand ordinary sentences. A good prompt names the subject first, then the camera or angle, the lighting, the style and anything to avoid.",
                "SlashFrame writes one sentence per command and ends with the size: 1024x1024 for square, 1792x1024 for wide and 1024x1792 for tall pictures. Avoid-commands become one closing sentence such as \"With no text, watermark, logo.\"",
                "You can also load the SlashFrame instructions into a custom GPT, so the slash commands work inside ChatGPT itself. The steps are in the project README."],
         faq=[("Which sizes does the ChatGPT prompt generator use?", "1024x1024 for square, 1792x1024 for wide and 1024x1792 for tall, chosen from your ratio command."),
              ("Can I use slash commands inside ChatGPT?", "Yes. The project includes custom GPT instructions and a knowledge file, so ChatGPT understands the same slash commands.")]),
    dict(slug="gemini-image-prompt-generator", key="gemini", name="Gemini",
         title="Free Gemini Image Prompt Generator | SlashFrame",
         desc="Free Gemini image prompt generator. Turn a short idea plus slash commands into a clear Gemini prompt with the aspect ratio included. No sign-up.",
         h1="Free Gemini image prompt generator.", em="Natural sentences plus the aspect ratio.",
         lead="Type your idea and a few slash commands. SlashFrame writes a natural-sentence prompt for Gemini and adds the aspect ratio on its own line. Free, in your browser, no sign-up.",
         about="Writing image prompts for Gemini",
         paras=["Gemini reads natural language, so a prompt works best as a few clear sentences: the subject first, then the angle and lens look, the light, the style and what to avoid.",
                "SlashFrame writes each command as a sentence, adds an \"Avoid ...\" sentence for avoid-commands and puts <code>Aspect ratio: 16:9</code> on its own line when you ask for a ratio.",
                "There is also a ready-made Gemini Gem pack in the project, so you can use the slash commands directly inside Gemini."],
         faq=[("Does the Gemini prompt generator set the aspect ratio?", "Yes. Add a ratio command like /16:9 and the prompt ends with an Aspect ratio line."),
              ("Can I use slash commands inside a Gemini Gem?", "Yes. The project includes instructions and a knowledge file for a Gemini Gem.")]),
    dict(slug="google-flow-prompt-generator", key="flow", name="Google Flow",
         title="Free Google Flow Prompt Generator | SlashFrame",
         desc="Free Google Flow prompt generator. Turn a short idea plus slash commands into a clear prompt for Flow, with a 16:9 or 9:16 aspect ratio note.",
         h1="Free Google Flow prompt generator.", em="Clear prompts with a 16:9 or 9:16 note.",
         lead="Type your idea and a few slash commands. SlashFrame writes a sentence-style prompt for Google Flow and tells you which aspect ratio to set. Free, in your browser, no sign-up.",
         about="Prompts for Google Flow",
         paras=["Google Flow works with video-style output, which supports wide 16:9 and tall 9:16 frames. A good prompt describes the subject, the camera move or angle, the light and the style in plain sentences.",
                "SlashFrame writes one sentence per command and ends with a line such as \"Set aspect ratio to 16:9\". If you ask for another ratio, it adds a note that video supports 16:9 or 9:16 only.",
                "Motion commands such as /dolly, /orbit and /handheld describe camera movement and are meant for video tools like Flow and Kling."],
         faq=[("Which aspect ratios does Google Flow support?", "Flow video supports 16:9 and 9:16. SlashFrame adds a note if you ask for any other ratio."),
              ("Are there camera-motion commands?", "Yes. Commands such as /dolly, /orbit, /pan, /crane, /handheld and /slowmotion describe camera movement for video prompts.")]),
    dict(slug="kling-prompt-generator", key="kling", name="Kling AI",
         title="Free Kling AI Prompt Generator | SlashFrame",
         desc="Free Kling AI prompt generator. Turn a short idea plus slash commands into a clear Kling prompt with a negative prompt line and aspect ratio. No sign-up.",
         h1="Free Kling AI prompt generator.", em="Prompt, negative prompt and aspect ratio.",
         lead="Type your idea and a few slash commands. SlashFrame writes a sentence-style prompt for Kling, a separate negative prompt line to paste into Kling's negative field, and the aspect ratio. Free, in your browser, no sign-up.",
         about="Prompts for Kling AI",
         paras=["Kling has a separate negative prompt field, so unwanted things should not be mixed into the main prompt. A good Kling prompt describes the subject, the camera, the light and the style in clear sentences.",
                "SlashFrame outputs the main prompt, then a <code>Negative prompt:</code> line to paste into Kling's negative field, then the aspect ratio. Kling supports 1:1, 16:9 and 9:16, and other ratios are mapped to the nearest wide or tall one.",
                "Camera-motion commands such as /dolly, /orbit, /tracking and /handheld help when you use Kling for video."],
         faq=[("Does Kling have a negative prompt?", "Yes. SlashFrame writes a separate Negative prompt line for Kling's negative-prompt field."),
              ("Which aspect ratios does the Kling prompt generator use?", "1:1, 16:9 and 9:16. Other ratios are mapped to the closest wide or tall option.")]),
]

TARGET_INDEX = [("Midjourney", "midjourney-prompt-generator", "Prompts with --ar and --no"),
                ("Flux", "flux-prompt-generator", "Natural sentences and size"),
                ("Stable Diffusion", "stable-diffusion-prompt-generator", "Prompt, negative prompt, size"),
                ("ChatGPT & DALL-E", "chatgpt-image-prompt-generator", "Sentences and DALL-E sizes"),
                ("Gemini", "gemini-image-prompt-generator", "Sentences plus aspect ratio"),
                ("Google Flow", "google-flow-prompt-generator", "16:9 and 9:16 video frames"),
                ("Kling AI", "kling-prompt-generator", "With a negative prompt line")]

GUIDE_SLUG = "guide/how-to-write-ai-image-prompts"
GUIDE_TITLE = "How to Write AI Image Prompts: Simple Formula | SlashFrame"
GUIDE_DESC = "A simple formula for writing AI image prompts that work in Midjourney, Flux, Stable Diffusion, Gemini and ChatGPT, with before and after examples."

ABOUT_SLUG = "about"
ABOUT_TITLE = "About SlashFrame | Free AI Image Prompt Generator"
ABOUT_DESC = "SlashFrame is a free, open-source AI image prompt generator. Learn who built it, how it works, and how to get in touch."


def e(x):
    return _h.escape(x)


def _faq_html(faq):
    return "".join('<details class="qa"><summary>%s</summary><p>%s</p></details>' % (e(a), e(b)) for a, b in faq)


def _ld(objs):
    return "".join('<script type="application/ld+json">%s</script>\n' % json.dumps(o, ensure_ascii=False) for o in objs)


def _faq_ld(faq):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": a, "acceptedAnswer": {"@type": "Answer", "text": b}} for a, b in faq]}


def _crumb_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}


def _app_ld(name, url, desc):
    return {"@context": "https://schema.org", "@type": "WebApplication", "name": name, "alternateName": "image-style",
            "url": url, "description": desc, "applicationCategory": "DesignApplication",
            "operatingSystem": "Any (web browser)", "browserRequirements": "Requires JavaScript",
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "image": SITE_URL + "social-preview.png", "license": "https://opensource.org/licenses/MIT",
            "isAccessibleForFree": True, "inLanguage": "en", "sameAs": [REPO]}


def _head_meta(url, title, desc, ld, target=None):
    img = SITE_URL + "social-preview.png"
    lines = [
        '<meta name="description" content="%s">' % e(desc),
        '<link rel="canonical" href="%s">' % url,
        '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1">',
        '<meta name="theme-color" content="#2a2163">',
        '<meta property="og:type" content="website">',
        '<meta property="og:locale" content="en_US">',
        '<meta property="og:site_name" content="%s">' % BRAND,
        '<meta property="og:title" content="%s">' % e(title),
        '<meta property="og:description" content="%s">' % e(desc),
        '<meta property="og:url" content="%s">' % url,
        '<meta property="og:image" content="%s">' % img,
        '<meta property="og:image:width" content="1280">',
        '<meta property="og:image:height" content="640">',
        '<meta property="og:image:alt" content="SlashFrame: free prompt generator for AI images">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<meta name="twitter:title" content="%s">' % e(title),
        '<meta name="twitter:description" content="%s">' % e(desc),
        '<meta name="twitter:image" content="%s">' % img,
        '<link rel="icon" type="image/svg+xml" href="/favicon.svg">',
        '<script>if(location.protocol==="http:"&&location.hostname==="glogee.online")location.replace("https://glogee.online"+location.pathname+location.search+location.hash)</script>',
    ]
    if target:
        lines.append('<script>window.__T="%s"</script>' % target)
    return "\n".join(lines) + "\n" + _ld(ld)


def _tools_html(current=None):
    cards = "".join(
        '<a class="tcard%s" href="/%s/"><b>%s prompt generator</b><span>%s</span></a>' % (" on" if s == current else "", s, e(n), e(t))
        for n, s, t in TARGET_INDEX)
    return ('<div class="tcards">%s</div><p class="tmore">New to prompts? Read <a href="/%s/">how to write AI image prompts</a>, '
            'or browse the <a href="/cheatsheet.html">command cheat sheet</a>.</p>' % (cards, GUIDE_SLUG + "/"))


def _foot_html():
    links = " &middot; ".join('<a href="/%s/">%s</a>' % (s, e(n)) for n, s, t in TARGET_INDEX)
    return ('<div class="wrap fl"><div><b>Free prompt generators</b><br>%s</div>'
            '<div><b>Learn</b><br><a href="/%s/">How to write AI image prompts</a> &middot; <a href="/cheatsheet.html">Cheat sheet</a> &middot; <a href="/%s/">About & Contact</a></div></div>'
            % (links, GUIDE_SLUG + "/", ABOUT_SLUG + "/"))


def _render(base, url, title, desc, faq, ld_extra=None, target=None, h1=None, lead=None, about_html="", current=None):
    s = base
    s = s.replace("<!--FAQ-->", _faq_html(faq))
    s = s.replace("<!--TOOLS-->", _tools_html(current))
    s = s.replace("<!--FOOT-->", _foot_html())
    s = s.replace("<!--ABOUT-->", about_html)
    if h1:
        s = re.sub(r"<!--H1-->.*?<!--/H1-->", lambda m: h1, s, count=1, flags=re.S)
    if lead:
        s = re.sub(r"<!--LEAD-->.*?<!--/LEAD-->", lambda m: lead, s, count=1, flags=re.S)
    s = re.sub(r"<!--/?(?:H1|LEAD)-->", "", s)
    if target:
        key_name = next(t["name"] for t in TARGETS if t["key"] == target)
        s = s.replace("You get (Midjourney format)", "You get (%s format)" % e(key_name), 1)
        s = re.sub(r'<div class="hout">.*?</div>', lambda m: '<div class="hout">%s</div>' % e(EX[target]).replace(chr(10), "<br>"), s, count=1, flags=re.S)
        s = re.sub(r'<div class="hin">.*?</div>', lambda m: '<div class="hin">a lone lighthouse on a cliff <b>/storm /dramaticlighting /24mm /16:9 /clean</b></div>', s, count=1, flags=re.S)
    s = re.sub(r"<title>[^<]*</title>", lambda m: "<title>%s</title>" % e(title), s, count=1)
    ld = [_app_ld("SlashFrame prompt generator" if not target else title.split(" |")[0].replace("Free ", "SlashFrame ", 1), url, desc)]
    ld += ld_extra or []
    ld.append(_faq_ld(faq))
    t = re.search(r"<title>[^<]*</title>", s).group(0)
    s = s.replace(t, t + "\n" + _head_meta(url, title, desc, ld, target), 1)
    # absolute asset paths so pages work from sub-folders
    s = s.replace('src="demo.gif"', 'src="/demo.gif"').replace('src="support-qr.webp"', 'src="/support-qr.webp"')
    return s


def _about_html(t):
    ex = EX[t["key"]]
    return (
        '<section class="band" id="about"><div class="wrap prose">'
        '<p class="eyebrow">About</p><h2 class="title">%s</h2>%s'
        '<h3>Example: the same idea for %s</h3>'
        '<p>You type:</p><pre class="ex">%s</pre><p>You get:</p><pre class="ex">%s</pre>'
        '<p class="note2">Want a different tool? <a href="/">See all free prompt generators</a>.</p>'
        '</div></section>' % (e(t["about"]), "".join("<p>%s</p>" % p for p in t["paras"]), e(t["name"]), e(REQ), e(ex)))


GUIDE_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
__META__
<style>
:root{--bg:#f6f5f1;--panel:#fff;--fg:#14141a;--mut:#5c5b67;--line:#e4e2db;--acc:#5b4bff;--code:#f1efea}
@media(prefers-color-scheme:dark){:root{--bg:#0b0b10;--panel:#15151c;--fg:#f0f0f5;--mut:#a3a2b2;--line:#26262f;--acc:#a79dff;--code:#101015}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.7 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--acc)}.top{border-bottom:1px solid var(--line)}.top .in{max-width:860px;margin:0 auto;padding:16px 20px;display:flex;justify-content:space-between;align-items:center}
.logo{font-weight:800;font-size:19px;letter-spacing:-.03em;color:var(--fg);text-decoration:none}.logo span{color:var(--acc)}
.btn{background:linear-gradient(135deg,#6b5bff,#8a5bff);color:#fff!important;text-decoration:none;padding:10px 18px;border-radius:11px;font-weight:700;font-size:15px}
main{max-width:760px;margin:0 auto;padding:36px 20px 70px}h1{font-size:clamp(30px,5vw,44px);line-height:1.12;letter-spacing:-.035em;margin:0 0 14px}
h2{font-size:26px;letter-spacing:-.02em;margin:44px 0 10px}h3{font-size:19px;margin:26px 0 6px}.meta{color:var(--mut);font-size:14.5px;margin:0 0 26px}
p,li{color:var(--fg)}pre{background:var(--code);border:1px solid var(--line);border-left:4px solid var(--acc);border-radius:12px;padding:14px 16px;white-space:pre-wrap;word-break:break-word;font:14px/1.65 ui-monospace,SFMono-Regular,Consolas,monospace}
code{background:var(--code);padding:2px 7px;border-radius:6px;font-size:.92em}.cta{margin:40px 0;padding:26px;border-radius:18px;background:var(--panel);border:1px solid var(--line);text-align:center}
.cta p{margin:0 0 14px}footer{border-top:1px solid var(--line);padding:26px 20px;color:var(--mut);font-size:14.5px;text-align:center}footer a{color:var(--mut)}
nav.bc{font-size:14px;color:var(--mut);margin-bottom:18px}nav.bc a{color:var(--mut)}
</style></head><body>
<div class="top"><div class="in"><a class="logo" href="/">Slash<span>Frame</span></a><a class="btn" href="/#tool">Open the free generator</a></div></div>
<main><nav class="bc"><a href="/">Home</a> &rsaquo; Guide</nav>
<h1>How to write AI image prompts: a simple formula</h1>
<p class="meta">Updated __DATE__ &middot; 5 minute read &middot; works for Midjourney, Flux, Stable Diffusion, Gemini and ChatGPT</p>
<p>A good AI image prompt is not long or magic. It is a short list of clear decisions, written in a sensible order. This guide gives you a formula you can reuse in any image tool, plus before and after examples. If you want to skip the typing, the <a href="/">free prompt generator</a> on this site builds the final wording for you from short slash commands.</p>
<h2>The formula: subject, view, light, style, extras</h2>
<ol>
<li><b>Subject first.</b> Say what the picture is of, in plain words: "a lone lighthouse on a cliff". Models give the most weight to the start of the prompt.</li>
<li><b>View and lens.</b> Say how close or far the camera is and the angle: "wide 24mm field of view", "close-up", "low angle", "top-down".</li>
<li><b>Light and weather.</b> Light changes the mood more than anything else: "golden hour, warm low-angle sunlight", "violent storm, dark clouds", "soft window light".</li>
<li><b>Style or medium.</b> Photo, oil painting, 3D render, matte painting, watercolor.</li>
<li><b>Extras.</b> Colors, detail level, and things to avoid such as text or watermarks.</li>
</ol>
<h2>Before and after</h2>
<p>Plain idea:</p><pre>a lone lighthouse on a cliff</pre>
<p>The same idea, with the formula applied (Midjourney format):</p><pre>__MJ__</pre>
<p>The wording after the subject came from four short slash commands: <code>/storm /dramaticlighting /24mm /16:9</code> plus <code>/clean</code> for the avoid list. You can try this exact request in the <a href="/">generator</a>.</p>
<h2>Each tool likes a slightly different format</h2>
<ul>
<li><b>Midjourney</b> reads comma-separated phrases. Settings go at the end: <code>--ar 16:9</code> for the aspect ratio and <code>--no text</code> to leave things out. See the <a href="/midjourney-prompt-generator/">Midjourney prompt generator</a>.</li>
<li><b>Flux</b> follows natural sentences well. See the <a href="/flux-prompt-generator/">Flux prompt generator</a>.</li>
<li><b>Stable Diffusion</b> takes a prompt plus a separate negative prompt and a size. See the <a href="/stable-diffusion-prompt-generator/">Stable Diffusion prompt generator</a>.</li>
<li><b>ChatGPT and DALL-E</b> and <b>Gemini</b> understand ordinary sentences. See the <a href="/chatgpt-image-prompt-generator/">ChatGPT</a> and <a href="/gemini-image-prompt-generator/">Gemini</a> generators.</li>
<li><b>Google Flow and Kling</b> are video-oriented and use 16:9 or 9:16 frames. See the <a href="/google-flow-prompt-generator/">Google Flow</a> and <a href="/kling-prompt-generator/">Kling</a> generators.</li>
</ul>
<h2>Common mistakes</h2>
<ul>
<li><b>Too many style words.</b> Stacking ten modifiers makes models ignore most of them. Keep about eight at most and drop clashing ones, such as "black and white" with "vibrant colors".</li>
<li><b>Naming equipment.</b> Writing "200mm telephoto lens" can make some models draw a lens or camera in the picture. Describe the look instead: "200mm look, strong background compression".</li>
<li><b>Hiding the subject.</b> If the subject is buried in the middle, results drift. Keep it first.</li>
<li><b>Fighting the format.</b> Pasting Midjourney parameters into a sentence-based tool does nothing useful. Match the tool.</li>
<li><b>Expecting an edit.</b> A prompt creates a new picture. To change an existing picture, use an image-to-image or instruction-edit model.</li>
</ul>
<h2>A quick checklist</h2>
<ul><li>Subject in the first few words</li><li>One clear view or lens look</li><li>One clear lighting idea</li><li>One style or medium</li><li>The right aspect ratio for where the image will be used</li><li>An avoid list if you see unwanted text or watermarks</li></ul>
<div class="cta"><p><b>Skip the typing.</b> Write your idea, add a few slash commands, pick your tool and copy the finished prompt. Free, no account.</p><a class="btn" href="/#tool">Open the free prompt generator</a></div>
</main>
<footer>__FOOT__<p style="margin:14px 0 0">SlashFrame &middot; MIT license &middot; <a href="__REPO__">GitHub</a></p></footer>
</body></html>"""


def _guide_page(today):
    url = SITE_URL + GUIDE_SLUG + "/"
    article = {"@context": "https://schema.org", "@type": "Article", "headline": "How to write AI image prompts: a simple formula",
               "description": GUIDE_DESC, "datePublished": today, "dateModified": today, "inLanguage": "en",
               "image": SITE_URL + "social-preview.png", "mainEntityOfPage": url,
               "author": {"@type": "Organization", "name": BRAND, "url": SITE_URL},
               "publisher": {"@type": "Organization", "name": BRAND, "url": SITE_URL}}
    crumbs = _crumb_ld([("Home", SITE_URL), ("Guide", url)])
    meta = _head_meta(url, GUIDE_TITLE, GUIDE_DESC, [article, crumbs])
    foot = '<div style="margin-bottom:6px">Free prompt generators: ' + " &middot; ".join('<a href="/%s/">%s</a>' % (s, e(n)) for n, s, t in TARGET_INDEX) + "</div>"
    out = GUIDE_HTML
    for k, v in (("__TITLE__", e(GUIDE_TITLE)), ("__META__", meta), ("__DATE__", today), ("__MJ__", e(EX["mj"])), ("__FOOT__", foot), ("__REPO__", REPO)):
        out = out.replace(k, v)
    return out


ABOUT_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title>
__META__
<style>
:root{--bg:#f6f5f1;--panel:#fff;--fg:#14141a;--mut:#5c5b67;--line:#e4e2db;--acc:#5b4bff;--code:#f1efea}
@media(prefers-color-scheme:dark){:root{--bg:#0b0b10;--panel:#15151c;--fg:#f0f0f5;--mut:#a3a2b2;--line:#26262f;--acc:#a79dff;--code:#101015}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.7 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
a{color:var(--acc)}.top{border-bottom:1px solid var(--line)}.top .in{max-width:860px;margin:0 auto;padding:16px 20px;display:flex;justify-content:space-between;align-items:center}
.logo{font-weight:800;font-size:19px;letter-spacing:-.03em;color:var(--fg);text-decoration:none}.logo span{color:var(--acc)}
.btn{background:linear-gradient(135deg,#6b5bff,#8a5bff);color:#fff!important;text-decoration:none;padding:10px 18px;border-radius:11px;font-weight:700;font-size:15px}
main{max-width:760px;margin:0 auto;padding:36px 20px 70px}h1{font-size:clamp(30px,5vw,44px);line-height:1.12;letter-spacing:-.035em;margin:0 0 14px}
h2{font-size:26px;letter-spacing:-.02em;margin:44px 0 10px}h3{font-size:19px;margin:26px 0 6px}
p,li{color:var(--fg)}
code{background:var(--code);padding:2px 7px;border-radius:6px;font-size:.92em}
.card{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:26px;margin:20px 0;box-shadow:0 1px 3px rgba(0,0,0,.06)}
.cta{margin:40px 0;padding:26px;border-radius:18px;background:var(--panel);border:1px solid var(--line);text-align:center}
.cta p{margin:0 0 14px}footer{border-top:1px solid var(--line);padding:26px 20px;color:var(--mut);font-size:14.5px;text-align:center}footer a{color:var(--mut)}
nav.bc{font-size:14px;color:var(--mut);margin-bottom:18px}nav.bc a{color:var(--mut)}
</style></head><body>
<div class="top"><div class="in"><a class="logo" href="/">Slash<span>Frame</span></a><a class="btn" href="/#tool">Open the free generator</a></div></div>
<main><nav class="bc"><a href="/">Home</a> &rsaquo; About</nav>
<h1>About SlashFrame</h1>
<p>SlashFrame is a free, open-source AI image prompt generator. It turns a short idea plus slash commands like <code>/storm</code>, <code>/85mm</code> or <code>/16:9</code> into a finished prompt for Midjourney, Flux, Stable Diffusion, ChatGPT, Gemini, Google Flow and Kling.</p>

<h2>How it works</h2>
<p>You type a subject and add slash commands. Each command stands for a piece of prompt wording: <code>/storm</code> becomes "violent storm, dark roiling clouds, lightning, wind", <code>/85mm</code> becomes a portrait-style lens look, <code>/16:9</code> sets a widescreen ratio. SlashFrame puts everything in a sensible order, resolves clashes and formats the result for your chosen tool.</p>
<p>There are over 400 commands covering camera and lens, lighting, weather, style, color, portrait, product photography, aspect ratios, negative prompts and presets. Browse them all on the <a href="/cheatsheet.html">cheat sheet</a>.</p>

<h2>What it runs on</h2>
<p>The website runs entirely in your browser. Your text is never sent to any server. The only network request the page makes is to the GitHub API to show the public star count. There is no account, no tracking and no cookie banner.</p>
<p>The source code is on <a href="__REPO__">GitHub</a> under the MIT license. It also ships as a Claude skill and plugin, ChatGPT and Gemini instruction packs, and ComfyUI nodes.</p>

<h2>Who built it</h2>
<p>SlashFrame is built and maintained by <b>Geevarghese K Thomas</b>, a developer focused on making AI tools more accessible. The project is open source and welcomes contributions on <a href="__REPO__">GitHub</a>.</p>

<h2>Contact</h2>
<div class="card">
<p><b>Bug reports and feature requests</b><br>Open an issue on <a href="__REPO__/issues">GitHub Issues</a>.</p>
<p><b>General questions</b><br>Email: <a href="mailto:geevarghesekthomas84@gmail.com">geevarghesekthomas84@gmail.com</a></p>
<p style="margin:0"><b>Source code</b><br><a href="__REPO__">github.com/geevarghesekthomas84-sys/image-style-skill</a></p>
</div>

<div class="cta"><p><b>Try the free prompt generator.</b> Type an idea, add slash commands, pick your tool and copy the finished prompt.</p><a class="btn" href="/#tool">Open the generator</a></div>
</main>
<footer>__FOOT__<p style="margin:14px 0 0">SlashFrame &middot; MIT license &middot; <a href="__REPO__">GitHub</a></p></footer>
</body></html>"""


def _about_page(today):
    url = SITE_URL + ABOUT_SLUG + "/"
    org = {"@context": "https://schema.org", "@type": "Organization", "name": BRAND, "url": SITE_URL,
           "description": ABOUT_DESC, "email": "geevarghesekthomas84@gmail.com",
           "sameAs": [REPO], "logo": SITE_URL + "social-preview.png"}
    crumbs = _crumb_ld([("Home", SITE_URL), ("About", url)])
    meta = _head_meta(url, ABOUT_TITLE, ABOUT_DESC, [org, crumbs])
    foot = '<div style="margin-bottom:6px">Free prompt generators: ' + " &middot; ".join('<a href="/%s/">%s</a>' % (s, e(n)) for n, s, t in TARGET_INDEX) + "</div>"
    out = ABOUT_HTML
    for k, v in (("__TITLE__", e(ABOUT_TITLE)), ("__META__", meta), ("__FOOT__", foot), ("__REPO__", REPO)):
        out = out.replace(k, v)
    return out


def build(DOCS, ROOT, hosted_html):
    today = datetime.date.today().isoformat()
    urls = []

    # home
    home = _render(hosted_html, SITE_URL, HOME_TITLE, HOME_DESC, HOME_FAQ, ld_extra=[_crumb_ld([("Home", SITE_URL)])], current=None)
    (DOCS / "index.html").write_text(home, encoding="utf-8")
    urls.append((SITE_URL, "weekly", "1.0"))

    # landing page per tool
    for t in TARGETS:
        url = SITE_URL + t["slug"] + "/"
        h1 = '%s<br><em>%s</em>' % (e(t["h1"]), e(t["em"]))
        page = _render(hosted_html, url, t["title"], t["desc"], t["faq"] + HOME_FAQ[1:3],
                       ld_extra=[_crumb_ld([("Home", SITE_URL), (t["name"] + " prompt generator", url)])],
                       target=t["key"], h1=h1, lead=t["lead"], about_html=_about_html(t), current=t["slug"])
        d = DOCS / t["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page, encoding="utf-8")
        urls.append((url, "monthly", "0.9"))

    # guide
    g = DOCS / GUIDE_SLUG
    g.mkdir(parents=True, exist_ok=True)
    (g / "index.html").write_text(_guide_page(today), encoding="utf-8")
    urls.append((SITE_URL + GUIDE_SLUG + "/", "monthly", "0.8"))

    # about / contact
    ab = DOCS / ABOUT_SLUG
    ab.mkdir(parents=True, exist_ok=True)
    (ab / "index.html").write_text(_about_page(today), encoding="utf-8")
    urls.append((SITE_URL + ABOUT_SLUG + "/", "monthly", "0.6"))

    urls.append((SITE_URL + "cheatsheet.html", "monthly", "0.7"))

    shutil.copy(ROOT / ".github" / "social-preview.png", DOCS / "social-preview.png")
    (DOCS / "robots.txt").write_text("User-agent: *\nAllow: /\n\nSitemap: " + SITE_URL + "sitemap.xml\n", encoding="utf-8")
    (DOCS / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join("  <url><loc>%s</loc><lastmod>%s</lastmod><changefreq>%s</changefreq><priority>%s</priority></url>\n" % (u, today, c, p) for u, c, p in urls)
        + "</urlset>\n", encoding="utf-8")
    (DOCS / (INDEXNOW_KEY + ".txt")).write_text(INDEXNOW_KEY, encoding="utf-8")
    (DOCS / "llms.txt").write_text(
        "# SlashFrame\n\n> Free, open-source prompt generator for AI images. Type a short idea plus slash commands (/storm, /85mm, /16:9) and get a finished prompt for Midjourney, Flux, Stable Diffusion, Gemini, DALL-E and ChatGPT, Google Flow and Kling.\n\n"
        "## Generators\n" + "".join("- [%s prompt generator](%s%s/)\n" % (n, SITE_URL, s) for n, s, t in TARGET_INDEX)
        + "\n## Learn\n- [How to write AI image prompts](" + SITE_URL + GUIDE_SLUG + "/)\n- [Command cheat sheet](" + SITE_URL + "cheatsheet.html)\n\n"
        "## Source\n- [GitHub](" + REPO + "): MIT license, Claude plugin, ComfyUI nodes\n", encoding="utf-8")
    return [u for u, c, p in urls]
