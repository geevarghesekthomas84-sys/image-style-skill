"""Generate docs/demo.svg: an animated typing demo (pure SVG + CSS, no scripts, plays inside a GitHub README)."""
import pathlib

OUT = pathlib.Path(__file__).parent / "docs" / "demo.svg"

REQUEST = "a lighthouse on a cliff /storm /dramaticlighting /24mm /16:9 /mj"
LINES = [
    "a lighthouse on a cliff, 24mm wide lens, environmental context with natural",
    "perspective, violent storm, dark roiling clouds, lightning, wind, dramatic",
    "lighting, strong contrast between light and shadow --ar 16:9",
]
CW_REQ = 12.0   # px per char for the typed line (font-size 20), forced with textLength
CW_OUT = 10.8   # px per char for the output (font-size 18)
X0 = 74         # left edge of text
CYCLE = 16      # seconds

n_req = len(REQUEST)
req_w = n_req * CW_REQ


def spans(text):
    """Colour the /commands pink, the rest white."""
    out = []
    for i, tok in enumerate(text.split(" ")):
        sep = " " if i else ""
        cls = "cmd" if tok.startswith("/") else "txt"
        out.append(f'<tspan class="{cls}">{sep}{tok}</tspan>')
    return "".join(out)


def out_line(i, text, y):
    w = len(text) * CW_OUT
    flag = text.find("--ar")
    if flag >= 0:
        body = f'<tspan class="out">{text[:flag]}</tspan><tspan class="flag">{text[flag:]}</tspan>'
    else:
        body = f'<tspan class="out">{text}</tspan>'
    return (f'<text class="line l{i}" x="{X0}" y="{y}" font-size="18" textLength="{w:.1f}" '
            f'lengthAdjust="spacing">{body}</text>')


lines_svg = "\n  ".join(out_line(i + 1, t, 196 + i * 30) for i, t in enumerate(LINES))

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="330" viewBox="0 0 1100 330" role="img" aria-label="Animated demo: typing a request with slash commands and getting a finished Midjourney prompt">
<style>
  .bg{{fill:#14121f}} .bar{{fill:#1f1b33}}
  text{{font-family:Consolas,Menlo,"DejaVu Sans Mono",monospace}}
  .title{{font-family:"Segoe UI",Helvetica,Arial,sans-serif;font-size:15px;fill:#9d96c9}}
  .prompt{{fill:#8a80c9;font-size:20px}}
  .txt{{fill:#e9e5ff}} .cmd{{fill:#ff9ee6}} .out{{fill:#cfeee6}} .flag{{fill:#ffd479}}
  .badge{{fill:#1f8f7a}} .badgetxt{{font-family:"Segoe UI",Helvetica,Arial,sans-serif;font-size:14px;font-weight:700;fill:#fff}}
  .hint,.foot{{font-family:"Segoe UI",Helvetica,Arial,sans-serif;font-size:14px;fill:#8a80c9}}

  /* typing reveal, one master timeline of {CYCLE}s that loops */
  #reveal{{animation:type {CYCLE}s infinite}}
  .caret{{animation:caret {CYCLE}s infinite}}
  .badge,.badgetxt{{animation:fadein {CYCLE}s infinite}}
  .hint{{animation:fadein {CYCLE}s infinite}}
  .l1{{animation:l1 {CYCLE}s infinite}} .l2{{animation:l2 {CYCLE}s infinite}} .l3{{animation:l3 {CYCLE}s infinite}}
  .win{{animation:win {CYCLE}s infinite}}

  @keyframes type{{0%,4%{{width:0}}4%{{animation-timing-function:steps({n_req},end)}}23%,100%{{width:{req_w:.0f}px}}}}
  @keyframes caret{{0%,3%{{opacity:1}}3.5%{{opacity:0}}4%{{opacity:1}}23%{{opacity:1}}24%{{opacity:0}}25%{{opacity:1}}26%{{opacity:0}}27%,100%{{opacity:0}}}}
  @keyframes fadein{{0%,26%{{opacity:0}}30%,90%{{opacity:1}}96%,100%{{opacity:0}}}}
  @keyframes l1{{0%,27%{{opacity:0;transform:translateY(6px)}}31%,90%{{opacity:1;transform:none}}96%,100%{{opacity:0}}}}
  @keyframes l2{{0%,32%{{opacity:0;transform:translateY(6px)}}36%,90%{{opacity:1;transform:none}}96%,100%{{opacity:0}}}}
  @keyframes l3{{0%,37%{{opacity:0;transform:translateY(6px)}}41%,90%{{opacity:1;transform:none}}96%,100%{{opacity:0}}}}
  @keyframes win{{0%{{opacity:1}}100%{{opacity:1}}}}

  @media (prefers-reduced-motion: reduce){{
    #reveal,.caret,.badge,.badgetxt,.hint,.l1,.l2,.l3{{animation:none !important}}
    .caret{{opacity:0}}
  }}
</style>
<defs>
  <clipPath id="clip"><rect id="reveal" x="{X0}" y="62" width="{req_w:.0f}" height="40"/></clipPath>
</defs>

<rect class="bg" width="1100" height="330" rx="16"/>
<rect class="bar" width="1100" height="40" rx="16"/><rect class="bar" y="20" width="1100" height="20"/>
<circle cx="26" cy="20" r="6" fill="#ff6b6b"/><circle cx="48" cy="20" r="6" fill="#ffd166"/><circle cx="70" cy="20" r="6" fill="#4cd3a0"/>
<text class="title" x="550" y="25" text-anchor="middle" style="font-family:'Segoe UI',Helvetica,Arial,sans-serif">image-style</text>

<text class="prompt" x="40" y="90">&gt;</text>
<g clip-path="url(#clip)">
  <text x="{X0}" y="90" font-size="20" textLength="{req_w:.1f}" lengthAdjust="spacing">{spans(REQUEST)}</text>
</g>
<rect class="caret" x="{X0 + req_w + 3:.0f}" y="72" width="10" height="22" fill="#e9e5ff"/>

<rect class="badge" x="{X0}" y="128" width="104" height="26" rx="13"/>
<text class="badgetxt" x="{X0 + 52}" y="146" text-anchor="middle">Midjourney</text>
<text class="hint" x="{X0 + 120}" y="146">3 styles expanded, ratio and target applied</text>

{lines_svg}

<text class="foot" x="{X0}" y="304">Swap /mj for /kling, /flux, /sd, /dalle or /gemini to get the same request in that tool's format.</text>
</svg>
'''

OUT.write_text(svg, encoding="utf-8")
print("wrote", OUT, f"({OUT.stat().st_size} bytes)", "| typed chars:", n_req, "| output line lengths:", [len(t) for t in LINES])
