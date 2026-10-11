"""Image format conversion plus a small vector tracer. Needs only NumPy and Pillow (both ship with ComfyUI).

The tracer is a posterise-and-trace method: it reduces the picture to a few flat colours and turns each
colour region into SVG paths. That suits logos, icons, flat illustrations and stylised art. It is not a
photo vectoriser: photos come out as a posterised look.
"""
import base64
import io

import numpy as np
from PIL import Image, ImageFilter

RASTER = {
    "png": ("PNG", ".png"),
    "jpg": ("JPEG", ".jpg"),
    "webp": ("WEBP", ".webp"),
    "bmp": ("BMP", ".bmp"),
    "tiff": ("TIFF", ".tiff"),
    "gif": ("GIF", ".gif"),
}
SVG_TRACE = "svg (trace to vector)"
SVG_EMBED = "svg (embed image)"
FORMATS = list(RASTER) + [SVG_TRACE, SVG_EMBED]

_QUANT = getattr(Image, "Quantize", Image)
_DITHER = getattr(Image, "Dither", Image)
_LANCZOS = getattr(getattr(Image, "Resampling", Image), "LANCZOS")
_BICUBIC = getattr(getattr(Image, "Resampling", Image), "BICUBIC")


def extension(fmt):
    return ".svg" if fmt in (SVG_TRACE, SVG_EMBED) else RASTER[fmt][1]


def flatten(img):
    """Any Pillow image to RGB; transparency is composited on white."""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        bg.alpha_composite(rgba)
        return bg.convert("RGB")
    return img.convert("RGB")


def _loops(mask):
    """Closed outlines of a boolean mask: lists of integer (x, y) corner points, clockwise (y down)."""
    h, w = mask.shape
    pad = np.zeros((h + 2, w + 2), bool)
    pad[1:-1, 1:-1] = mask
    c = pad[1:-1, 1:-1]
    edges = {}

    def add(sel, x0, y0, x1, y1):
        ys, xs = np.nonzero(sel)
        for y, x in zip(ys.tolist(), xs.tolist()):
            edges.setdefault((x + x0, y + y0), []).append((x + x1, y + y1))

    add(c & ~pad[:-2, 1:-1], 0, 0, 1, 0)   # top edges
    add(c & ~pad[1:-1, 2:], 1, 0, 1, 1)    # right edges
    add(c & ~pad[2:, 1:-1], 1, 1, 0, 1)    # bottom edges
    add(c & ~pad[1:-1, :-2], 0, 1, 0, 0)   # left edges
    loops = []
    while edges:
        start = next(iter(edges))
        pts = [start]
        cur = start
        while True:
            outs = edges[cur]
            nxt = outs.pop()
            if not outs:
                del edges[cur]
            if nxt == start:
                break
            pts.append(nxt)
            cur = nxt
        loops.append(pts)
    return loops


