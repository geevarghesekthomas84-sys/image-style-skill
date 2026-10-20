"""Pure-Python port of the image-style expander (no ComfyUI or torch imports).

It follows the same rules as the web page (src/expander.template.html): commands are looked up,
conflicts resolved (last one wins), at most 8 style modifiers kept, plain-English words and ratios
recognised, presets expanded. tests/test_core.py compares it to the web page's own output.
"""
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

_RE_PREAMBLE = re.compile(r"^(please\s+)?(create|make|generate|draw|design|give|show)\s+(me\s+)?(an?\s+|the\s+)?", re.I)
_RE_SIZE_WORDS = re.compile(r"\b(size|sizes|ratio|ratios|frame|frames|aspect|both)\b", re.I)
_RE_DUP_PREP = re.compile(r"\b(and|in|with|of|at|for)\b(?=\s+(and|in|with|of|at|for)\b)", re.I)
_RE_TRAIL_PREP = re.compile(r"(\s|,)+(and|in|with|of|at|for)\s*$", re.I)
_RE_LEAD_PREP = re.compile(r"^(and|in|with|of|at|for)\s+", re.I)
_RE_MULTI_SPACE = re.compile(r"\s+")
_RE_TRAIL_COMMA = re.compile(r"[,\s]+$")

# These constants mirror the ones in src/expander.template.html (a test checks they stay equal).
ORDER = ["subject", "couple", "angle", "camera", "motion", "composition", "lens", "film", "genre", "portrait", "macro",
         "scene", "landscape", "architecture", "space", "weather", "light", "era", "style", "art", "render", "material",
         "technique", "effect", "color", "quality", "reference"]
GROUPS = [["age20s", "age30s", "age40s", "age50s", "elderly"],
          ["smile", "serious", "laughing", "thoughtful", "surprised", "calm"],
          ["standing", "sitting", "walking", "running", "leaning"],
          ["lookingatcamera", "lookingaway"], ["longhair", "shorthair"],
          ["hdreal", "4k", "8k", "8ktextures"], ["photorealistic", "hyperrealistic", "ultrarealistic", "rawphoto"],
          ["14mm", "24mm", "35mm", "50mm", "85mm", "135mm", "200mm"], ["f1.4", "f2.8", "f8"],
          ["highkeylighting", "lowkeylighting"], ["warmtones", "cooltones"],
          ["blackandwhite", "vibrantcolors", "pastelcolors", "monochrome", "duotone"],
          ["overexposed", "underexposed"], ["highcontrast", "lowcontrast"]]
PRIO = ["genre", "subject", "couple", "reference", "style", "scene", "portrait", "macro", "angle", "camera", "lens",
        "light", "weather", "landscape", "architecture", "space", "film", "art", "render", "material", "technique",
        "effect", "motion", "color", "era", "composition", "quality"]
NATCATS = ["camera", "motion", "quality", "angle", "lens", "film", "light", "color", "technique", "composition", "art",
           "render", "material", "effect", "genre", "era", "style", "portrait", "macro"]
MAX_MODIFIERS = 8
BASE_NEGATIVE = "lowres, blurry, bad anatomy, watermark"

_data = None


def load_data(path=None):
    global _data
    if path is None and _data is not None:
        return _data
    p = path or os.path.join(HERE, "data", "imagestyle.json")
    with open(p, encoding="utf-8") as f:
        d = json.load(f)
    if path is None:
        _data = d
    return d


def norm(s):
    return re.sub(r"[\s_-]+", "", s.lower())


class _Tables(object):
    def __init__(self, d):
        self.mods = d["mods"]
        self.aspect_rows = d["aspect"]
        self.negs = dict((n, t) for n, t in d["negatives"])
        self.models = set(m[0] for m in d["models"])
        self.pre = dict((n, {"t": t, "a": a}) for n, l, t, a in d["presets"])
        self.asp = {}
        for n, r, px, note in d["aspect"]:
            v = {"r": r, "px": px}
            self.asp[norm(n)] = v
            self.asp[norm(r)] = v
            self.asp[norm(r.replace(":", "x"))] = v
            m = re.search(r"aliases?:\s*(.*)$", note)
            if m:
                for a in re.split(r"\s+", m.group(1)):
                    if a:
                        self.asp[norm(a)] = v
        self.nat = set(k for k, v in self.mods.items() if v["category"] in NATCATS)


_tables = {}


def tables(d=None):
    d = d or load_data()
    key = id(d)
    if key not in _tables:
        _tables[key] = _Tables(d)
    return _tables[key]


def ratio_names(d=None):
    """Ratios offered in the ComfyUI dropdown, e.g. ['1:1', '4:3', ...]."""
    return [r[1] for r in (d or load_data())["aspect"]]


def _natural(text, sel, ars, T):
    t = " " + text + " "

    def ratio(m):
        v = T.asp.get(m.group(1) + ":" + m.group(2))
        if not v:
            return m.group(0)
        if v not in ars:
            ars.append(v)
        return " "

    t = re.sub(r"(\d{1,2})\s*[:xX]\s*(\d{1,2})(?!\d)", ratio, t)
    w = [x for x in re.split(r"\s+", t.strip()) if x]
    keep = []
    i = 0
    while i < len(w):
        hit = 0
        n = 4
        while n >= 1 and not hit:
            if i + n <= len(w):
                k = norm(re.sub(r"[^\w]", "", "".join(w[i:i + n]), flags=re.ASCII))
                if k in T.nat:
                    if k not in sel:
                        sel.append(k)
                    hit = n
            n -= 1
        if hit:
            i += hit
        else:
            keep.append(w[i])
            i += 1
    s = " ".join(keep)
    s = _RE_PREAMBLE.sub("", s)
    s = _RE_SIZE_WORDS.sub(" ", s)
    s = _RE_DUP_PREP.sub(" ", s)
    s = _RE_TRAIL_PREP.sub("", s)
    s = _RE_LEAD_PREP.sub("", s)
    s = _RE_MULTI_SPACE.sub(" ", s)
    s = _RE_TRAIL_COMMA.sub("", s)
    return s.strip()


