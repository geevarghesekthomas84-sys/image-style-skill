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
