"""Tests for the ComfyUI node. Run:  python comfyui/ComfyUI-ImageStyle/tests/test_core.py"""
import importlib.util
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(PKG))

spec = importlib.util.spec_from_file_location("ComfyUI_ImageStyle", os.path.join(PKG, "__init__.py"),
                                              submodule_search_locations=[PKG])
pkg = importlib.util.module_from_spec(spec)
sys.modules["ComfyUI_ImageStyle"] = pkg
spec.loader.exec_module(pkg)
core = sys.modules["ComfyUI_ImageStyle.imagestyle_core"]

with open(os.path.join(HERE, "golden.json"), encoding="utf-8") as f:
    GOLDEN = json.load(f)


class Parity(unittest.TestCase):
    """The Python port must match what the web page itself printed for the same requests."""

    def test_golden_cases(self):
        for g in GOLDEN:
            res = core.expand(g["req"], plain_english=True)
            ctx = "request: %r" % g["req"]
            self.assertEqual(res["keywords"], g["base"], ctx)
            self.assertEqual(res["sentences"], g["sent"].strip(), ctx)
            self.assertEqual([r["r"] for r in res["ratios"]], g["ratios"], ctx)
            self.assertEqual(", ".join(res["negatives"]), g["avoid"], ctx)
            parts = []
            if res["dropped"]:
                parts.append("Dropped: " + ", ".join(res["dropped"]))
            if res["unknown"]:
                parts.append("Unknown: /" + ", /".join(res["unknown"]))
            self.assertEqual("  ·  ".join(parts), g["note"], ctx)

    def test_constants_match_the_web_page(self):
        with open(os.path.join(REPO, "src", "expander.template.html"), encoding="utf-8") as fh:
            html = fh.read()

        def arr(name):
            m = re.search(r"const " + name + r"=(\[.*?\]);", html)
            self.assertTrue(m, name)
            return json.loads(m.group(1))

        self.assertEqual(core.ORDER, arr("ORDER"))
        self.assertEqual(core.GROUPS, arr("GROUPS"))
        self.assertEqual(core.PRIO, arr("PRIO"))
        self.assertEqual(core.NATCATS, arr("NATCATS"))
        self.assertEqual(core.MAX_MODIFIERS, int(re.search(r"const MAX=(\d+);", html).group(1)))


class Behaviour(unittest.TestCase):
    def test_plain_english_off_keeps_subject_words(self):
        res = core.expand("a macro photo of a leaf /hdreal", plain_english=False)
        self.assertEqual(res["subject"], "a macro photo of a leaf")
        self.assertIn("a macro photo of a leaf", res["keywords"])

    def test_negative_is_deduplicated(self):
        res = core.expand("a cat /clean")
        _, neg = core.compose(res, "keywords (SD, SDXL, Pony)")
        terms = [t.strip() for t in neg.split(",")]
        self.assertEqual(len(terms), len(set(terms)))
        self.assertIn("lowres", terms)
        self.assertIn("logo", terms)

    def test_sentences_style_and_folding(self):
        res = core.expand("a cat /clean /storm")
        pos, neg = core.compose(res, "sentences (Flux, SD3, Qwen-Image)")
        self.assertNotIn("Clean image without", pos)
        pos2, _ = core.compose(res, "sentences (Flux, SD3, Qwen-Image)", fold_negatives=True)
        self.assertIn("Clean image without text", pos2)
        self.assertNotIn("lowres", neg)  # base negative is for keyword style only

    def test_sizes(self):
        self.assertEqual(core.scaled_size(1344, 768, 1.0), (1344, 768))
        w, h = core.scaled_size(1344, 768, 2.0)
        self.assertEqual((w % 64, h % 64), (0, 0))
        self.assertAlmostEqual(w * h / 2000000.0, 1.0, delta=0.12)

    def test_report_mentions_everything(self):
        rep = core.build_report(core.expand("a cat /8k /4k /nope /16:9 /clean"))
        for needle in ("/4k", "/8k dropped", "/nope is not a known command", "ratio 16:9 -> 1344x768", "avoid:"):
            self.assertIn(needle, rep)


