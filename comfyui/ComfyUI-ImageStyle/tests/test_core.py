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
        self.assertEqual(set(pkg.NODE_CLASS_MAPPINGS), {"ImageStylePrompt", "ImageStylePromptAllRatios"})
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
        self.assertTrue(pos.startswith("a lighthouse, 24mm wide lens"))
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


if __name__ == "__main__":
    unittest.main(verbosity=1)
