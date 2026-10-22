"""Local image helper for expander.html. Keeps your API key out of the web page.

Run:   python imagegen.py
Keys:  set OPENAI_API_KEY and/or GEMINI_API_KEY in your environment (never in the page).
Then open http://127.0.0.1:8787/app (the helper serves the page) and click "Generate image".
The page also works opened as a file, but some browsers block file pages from calling localhost.

Optional env: OPENAI_IMAGE_MODEL (default gpt-image-2), GEMINI_IMAGE_MODEL (default gemini-3.1-flash-image),
OPENAI_BASE, GEMINI_BASE, IMAGEGEN_PORT. Model names change often: override them if a provider rejects one.
Listens on 127.0.0.1 only. Costs are billed to your provider account.
"""
import base64
import json
import os
import pathlib
import re
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

PORT = int(os.environ.get("IMAGEGEN_PORT", "8787"))
OPENAI_BASE = os.environ.get("OPENAI_BASE", "https://api.openai.com")
GEMINI_BASE = os.environ.get("GEMINI_BASE", "https://generativelanguage.googleapis.com")
OPENAI_MODEL = os.environ.get("OPENAI_IMAGE_MODEL", "gpt-image-2")
GEMINI_MODEL = os.environ.get("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image")

SIZES = {"1:1": "1024x1024", "4:3": "1152x896", "3:2": "1216x832", "16:9": "1344x768", "21:9": "1536x640",
         "9:16": "768x1344", "2:3": "832x1216", "3:4": "896x1152", "4:5": "896x1120", "3:1": "1728x576"}
FIXED = {"wide": "1536x1024", "tall": "1024x1536", "square": "1024x1024"}  # older gpt-image-1 sizes
GEMINI_RATIOS = {"1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"}
B64 = re.compile(r"^[A-Za-z0-9+/=\s]{200,}$")


def post(url, body, headers):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{e.code} from provider: {e.read().decode(errors='replace')[:300]}")


def find_b64(node):
    """Return the first long base64 string found under keys like data/b64_json/bytesBase64Encoded."""
    if isinstance(node, dict):
        for k, v in node.items():
            if k in ("data", "b64_json", "bytesBase64Encoded") and isinstance(v, str) and B64.match(v):
                return v
        for v in node.values():
            r = find_b64(v)
            if r:
                return r
    elif isinstance(node, list):
        for v in node:
            r = find_b64(v)
            if r:
                return r
    return None


def openai(prompt, ratio):
    size = SIZES.get(ratio, "1024x1024")
    if OPENAI_MODEL != "gpt-image-2":  # older models only take fixed sizes
        w, h = map(int, size.split("x"))
        size = FIXED["square" if w == h else "wide" if w > h else "tall"]
    out = post(OPENAI_BASE + "/v1/images/generations", {"model": OPENAI_MODEL, "prompt": prompt, "size": size, "n": 1},
               {"Authorization": "Bearer " + os.environ["OPENAI_API_KEY"]})
    return find_b64(out)


def gemini(prompt, ratio):
    fmt = {"type": "image", "mime_type": "image/png"}
    if ratio in GEMINI_RATIOS:
        fmt["aspect_ratio"] = ratio
    out = post(GEMINI_BASE + "/v1beta/interactions", {"model": GEMINI_MODEL, "input": prompt, "response_format": fmt},
               {"x-goog-api-key": os.environ["GEMINI_API_KEY"]})
    return find_b64(out)


def pick(requested):
    have = [p for p, k in (("openai", "OPENAI_API_KEY"), ("gemini", "GEMINI_API_KEY")) if os.environ.get(k)]
    if requested in have:
        return requested
    return have[0] if have else None


class H(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        origin = self.headers.get("Origin")
        allowed_origins = {f"http://127.0.0.1:{PORT}", f"http://localhost:{PORT}", "null"}
        if origin in allowed_origins:
            self.send_header("Access-Control-Allow-Origin", origin)
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self._send(204, {})

    def do_GET(self):
        if self.path.startswith("/app"):  # serve the page from here: same origin, no browser blocking
            here = pathlib.Path(__file__).parent
            for f in (here / "expander.html", here / "dist/platforms/flow-kling-anywhere/expander.html"):
                if f.exists():
                    data = f.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    return self.wfile.write(data)
            return self._send(404, {"error": "expander.html not found next to imagegen.py"})
        self._send(200, {"ok": True, "providers": [p for p, k in (("openai", "OPENAI_API_KEY"), ("gemini", "GEMINI_API_KEY")) if os.environ.get(k)]})

    def do_POST(self):
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            prompt = str(body.get("prompt", "")).strip()[:4000]
            if not prompt:
                return self._send(400, {"error": "empty prompt"})
            provider = pick(body.get("provider"))
            if not provider:
                return self._send(400, {"error": "Set OPENAI_API_KEY or GEMINI_API_KEY, then restart imagegen.py"})
            b64 = (openai if provider == "openai" else gemini)(prompt, body.get("ratio", "1:1"))
            if not b64:
                return self._send(502, {"error": "provider replied without an image (model name or API may have changed)"})
            mime = "image/jpeg" if base64.b64decode(b64[:16] + "=" * (-len(b64[:16]) % 4))[:2] == b"\xff\xd8" else "image/png"
            self._send(200, {"image": f"data:{mime};base64,{b64.strip()}", "provider": provider})
        except Exception as e:  # report to the page instead of dying
            self._send(500, {"error": str(e)})

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print(f"imagegen listening on http://127.0.0.1:{PORT}  (Ctrl+C to stop)")
    HTTPServer(("127.0.0.1", PORT), H).serve_forever()