class Nodes(unittest.TestCase):
    def setUp(self):
        self.A = pkg.NODE_CLASS_MAPPINGS["ImageStylePrompt"]()
        self.B = pkg.NODE_CLASS_MAPPINGS["ImageStylePromptAllRatios"]()
        self.kw = "keywords (SD, SDXL, Pony)"

    def test_registered(self):
        self.assertEqual(set(pkg.NODE_CLASS_MAPPINGS),
                         {"ImageStylePrompt", "ImageStylePromptAllRatios", "ImageStyleUploadConvert"})
        self.assertEqual(set(pkg.NODE_DISPLAY_NAME_MAPPINGS), set(pkg.NODE_CLASS_MAPPINGS))

    def test_input_types_shape(self):
        for cls in pkg.NODE_CLASS_MAPPINGS.values():
            it = cls.INPUT_TYPES()
            self.assertIn("required", it)
            self.assertEqual(len(cls.RETURN_TYPES), len(cls.RETURN_NAMES))
            for _, spec in list(it["required"].items()) + list(it.get("optional", {}).items()):
                self.assertTrue(isinstance(spec, tuple) and len(spec) >= 1)

    def test_single_node_outputs(self):
        pos, neg, w, h, rep = self.A.run("a lighthouse /storm /24mm /16:9 /clean", self.kw, "1:1", 1.0, 0)
        self.assertTrue(pos.startswith("a lighthouse, wide 24mm field of view"))
        self.assertNotIn("lens", pos)  # equipment words make some models draw the lens itself
        self.assertIn("lowres", neg)
        self.assertEqual((w, h), (1344, 768))
        self.assertIn("ratio 16:9", rep)

    def test_default_ratio_used_when_none_given(self):
        _, _, w, h, _ = self.A.run("a cat /storm", self.kw, "9:16", 1.0, 0)
        self.assertEqual((w, h), (768, 1344))

    def test_ratio_pick_and_clamp(self):
        for pick, want in ((0, (1344, 768)), (1, (768, 1344)), (9, (768, 1344))):
            _, _, w, h, rep = self.A.run("a cat /16:9 /9:16", self.kw, "1:1", 1.0, pick)
            self.assertEqual((w, h), want)
        self.assertIn("All Ratios node", rep)

    def test_all_ratios_returns_lists(self):
        out = self.B.run("a cat /goldenhour /16:9 /9:16", self.kw, "1:1", 1.0)
        self.assertEqual(self.B.OUTPUT_IS_LIST, (True, True, True, True, False))
        self.assertEqual(list(zip(out[2], out[3])), [(1344, 768), (768, 1344)])
        self.assertTrue(all(isinstance(x, list) and len(x) == 2 for x in out[:4]))

    def test_all_ratios_without_any_ratio_gives_one_item(self):
        out = self.B.run("a cat", self.kw, "4:5", 1.0)
        self.assertEqual(len(out[0]), 1)

    def test_preset_default_ratio(self):
        _, _, w, h, _ = self.A.run("a mug /productshot", self.kw, "9:16", 1.0, 0)
        self.assertEqual((w, h), (1024, 1024))  # the preset's own 1:1 beats the node's default

    def test_hostile_text_is_just_text(self):
        pos, _, _, _, _ = self.A.run("<script>alert(1)</script> /storm", self.kw, "1:1", 1.0, 0)
        self.assertIn("<script>alert(1)</script>", pos)  # passed through as plain prompt text, never executed


