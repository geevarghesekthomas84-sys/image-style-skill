"""ComfyUI nodes for image-style (classic node API, works on old and new ComfyUI)."""
from . import imagestyle_core as core

STYLES = ["keywords (SD, SDXL, Pony)", "sentences (Flux, SD3, Qwen-Image)"]
EXAMPLE = "a lone lighthouse on a cliff /storm /dramaticlighting /24mm /16:9"


def _ratio_choices():
    return core.ratio_names()


def _pick_size(res, default_ratio, ratio_pick, megapixels):
    """Choose one ratio from the request (or the default) and return (w, h, label)."""
    if res["ratios"]:
        r = res["ratios"][min(max(int(ratio_pick), 0), len(res["ratios"]) - 1)]
        w, h, label = r["w"], r["h"], r["r"]
    else:
        d = core.tables().asp[core.norm(default_ratio)]
        w, h = [int(x) for x in d["px"].split("x")]
        label = d["r"]
    w, h = core.scaled_size(w, h, float(megapixels))
    return w, h, label


class ImageStylePrompt(object):
    """Type a request with /commands. Get a positive prompt, a negative prompt and a size."""

    CATEGORY = "image-style"
    FUNCTION = "run"
    RETURN_TYPES = ("STRING", "STRING", "INT", "INT", "STRING")
    RETURN_NAMES = ("positive", "negative", "width", "height", "report")
    DESCRIPTION = ("Expands short /commands into a full prompt. Connect positive and negative to your text "
                   "encoders and width/height to Empty Latent Image (convert those widgets to inputs).")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "request": ("STRING", {"multiline": True, "default": EXAMPLE}),
                "style": (STYLES, {"default": STYLES[0]}),
                "default_ratio": (_ratio_choices(), {"default": "1:1"}),
                "megapixels": ("FLOAT", {"default": 1.0, "min": 0.25, "max": 4.0, "step": 0.05}),
                "ratio_pick": ("INT", {"default": 0, "min": 0, "max": 9}),
            },
            "optional": {
                "extra_negative": ("STRING", {"multiline": True, "default": ""}),
                "add_base_negative": ("BOOLEAN", {"default": True}),
                "fold_negatives_into_prompt": ("BOOLEAN", {"default": False}),
                "plain_english": ("BOOLEAN", {"default": False}),
            },
        }

    def run(self, request, style, default_ratio, megapixels, ratio_pick,
            extra_negative="", add_base_negative=True, fold_negatives_into_prompt=False, plain_english=False):
        res = core.expand(request, plain_english=plain_english)
        positive, negative = core.compose(res, style, add_base_negative, extra_negative, fold_negatives_into_prompt)
        w, h, label = _pick_size(res, default_ratio, ratio_pick, megapixels)
        report = core.build_report(res)
        if len(res["ratios"]) > 1:
            report += "\n(request has %d ratios; using #%d: %s. Use the All Ratios node to run each.)" % (
                len(res["ratios"]), min(int(ratio_pick), len(res["ratios"]) - 1), label)
        return (positive, negative, w, h, report)