def expand(request, data=None, plain_english=True):
    """Expand a request with /commands. Returns a dict (see keys below).

    plain_english=True also recognises style words and ratios written without slashes (the web page does this).
    """
    d = data or load_data()
    T = tables(d)
    mods = T.mods
    text = request or ""
    preset_ar = [None]

    def preset(m):
        P = T.pre.get(norm(m.group(2)))
        if not P:
            return m.group(0)
        if P["a"]:
            preset_ar[0] = T.asp.get(norm(P["a"]))
        return m.group(1) + " ".join("/" + x for x in P["t"].split(" "))

    text = re.sub(r"(^|\s)/([^\s/]+)", preset, text)

    dropped, unknown, ars, sel, neg = [], [], [], [], []
    model = [None]

    def tok(m):
        sp, raw = m.group(1), m.group(2)
        k = norm(raw)
        if k == "freeezeaction":
            k = "freezeaction"
        if k in T.models:
            model[0] = k
            return sp
        if k in T.asp:
            if T.asp[k] not in ars:
                ars.append(T.asp[k])
            return sp
        if k in T.negs:
            for x in T.negs[k].split(", "):
                if x not in neg:
                    neg.append(x)
            return sp
        if k in mods:
            sel.append(k)
            return sp
        unknown.append(raw)
        return sp + "/" + raw

    subject = re.sub(r"\s+", " ", re.sub(r"(^|\s)/([^\s/]+)", tok, text)).strip()
    if plain_english:
        subject = _natural(subject, sel, ars, T)
    if not ars and preset_ar[0]:
        ars.append(preset_ar[0])

    seen = []
    for k in sel:
        if k not in seen:
            seen.append(k)
    sel = seen
    for g in GROUPS:
        hit = [k for k in sel if k in g]
        for k in hit[:-1]:
            dropped.append(k)
            sel = [x for x in sel if x != k]

    def capped():
        return [k for k in sel if mods[k]["category"] != "reference"]

    over = []
    while len(capped()) > MAX_MODIFIERS:
        c = capped()
        w = c[0]
        for y in c[1:]:
            if _idx(PRIO, mods[y]["category"]) > _idx(PRIO, mods[w]["category"]):
                w = y
        over.append(w)
        sel = [x for x in sel if x != w]
    dropped.extend(x + " (over 8 limit)" for x in over)
    sel = sorted(sel, key=lambda k: _idx(ORDER, mods[k]["category"]))

    phrases = [mods[k]["phrase"] for k in sel]
    s = subject or "[your subject]"
    keywords = ", ".join([s] + phrases)
    sentences = " ".join([re.sub(r"[.]$", "", s) + "."] + [p[0].upper() + p[1:] + "." for p in phrases])

    ratios = []
    for a in ars:
        w, h = [int(x) for x in a["px"].split("x")]
        ratios.append({"r": a["r"], "px": a["px"], "w": w, "h": h})

    return {
        "subject": subject,
        "keywords": keywords,
        "sentences": sentences,
        "negatives": neg,
        "ratios": ratios,
        "used": sel,
        "phrases": dict((k, mods[k]["phrase"]) for k in sel),
        "dropped": dropped,
        "unknown": unknown,
        "target": model[0],
    }


def _idx(lst, v):
    return lst.index(v) if v in lst else -1


def scaled_size(w, h, megapixels):
    """Scale a table size to the requested megapixels (multiples of 64). 1.0 keeps the table size."""
    if abs(megapixels - 1.0) < 0.005:
        return w, h
    s = math.sqrt(megapixels * 1000000.0 / float(w * h))
    return max(64, int(round(w * s / 64.0)) * 64), max(64, int(round(h * s / 64.0)) * 64)


def build_report(res):
    lines = []
    for k in res["used"]:
        lines.append("+ /%s: %s" % (k, res["phrases"][k]))
    for k in res["dropped"]:
        name = k.split(" ")[0]
        why = "over the 8-modifier limit" if "over" in k else "conflicts with a later command"
        lines.append("- /%s dropped: %s" % (name, why))
    for u in res["unknown"]:
        lines.append("? /%s is not a known command (kept as text)" % u)
    for r in res["ratios"]:
        lines.append("ratio %s -> %s" % (r["r"], r["px"]))
    if res["negatives"]:
        lines.append("avoid: " + ", ".join(res["negatives"]))
    return "\n".join(lines) if lines else "No commands found. Type a request with /commands."


def compose(res, style="keywords", add_base_negative=True, extra_negative="", fold_negatives=False):
    """Positive and negative prompt strings for ComfyUI."""
    if style.startswith("sentences"):
        positive = res["sentences"]
        negs = list(res["negatives"])
        if fold_negatives and negs:
            positive += " Clean image without " + ", ".join(negs) + "."
    else:
        positive = res["keywords"]
        negs = ([BASE_NEGATIVE] if add_base_negative else []) + list(res["negatives"])
    if extra_negative and extra_negative.strip():
        negs.append(extra_negative.strip())
    seen, out = set(), []
    for chunk in negs:
        for term in chunk.split(","):
            t = term.strip()
            if t and t.lower() not in seen:
                seen.add(t.lower())
                out.append(t)
    return positive, ", ".join(out)