class WebHelper(unittest.TestCase):
    """The browser extension talks to two small routes backed by plain functions."""

    def setUp(self):
        self.nodes = sys.modules["ComfyUI_ImageStyle.nodes"]

    def test_commands_payload(self):
        items = self.nodes.commands_payload()
        names = set(i["n"] for i in items)
        for must in ("storm", "24mm", "16:9", "clean", "productshot", "square"):
            self.assertIn(must, names)
        self.assertNotIn("mj", names)  # target-tool names are ignored by the node, so not suggested
        self.assertTrue(all(set(i) == {"n", "c", "p"} for i in items))

    def test_expand_payload_matches_node(self):
        e = self.nodes.expand_payload({"request": "a cat /storm /16:9 /clean", "style": self.nodes.STYLES[0]})
        self.assertEqual((e["width"], e["height"]), (1344, 768))
        self.assertIn("violent storm", e["positive"])
        self.assertIn("lowres", e["negative"])
        self.assertIn("ratio 16:9", e["report"])

    def test_expand_payload_survives_junk(self):
        for body in (None, "x", 5, {}, {"megapixels": "abc", "ratio_pick": "q", "style": "zzz", "default_ratio": "9:99"},
                     {"request": "a" * 20000}):
            e = self.nodes.expand_payload(body)
            self.assertEqual(set(e), {"positive", "negative", "width", "height", "report"})

    def test_extension_file_is_wired_and_parses(self):
        self.assertEqual(getattr(pkg, "WEB_DIRECTORY", None), "./web")
        js = os.path.join(PKG, "web", "imagestyle.js")
        self.assertTrue(os.path.isfile(js))
        with open(js, encoding="utf-8") as fh:
            src = fh.read()
        self.assertIn('registerExtension', src)
        self.assertNotIn("innerHTML", src)  # preview text is always set as plain text
        import shutil, subprocess, tempfile
        node = shutil.which("node")
        if node:
            tmp = os.path.join(tempfile.mkdtemp(), "imagestyle.mjs")
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(src)
            r = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)



class Convert(unittest.TestCase):
    """The converter and the upload/convert node (no ComfyUI needed)."""

    @classmethod
    def setUpClass(cls):
        from PIL import Image, ImageDraw
        cls.Image = Image
        cls.convert = sys.modules["ComfyUI_ImageStyle.convert"]
        im = Image.new("RGB", (160, 100), (255, 255, 255))
        d = ImageDraw.Draw(im)
        d.ellipse((15, 15, 80, 85), fill=(220, 30, 30))
        d.rectangle((100, 25, 145, 75), fill=(30, 60, 200))
        cls.img = im

    def test_trace_is_valid_svg_with_the_right_colours(self):
        import xml.dom.minidom as md
        svg = self.convert.trace_svg(self.img, colors=4)
        md.parseString(svg)
        self.assertIn('viewBox="0 0', svg)
        self.assertIn('width="160" height="100"', svg)          # keeps the original size
        self.assertNotIn("<script", svg)
        self.assertNotIn("<image", svg)                          # real paths, not an embedded picture
        fills = set(re.findall(r'fill="(#[0-9a-f]{6})"', svg))
        self.assertIn("#ffffff", fills)                          # background
        reds = [f for f in fills if int(f[1:3], 16) > 180 and int(f[3:5], 16) < 80]
        blues = [f for f in fills if int(f[5:7], 16) > 150 and int(f[1:3], 16) < 80]
        self.assertTrue(reds and blues, fills)

    def test_trace_handles_flat_and_tiny_images(self):
        for im in (self.Image.new("RGB", (1, 1), (5, 5, 5)), self.Image.new("RGB", (40, 40), (9, 99, 199)),
                   self.Image.new("RGBA", (30, 20), (255, 0, 0, 0))):
            svg = self.convert.trace_svg(im, colors=8)
            self.assertTrue(svg.startswith("<svg") and svg.endswith("</svg>"))

    def test_embed_svg_wraps_the_picture(self):
        svg = self.convert.embed_svg(self.img)
        self.assertIn("data:image/png;base64,", svg)

    def test_every_format_writes_a_readable_file(self):
        import tempfile
        d = tempfile.mkdtemp()
        for fmt in self.convert.FORMATS:
            path, svg = self.convert.save_as(self.img, fmt, os.path.join(d, "t_" + fmt.split()[0] + fmt[-2:]), 80)
            self.assertTrue(os.path.getsize(path) > 100, fmt)
            if fmt.startswith("svg"):
                self.assertTrue(svg.startswith("<svg") and path.endswith(".svg"))
            else:
                with self.Image.open(path) as back:
                    self.assertEqual(back.size, (160, 100), fmt)

    def test_unknown_format_is_rejected(self):
        with self.assertRaises(ValueError):
            self.convert.save_as(self.img, "exe", "x")

    def test_alpha_is_flattened_on_white(self):
        rgba = self.Image.new("RGBA", (4, 4), (0, 0, 0, 0))
        self.assertEqual(self.convert.flatten(rgba).getpixel((0, 0)), (255, 255, 255))

    def test_node_converts_a_connected_image(self):
        import numpy as np, tempfile, shutil
        mod = sys.modules["ComfyUI_ImageStyle.export_node"]

        class FakeTensor(object):            # stands in for a torch IMAGE tensor
            def __init__(self, a): self.a = a
            def cpu(self): return self
            def numpy(self): return self.a

        arr = np.asarray(self.img, dtype=np.float32)[None, ...] / 255.0
        old = os.getcwd()
        tmp = tempfile.mkdtemp()
        os.chdir(tmp)
        try:
            node = mod.ImageStyleUploadConvert()
            out = node.run("svg (trace to vector)", 90, 6, 512, 1.0, "demo", images=FakeTensor(arr))
            tensor, paths, svg = out["result"]
            self.assertTrue(paths.endswith(".svg") and os.path.isfile(paths))
            self.assertTrue(svg.startswith("<svg"))
            out2 = node.run("png", 90, 6, 512, 1.0, "demo", images=FakeTensor(arr))
            self.assertTrue(out2["result"][1].endswith(".png"))
            self.assertEqual(out2["ui"]["images"][0]["type"], "output")
            self.assertNotEqual(paths, out2["result"][1])
            with self.assertRaises(ValueError):
                node.run("png", 90, 6, 512, 1.0, "demo")        # nothing uploaded, nothing connected
        finally:
            os.chdir(old)
            shutil.rmtree(tmp, ignore_errors=True)


