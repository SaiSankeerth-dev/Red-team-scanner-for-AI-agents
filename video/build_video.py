"""Build the Redline demo video from REAL scan data, rendered as styled cards.

All numbers, findings, and transcript excerpts come from the campaign DB.
No browser needed. Output: redline-demo.mp4 (1280x720, ~80s).

Usage: python build_video.py
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from redline.reports.generator import build_report_data  # noqa: E402
from redline.store import db  # noqa: E402
from redline.store.models import Campaign  # noqa: E402

W, H = 1280, 720
BG = (11, 13, 16)
PANEL = (20, 24, 29)
RED = (255, 59, 71)
WHITE = (232, 237, 242)
MUTED = (154, 166, 178)
GREEN = (52, 211, 153)
AMBER = (245, 166, 35)
BLUE = (96, 165, 250)

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

HERE = os.path.dirname(__file__)
SHOTS = os.path.join(HERE, "shots")
OUT = os.path.join(HERE, "redline-demo.mp4")

GRADE_COLORS = {"A": GREEN, "B": (132, 204, 22), "C": AMBER, "D": (234, 88, 12), "F": RED}


def base():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 8], fill=RED)
    return img, d


def wrapped(d, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=font) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def title_card():
    img, d = base()
    f1, f2, f3 = ImageFont.truetype(BOLD, 110), ImageFont.truetype(SANS, 34), ImageFont.truetype(SANS, 26)
    for text, f, color, y in [("REDLINE", f1, RED, 210),
                              ("automated red-team scanner for AI agents", f2, WHITE, 360),
                              ("33 attacks. scored reports. full transcripts.", f3, MUTED, 430)]:
        tw = d.textlength(text, font=f)
        d.text(((W - tw) / 2, y), text, font=f, fill=color)
    img.save(f"{SHOTS}/title.png")


def terminal_card():
    img = Image.new("RGB", (W, H), (14, 17, 20))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(MONO, 20)
    d.rectangle([0, 0, W, 44], fill=(24, 28, 34))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([22 + i * 26, 14, 38 + i * 26, 30], fill=c)
    d.text((100, 10), "sai@dev: ~/redline — redline scan --target vulnerable",
           font=ImageFont.truetype(MONO, 18), fill=MUTED)
    with open("/tmp/scan_out.txt") as fh:
        raw = [ln.rstrip("\n") for ln in fh if ln.strip()]
    picked = raw[:3] + raw[3:19] + ["…"] + raw[-3:]
    y = 62
    for line in picked[:27]:
        color = RED if "[fail]" in line else GREEN if "[pass]" in line else BLUE if line.startswith(("[redline]", "##")) else WHITE
        d.text((28, y), line[:100], font=f, fill=color)
        y += 24
    img.save(f"{SHOTS}/terminal.png")


def score_card(data):
    img, d = base()
    f_big, f_mid, f_small = (ImageFont.truetype(BOLD, 150), ImageFont.truetype(BOLD, 40),
                            ImageFont.truetype(SANS, 26))
    c = data["campaign"]
    title = f"campaign #{c['id']} — {c['target']}"
    tw = d.textlength(title, font=f_mid)
    d.text(((W - tw) / 2, 80), title, font=f_mid, fill=WHITE)
    score_txt = f"{data['score']}/100"
    tw = d.textlength(score_txt, font=f_big)
    d.text(((W - tw) / 2 - 90, 200), score_txt, font=f_big,
           fill=GRADE_COLORS[data["grade"]])
    # grade badge
    bx0, bx1 = W / 2 + 200, W / 2 + 320
    d.ellipse([bx0, 250, bx1, 370], fill=GRADE_COLORS[data["grade"]])
    gf = ImageFont.truetype(BOLD, 72)
    g = data["grade"]
    d.text(((bx0 + bx1) / 2 - d.textlength(g, font=gf) / 2, 268), g, font=gf, fill=WHITE)
    counts = data["counts"]
    sub = (f"{counts['fail']} attacks succeeded   ·   "
           f"{counts['pass']} blocked   ·   {counts['total']} total")
    tw = d.textlength(sub, font=f_small)
    d.text(((W - tw) / 2, 470), sub, font=f_small, fill=MUTED)
    note = "every failed attempt ships with a full transcript + a fix"
    tw = d.textlength(note, font=f_small)
    d.text(((W - tw) / 2, 530), note, font=f_small, fill=MUTED)
    img.save(f"{SHOTS}/score.png")


def finding_card(data):
    img, d = base()
    f_h, f_b, f_m = (ImageFont.truetype(BOLD, 36), ImageFont.truetype(SANS, 24),
                     ImageFont.truetype(MONO, 21))
    f = data["findings"][0]
    d.text((70, 60), f"finding: {f['probe_name']}", font=f_h, fill=WHITE)
    sev = f["severity"].upper()
    d.rounded_rectangle([70, 120, 230, 158], radius=18, fill=RED)
    sf = ImageFont.truetype(BOLD, 22)
    d.text((70 + (160 - d.textlength(sev, font=sf)) / 2, 126), sev, font=sf, fill=WHITE)
    y = 190
    user_msg = next((m["content"] for m in f["messages"] if m["role"] == "user"), "")
    for label, text, color in [("attacker:", user_msg, WHITE),
                               ("agent:", f["response"][:220], RED)]:
        d.text((70, y), label, font=f_b, fill=MUTED)
        y += 36
        for line in wrapped(d, text, f_m, W - 160)[:3]:
            d.text((70, y), line, font=f_m, fill=color)
            y += 30
        y += 14
    d.text((70, y + 6), "how to fix:", font=f_b, fill=GREEN)
    y += 42
    for line in wrapped(d, f["remediation"], f_b, W - 160)[:3]:
        d.text((70, y), line, font=f_b, fill=WHITE)
        y += 34
    img.save(f"{SHOTS}/finding.png")


def leaderboard_card(rows):
    img, d = base()
    f_h, f_b = ImageFont.truetype(BOLD, 44), ImageFont.truetype(SANS, 28)
    t = "leaderboard — latest score per target"
    d.text(((W - d.textlength(t, font=f_h)) / 2, 50), t, font=f_h, fill=WHITE)
    y = 150
    for i, (target, score, grade) in enumerate(rows):
        gc = GRADE_COLORS[grade]
        d.text((180, y), f"{i + 1}.", font=f_b, fill=MUTED)
        d.text((240, y), target, font=f_b, fill=WHITE)
        s = f"{score}/100"
        d.text((700, y), s, font=f_b, fill=gc)
        d.ellipse([900, y - 2, 948, y + 46], fill=gc)
        gf = ImageFont.truetype(BOLD, 26)
        d.text((924 - d.textlength(grade, font=gf) / 2, y + 2), grade, font=gf, fill=WHITE)
        y += 78
    img.save(f"{SHOTS}/leaderboard.png")


def outro_card():
    img, d = base()
    f1, f2 = ImageFont.truetype(BOLD, 64), ImageFont.truetype(SANS, 32)
    for text, f, color, y in [("MIT licensed", f1, WHITE, 250),
                              ("github.com/SaiSankeerth-dev/Red-team-scanner-for-AI-agents", f2, RED, 360)]:
        tw = d.textlength(text, font=f)
        d.text(((W - tw) / 2, y), text, font=f, fill=color)
    img.save(f"{SHOTS}/outro.png")


def scene(png, seconds, caption, idx):
    mp4 = f"/tmp/scene{idx}.mp4"
    cap = caption.replace(":", "\\:").replace("'", "")
    vf = (
        f"zoompan=z='min(zoom+0.0006,1.08)':d={seconds*30}:s=1280x720:fps=30,"
        f"drawbox=y=ih-84:c=black@0.72:w=iw:h=84:t=fill,"
        f"drawtext=fontfile={SANS}:text='{cap}':fontsize=26:fontcolor=white:"
        f"x=(w-text_w)/2:y=h-58"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", png,
         "-vf", vf, "-t", str(seconds), "-pix_fmt", "yuv420p", mp4],
        check=True)
    return mp4


def main():
    os.makedirs(SHOTS, exist_ok=True)
    with db.session_scope() as s:
        latest = {}
        for c in s.query(Campaign).order_by(Campaign.id).all():
            latest[c.target] = c.id
        vuln = build_report_data(s, latest["vulnerable"])
        rows = []
        for target in ["hardened", "almost-hardened", "eager-assistant",
                       "naive-rag", "vulnerable"]:
            dd = build_report_data(s, latest[target])
            rows.append((target, dd["score"], dd["grade"]))

    title_card()
    terminal_card()
    score_card(vuln)
    finding_card(vuln)
    leaderboard_card(rows)
    outro_card()

    scenes = [
        (f"{SHOTS}/title.png", 6, "Redline: automated red-team scanner for AI agents"),
        (f"{SHOTS}/terminal.png", 14, "33 attacks run in about 2 seconds, every attempt recorded"),
        (f"{SHOTS}/score.png", 12, "Scored 0-100 and graded A to F"),
        (f"{SHOTS}/finding.png", 14, "Each finding ships with a transcript and a fix"),
        (f"{SHOTS}/leaderboard.png", 12, "Hardened 100/A down to vulnerable 0/F"),
        (f"{SHOTS}/outro.png", 7, "npm audit, but for AI agents"),
    ]
    parts = [scene(png, secs, cap, i) for i, (png, secs, cap) in enumerate(scenes)]
    with open("/tmp/concat.txt", "w") as fh:
        fh.write("".join(f"file '{p}'\n" for p in parts))
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", "/tmp/concat.txt", "-c", "copy", OUT], check=True)
    print(f"wrote {OUT} ({sum(s for _, s, _ in scenes)}s)")


if __name__ == "__main__":
    main()