class ImageStylePromptAllRatios(object):
    """Same as Image Style Prompt, but outputs one item per ratio so the workflow runs once for each."""

    CATEGORY = "image-style"
    FUNCTION = "run"
    RETURN_TYPES = ("STRING", "STRING", "INT", "INT", "STRING")
    RETURN_NAMES = ("positive", "negative", "width", "height", "report")
    OUTPUT_IS_LIST = (True, True, True, True, False)
    DESCRIPTION = "Ask for /16:9 /9:16 together and the downstream nodes run once per ratio."

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "request": ("STRING", {"multiline": True, "default": EXAMPLE + " /9:16"}),
                "style": (STYLES, {"default": STYLES[0]}),
                "default_ratio": (_ratio_choices(), {"default": "1:1"}),
                "megapixels": ("FLOAT", {"default": 1.0, "min": 0.25, "max": 4.0, "step": 0.05}),
            },
            "optional": {
                "extra_negative": ("STRING", {"multiline": True, "default": ""}),
                "add_base_negative": ("BOOLEAN", {"default": True}),
                "fold_negatives_into_prompt": ("BOOLEAN", {"default": False}),
                "plain_english": ("BOOLEAN", {"default": False}),
            },
        }

    def run(self, request, style, default_ratio, megapixels,
            extra_negative="", add_base_negative=True, fold_negatives_into_prompt=False, plain_english=False):
        res = core.expand(request, plain_english=plain_english)
        positive, negative = core.compose(res, style, add_base_negative, extra_negative, fold_negatives_into_prompt)
        count = max(1, len(res["ratios"]))
        ps, ns, ws, hs = [], [], [], []
        for i in range(count):
            w, h, _ = _pick_size(res, default_ratio, i, megapixels)
            ps.append(positive)
            ns.append(negative)
            ws.append(w)
            hs.append(h)
        return (ps, ns, ws, hs, core.build_report(res))


NODE_CLASS_MAPPINGS = {
    "ImageStylePrompt": ImageStylePrompt,
    "ImageStylePromptAllRatios": ImageStylePromptAllRatios,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageStylePrompt": "Image Style Prompt",
    "ImageStylePromptAllRatios": "Image Style Prompt (all ratios)",
}


# ---- small helper API used by web/imagestyle.js (autocomplete + live preview) ----
def commands_payload():
    """All command names the request box understands, for autocomplete."""
    d = core.load_data()
    items = []
    for name, v in d["mods"].items():
        items.append({"n": name, "c": v["category"], "p": v["phrase"]})
    for name, r, px, note in d["aspect"]:
        items.append({"n": name, "c": "ratio", "p": "%s (%s)" % (r, px)})
    for name, terms in d["negatives"]:
        items.append({"n": name, "c": "avoid", "p": "avoid: " + terms})
    for name, label, toks, ar in d["presets"]:
        items.append({"n": name, "c": "preset", "p": "%s = %s (ratio %s)" % (label, toks, ar)})
    items.sort(key=lambda x: x["n"])
    return items


def expand_payload(body):
    """Run the node logic on plain JSON input; returns a JSON-safe dict."""
    body = body if isinstance(body, dict) else {}
    request = str(body.get("request", ""))[:4000]
    style = body.get("style") if body.get("style") in STYLES else STYLES[0]
    ratio = body.get("default_ratio") if body.get("default_ratio") in _ratio_choices() else "1:1"
    try:
        mp = min(4.0, max(0.25, float(body.get("megapixels", 1.0))))
    except (TypeError, ValueError):
        mp = 1.0
    try:
        pick = min(9, max(0, int(body.get("ratio_pick", 0))))
    except (TypeError, ValueError):
        pick = 0
    pos, neg, w, h, rep = ImageStylePrompt().run(
        request, style, ratio, mp, pick,
        extra_negative=str(body.get("extra_negative", ""))[:1000],
        add_base_negative=bool(body.get("add_base_negative", True)),
        fold_negatives_into_prompt=bool(body.get("fold_negatives_into_prompt", False)),
        plain_english=bool(body.get("plain_english", False)))
    return {"positive": pos, "negative": neg, "width": w, "height": h, "report": rep}


def _register_routes():
    try:  # only inside ComfyUI; plain imports (tests) skip this quietly
        from aiohttp import web
        from server import PromptServer
        routes = PromptServer.instance.routes
    except Exception:
        return

    @routes.get("/imagestyle/commands")
    async def _commands(request):
        return web.json_response(commands_payload())

    @routes.post("/imagestyle/expand")
    async def _expand(request):
        try:
            body = await request.json()
        except Exception:
            body = {}
        return web.json_response(expand_payload(body))


_register_routes()