def _rdp(pts, eps):
    """Ramer-Douglas-Peucker on an open polyline (NumPy array of points)."""
    keep = np.zeros(len(pts), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        i, j = stack.pop()
        if j <= i + 1:
            continue
        seg = pts[j] - pts[i]
        length = float(np.hypot(seg[0], seg[1]))
        v = pts[i + 1:j] - pts[i]
        if length == 0.0:
            dist = np.hypot(v[:, 0], v[:, 1])
        else:
            dist = np.abs(seg[0] * v[:, 1] - seg[1] * v[:, 0]) / length
        k = int(dist.argmax())
        if dist[k] > eps:
            m = i + 1 + k
            keep[m] = True
            stack.append((i, m))
            stack.append((m, j))
    return pts[keep]


def _simplify(loop, eps):
    arr = np.array(loop, dtype=float)
    if len(arr) < 3:
        return arr
    p0, p2 = np.roll(arr, 1, 0), np.roll(arr, -1, 0)
    cross = (arr - p0)[:, 0] * (p2 - arr)[:, 1] - (arr - p0)[:, 1] * (p2 - arr)[:, 0]
    arr = arr[cross != 0]                       # drop points on straight runs
    if len(arr) < 3:
        return arr
    d = np.hypot(arr[:, 0] - arr[0, 0], arr[:, 1] - arr[0, 1])
    j = int(d.argmax())
    a = _rdp(arr[:j + 1], eps)
    b = _rdp(np.vstack([arr[j:], arr[:1]]), eps)
    return np.vstack([a[:-1], b[:-1]])


def _area(poly):
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def trace_svg(img, colors=8, max_size=512, smoothness=1.0, speckle=4):
    """Posterise to `colors` flat colours and return SVG text made of filled paths."""
    rgb = flatten(img)
    w0, h0 = rgb.size
    scale = min(1.0, float(max_size) / max(w0, h0))
    w, h = max(1, int(round(w0 * scale))), max(1, int(round(h0 * scale)))
    small = rgb if (w, h) == (w0, h0) else rgb.resize((w, h), _LANCZOS)
    n = int(colors)
    q = small.quantize(colors=n, method=_QUANT.MEDIANCUT, dither=_DITHER.NONE)
    idx = np.array(q)
    pal = (q.getpalette() or [])[:3 * n]
    pal += [0] * (3 * n - len(pal))
    counts = np.bincount(idx.ravel(), minlength=n)
    order = [int(k) for k in np.argsort(-counts) if counts[k] > 0]
    f = 2 if max(w, h) * 2 <= 2048 else 1          # trace at 2x so edges can be smoothed
    if f > 1:
        maps = np.zeros((n, h * f, w * f), np.uint8)
        for k in order:
            m = Image.fromarray(((idx == k) * 255).astype(np.uint8), "L").resize((w * f, h * f), _BICUBIC)
            maps[k] = np.asarray(m.filter(ImageFilter.GaussianBlur(radius=0.9 * f)))
        label = maps.argmax(axis=0)                  # disjoint regions with rounded edges, no gaps or overlaps
        del maps
    else:
        label = idx
    H, W = label.shape

    def hexcol(k):
        return "#%02x%02x%02x" % tuple(pal[3 * k:3 * k + 3])

    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (w0, h0, W, H),
             '<rect width="%d" height="%d" fill="%s"/>' % (W, H, hexcol(order[0]))]   # biggest colour is the background
    for k in order[1:]:
        d = []
        for loop in _loops(label == k):
            poly = _simplify(loop, float(smoothness) * f * 0.5)
            if len(poly) < 3 or abs(_area(poly)) < speckle * f * f:
                continue
            d.append("M" + "L".join("%d %d" % (int(x), int(y)) for x, y in poly) + "Z")
        if d:
            parts.append('<path fill="%s" fill-rule="evenodd" d="%s"/>' % (hexcol(k), "".join(d)))
    parts.append("</svg>")
    return "\n".join(parts)


def embed_svg(img):
    """An SVG wrapper around the raster picture. It scales cleanly but is NOT vector artwork."""
    rgb = flatten(img)
    buf = io.BytesIO()
    rgb.save(buf, format="PNG")
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    w, h = rgb.size
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
            '<image width="%d" height="%d" href="data:image/png;base64,%s"/></svg>' % (w, h, w, h, w, h, data))


def save_as(img, fmt, path_without_ext, quality=90, svg_colors=8, max_trace_size=512, smoothness=1.0):
    """Save `img` in `fmt`. Returns (file path, svg text or empty string)."""
    if fmt not in FORMATS:
        raise ValueError("Unknown format: %r" % (fmt,))
    path = path_without_ext + extension(fmt)
    if fmt == SVG_TRACE or fmt == SVG_EMBED:
        svg = trace_svg(img, svg_colors, max_trace_size, smoothness) if fmt == SVG_TRACE else embed_svg(img)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        return path, svg
    pil_fmt = RASTER[fmt][0]
    rgb = flatten(img)
    if pil_fmt == "JPEG":
        rgb.save(path, format=pil_fmt, quality=int(quality), optimize=True)
    elif pil_fmt == "WEBP":
        rgb.save(path, format=pil_fmt, quality=int(quality))
    elif pil_fmt == "GIF":
        rgb.quantize(256).save(path, format=pil_fmt)
    else:
        rgb.save(path, format=pil_fmt)
    return path, ""