class ExampleWorkflow(unittest.TestCase):
    EXPECT = {"image-style-z-image-turbo.json": 14, "image-style-z-image-turbo-svg.json": 16,
              "image-style-upload-to-svg.json": 3}

    def _load(self, name):
        with open(os.path.join(PKG, "example_workflows", name), encoding="utf-8") as fh:
            return json.load(fh)

    def test_all_example_workflows_are_consistent(self):
        found = sorted(f for f in os.listdir(os.path.join(PKG, "example_workflows")) if f.endswith(".json"))
        self.assertEqual(found, sorted(self.EXPECT))
        for name, nlinks in self.EXPECT.items():
            wf = self._load(name)
            ids = set(n["id"] for n in wf["nodes"])
            self.assertEqual(len(wf["links"]), nlinks, name)
            for l in wf["links"]:
                self.assertIn(l[1], ids, name)
                self.assertIn(l[3], ids, name)

    def test_style_node_values(self):
        wf = self._load("image-style-z-image-turbo.json")
        stylenode = [n for n in wf["nodes"] if n["type"] == "ImageStylePrompt"][0]
        self.assertIn(stylenode["widgets_values"][1], pkg.nodes.STYLES)
        self.assertIn(stylenode["widgets_values"][2], core.ratio_names())

    def test_convert_node_values(self):
        for name in ("image-style-z-image-turbo-svg.json", "image-style-upload-to-svg.json"):
            conv = [n for n in self._load(name)["nodes"] if n["type"] == "ImageStyleUploadConvert"][0]
            self.assertIn(conv["widgets_values"][0], sys.modules["ComfyUI_ImageStyle.convert"].FORMATS)


if __name__ == "__main__":
    unittest.main(verbosity=1)
