"""Scripted end-to-end tests: send real requests to Claude with the image-style skill installed.

Needs: `claude` CLI signed in, and the skill or plugin installed (see README).
Run:   python run_claude_tests.py            (all cases)
       python run_claude_tests.py 2 4        (only cases 2 and 4)
Each case checks the reply for required and forbidden text (case-insensitive). Replies vary a little
between runs, so a failure means "look at the printed reply", not always "broken".
"""
import subprocess
import sys

PRE = "Use the image-style skill. Do not generate an image. Output only the final prompt(s). Request: "

CASES = [
    ("slash commands + Midjourney, two ratios, last resolution wins",
     PRE + "a lone lighthouse /storm /dramaticlighting /85mm /8k /4k /16:9 /9:16 /clean /mj",
     ["--ar 16:9", "--ar 9:16", "--no", "storm", "85mm", "4k"], ["8k resolution"]),
    ("plain English, Kling, two ratios",
     PRE + "Create me a cinematic album double exposure and Size 16:9 ratio frame both 9:16. Target kling.",
     ["double exposure", "16:9", "9:16", "cinematic"], ["ratio frame", "create me"]),
    ("preset + Flux size",
     PRE + "a ceramic mug /productshot /flux",
     ["85mm", "1024x1024"], []),
    ("cap at 8 modifiers is reported",
     PRE + "a girl /portrait /85mm /f1.4 /bokeh /goldenhour /filmgrain /vintage /cinematic /fog /rimlight /backlight /softlighting",
     ["drop"], []),
    ("unknown command is reported, not invented",
     PRE + "a cat /notacommand /8k",
     ["notacommand"], []),
    ("conflict: last of high-key / low-key wins",
     PRE + "a room /highkeylighting /lowkeylighting",
     ["low-key"], []),
    ("subject controls and reference flags (Midjourney)",
     PRE + "a woman at a cafe /age30s /smile /sitting /sameface /samestyle /mj",
     ["thirties", "--cref", "--sref"], []),
    ("motion command ignored for a still image",
     PRE + "a car on a road /orbit /cinematic /generic",
     ["cinematic"], []),
]


def run(prompt):
    r = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True, timeout=240, cwd=None)
    return (r.stdout or "") + (r.stderr or "")


def main():
    pick = {int(a) for a in sys.argv[1:] if a.isdigit()}
    bad = 0
    for i, (name, prompt, need, forbid) in enumerate(CASES, 1):
        if pick and i not in pick:
            continue
        try:
            out = run(prompt)
        except subprocess.TimeoutExpired:
            print(f"[{i}] TIMEOUT  {name}")
            bad += 1
            continue
        low = out.lower()
        miss = [n for n in need if n.lower() not in low]
        hit = [f for f in forbid if f.lower() in low]
        if "failed to authenticate" in low:
            print("Not signed in: run `claude` once and log in, then re-run.")
            return 2
        ok = not miss and not hit
        print(f"[{i}] {'PASS' if ok else 'FAIL'}  {name}")
        if not ok:
            bad += 1
            print("     missing:", miss, " forbidden present:", hit)
            print("     reply:", out.strip().replace("\n", "\n            ")[:900])
    print(f"\n{bad} case(s) need a look")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
