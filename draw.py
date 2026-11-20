#!/usr/bin/env python3
"""Draw the news-image-20261120 entry: Friday 20 November 2026 in one picture.

A newspaper front page rendered entirely with Pillow: a reusable scene
library (layered, labelled scenes with gradients, shadows and halftone
texture) composed into masthead, tally strip, timeline, four heroes,
twelve cards, a dotted world map and a briefs column. Deterministic:
a fixed seed drives every pseudo-random detail, so two runs of this
file produce byte-identical PNGs.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
FD = "/usr/share/fonts/truetype/dejavu/"

# ---------------------------------------------------------------- palette
PAPER = (243, 238, 226)
PAPER_DK = (232, 224, 205)
INK = (26, 24, 20)
MUTE = (96, 90, 78)
RED = (178, 34, 30)
RED_DK = (140, 26, 24)
NAVY = (18, 32, 54)
TEAL = (23, 92, 96)
GOLD = (196, 148, 38)
GREEN = (38, 110, 62)
SKIN = (222, 184, 150)


def SERIF(sz):
    return ImageFont.truetype(FD + "DejaVuSerif-Bold.ttf", sz)


def SANS(sz):
    return ImageFont.truetype(FD + "DejaVuSans.ttf", sz)


def SANS_B(sz):
    return ImageFont.truetype(FD + "DejaVuSans-Bold.ttf", sz)


def SANS_O(sz):
    # no DejaVu Sans Oblique on this system; the strap reads better in
    # the regular serif anyway, so use it for oblique-style lines
    return ImageFont.truetype(FD + "DejaVuSerif.ttf", sz)


# ---------------------------------------------------------------- helpers
OVERFLOWS = []


def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if d.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def text_block(d, x, y, text, font, fill, maxw, leading, max_lines=None, tag=""):
    lines = wrap(d, text, font, maxw)
    if max_lines and len(lines) > max_lines:
        OVERFLOWS.append(f"{tag}: {len(lines)} lines > {max_lines}: {text[:40]}")
        lines = lines[:max_lines]
    for ln in lines:
        d.text((x, y), ln, font=font, fill=fill)
        y += leading
    return y


def center(d, y, text, font, fill, cx=W // 2):
    d.text((cx - d.textlength(text, font=font) / 2, y), text, font=font, fill=fill)


def vgrad(w, h, top, bot):
    """Vertical gradient image of size w x h from top colour to bot colour."""
    img = Image.new("RGB", (w, h))
    px = img.load()
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        for xx in range(w):
            px[xx, yy] = c
    return img


def halftone(d, box, colour, step=7, r=1, phase=0):
    x0, y0, x1, y1 = box
    for yy in range(y0 + phase, y1, step):
        off = phase if (yy // step) % 2 else 0
        for xx in range(x0 + off, x1, step):
            d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=colour)


def soft_shadow(d, cx, cy, w, h, colour=(0, 0, 0)):
    for i, a in enumerate((70, 45, 25)):
        d.ellipse([cx - w // 2 - i * 2, cy - h // 2 - i, cx + w // 2 + i * 2,
                   cy + h // 2 + i], fill=None)
    d.ellipse([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2],
              fill=(colour[0], colour[1], colour[2]))


def tag(d, x, y, text, bg, fg=(255, 255, 255), font=None, pad=4):
    """Small filled label tag with its text; returns its right edge."""
    f = font or SANS_B(9)
    w = int(d.textlength(text, font=f)) + pad * 2
    d.rectangle([x, y, x + w, y + 15], fill=bg)
    d.text((x + pad, y + 2), text, font=f, fill=fg)
    return x + w


def rtext(d, w, y, text, fill, font=None):
    """Right-aligned small figure text inside a scene."""
    f = font or SANS_B(8)
    d.text((w - 4 - d.textlength(text, font=f), y), text, font=f, fill=fill)


def chip(d, x, y, text, kind):
    """Status chip: coloured dot + bold small-caps text, right-aligned to x."""
    colours = {"CONFIRMED": GREEN, "OFFICIALS": TEAL, "CLOSE": NAVY,
               "ONGOING": GOLD, "REPORT": (120, 70, 160), "AGREED": GREEN,
               "ESTIMATE": (170, 100, 20), "ARRIVED": TEAL, "EARLY": (170, 100, 20),
               "RESULT": GREEN, "OFFICIAL": TEAL, "CEREMONY": GOLD,
               "CLAIM": (178, 34, 30)}
    c = colours.get(kind, MUTE)
    f = SANS_B(8)
    w = int(d.textlength(text, font=f)) + 14
    d.rectangle([x - w, y, x, y + 13], outline=c, width=1)
    d.ellipse([x - w + 3, y + 4, x - w + 8, y + 9], fill=c)
    d.text((x - w + 11, y + 2), text, font=f, fill=c)
    return x - w


def num_badge(d, x, y, n, bg=RED):
    d.ellipse([x, y, x + 17, y + 17], fill=bg)
    s = str(n)
    f = SANS_B(10)
    d.text((x + 8.5 - d.textlength(s, font=f) / 2, y + 2), s, font=f,
           fill=(255, 255, 255))


def scene_canvas(w, h, top, bot):
    img = vgrad(w, h, top, bot)
    return img, ImageDraw.Draw(img, "RGBA")


def paste_scene(page, img, x, y):
    page.paste(img, (x, y))
    d = ImageDraw.Draw(page)
    d.rectangle([x, y, x + img.width - 1, y + img.height - 1], outline=INK, width=1)
    return d


# ================================================================ SCENES
# Each scene builder returns an RGB image of exactly w x h, drawn in
# layers: sky/background gradient, midground landmarks, foreground
# actors/objects, soft shadows, halftone texture and in-scene labels.

def scene_kyiv(w, h):
    img, d = scene_canvas(w, h, (10, 18, 40), (38, 62, 92))
    rng = random.Random(11)
    for _ in range(46):  # stars
        sx, sy = rng.randrange(w), rng.randrange(h // 2)
        d.point((sx, sy), fill=(220, 228, 240))
    # skyline: two banks of tower blocks with lit windows
    for bx, bw, bh, tone in [(4, 30, 52, 16), (38, 22, 68, 22), (64, 34, 44, 14),
                             (w - 96, 30, 58, 20), (w - 62, 24, 74, 26),
                             (w - 34, 28, 48, 15)]:
        d.rectangle([bx, h - 34 - bh, bx + bw, h - 34], fill=(tone, tone + 6, tone + 16))
        for wy in range(h - 30 - bh, h - 40, 7):
            for wx in range(bx + 3, bx + bw - 3, 6):
                if rng.random() < 0.42:
                    d.rectangle([wx, wy, wx + 2, wy + 3], fill=(250, 205, 110))
    # missile trails: dashed arcs falling toward the bridges
    for (sx, tx, col) in [(30, 96, (255, 170, 90)), (86, 150, (255, 140, 80)),
                          (w - 60, w - 130, (255, 170, 90))]:
        pts = []
        for i in range(21):
            t = i / 20
            pts.append((sx + (tx - sx) * t, 6 + (h - 52) * t * t))
        for i in range(0, 20, 2):
            d.line([pts[i], pts[i + 1]], fill=col, width=2)
        ex, ey = pts[-1]
        for r_ in (9, 6, 3):  # explosion burst
            d.ellipse([ex - r_, ey - r_, ex + r_, ey + r_],
                      fill=(255, 190 - r_ * 8, 70))
    # the Dnipro: river band with three bridges
    d.rectangle([0, h - 34, w, h], fill=(16, 44, 74))
    for i in range(0, w, 9):
        d.line([i, h - 8 - (i % 3) * 3, i + 5, h - 8 - (i % 3) * 3],
               fill=(70, 120, 165))
    for bx in (w * 0.22, w * 0.52, w * 0.80):
        d.arc([bx - 26, h - 52, bx + 26, h - 16], 180, 360, fill=(210, 200, 180), width=3)
        d.line([bx - 30, h - 33, bx + 30, h - 33], fill=(230, 220, 200), width=2)
        d.line([bx, h - 50, bx, h - 34], fill=(210, 200, 180), width=2)
    tag(d, 6, 6, "KYIV", RED)
    tag(d, 6, h - 15, "DNIPRO RIVER", (0, 0, 0))
    tag(d, w - 96, 6, "3 BRIDGES HIT", RED)
    return img


def scene_cyclone(w, h):
    img, d = scene_canvas(w, h, (96, 128, 150), (196, 205, 196))
    cx, cy = w - 62, 40
    for r_ in range(52, 8, -9):  # spiral storm bands
        d.arc([cx - r_, cy - r_ * 0.72, cx + r_, cy + r_ * 0.72],
              20 + r_, 300 + r_, fill=(240, 244, 246), width=5)
    d.ellipse([cx - 8, cy - 6, cx + 8, cy + 6], fill=(60, 84, 104))
    # coast and sea
    d.polygon([(0, h - 44), (w * 0.52, h - 52), (w * 0.72, h - 30), (w, h - 38),
               (w, h), (0, h)], fill=(214, 196, 150))
    d.polygon([(0, h - 26), (w, h - 30), (w, h), (0, h)], fill=(52, 110, 140))
    for i in range(6):  # waves
        yv = h - 22 + i * 4
        for xv in range(i * 13, w, 34):
            d.arc([xv, yv, xv + 16, yv + 6], 180, 330, fill=(190, 220, 235), width=2)
    rng = random.Random(23)
    for _ in range(60):  # rain streaks
        rx, ry = rng.randrange(w), rng.randrange(h - 40)
        d.line([rx, ry, rx - 3, ry + 6], fill=(225, 235, 240))
    # bent palms and shelter tents on the shore
    for px in (18, 44):
        d.line([px, h - 44, px + 4, h - 66], fill=(90, 70, 40), width=3)
        for a in range(5):
            ang = math.radians(150 + a * 22)
            d.line([px + 4, h - 66, px + 4 + 13 * math.cos(ang),
                    h - 66 + 8 * math.sin(ang)], fill=(52, 110, 62), width=2)
    for tx in (86, 116, 146):
        d.polygon([(tx, h - 40), (tx + 11, h - 54), (tx + 22, h - 40)],
                  fill=(196, 90, 50))
        d.rectangle([tx + 8, h - 47, tx + 14, h - 40], fill=(70, 44, 30))
    tag(d, 6, 6, "GOPALPUR · ODISHA", TEAL)
    tag(d, 6, h - 15, "LANDFALL 07:30 IST", (0, 0, 0))
    return img


def scene_cop(w, h):
    img, d = scene_canvas(w, h, (226, 216, 188), (196, 178, 140))
    # hall backdrop: flag row and a big globe
    flags = [(178, 34, 30), (30, 70, 160), (240, 190, 40), (38, 110, 62),
             (240, 240, 240), (200, 60, 140), (30, 130, 180), (240, 120, 40)]
    for i, fc in enumerate(flags):
        fx = 62 + i * (w - 130) // 8
        d.rectangle([fx, 8, fx + 12, 20], fill=fc, outline=(120, 105, 80))
    gx, gy = w // 2, 46
    d.ellipse([gx - 23, gy - 21, gx + 23, gy + 21], fill=(86, 140, 180))
    d.arc([gx - 23, gy - 21, gx + 23, gy + 21], 60, 200, fill=(70, 130, 90), width=5)
    d.arc([gx - 12, gy - 21, gx + 12, gy + 21], 240, 420, fill=(70, 130, 90), width=4)
    d.line([gx - 23, gy, gx + 23, gy], fill=(70, 130, 90), width=2)
    # thermometer of ambition, running low
    d.rectangle([w - 24, 26, w - 17, 62], outline=INK, width=1)
    d.rectangle([w - 23, 48, w - 18, 61], fill=RED)
    d.ellipse([w - 27, 58, w - 14, 71], fill=RED)
    d.text((w - 52, 76), "1.5°C", font=SANS_B(9), fill=RED_DK)
    # delegate desks in rows, heads, name plates
    for row in range(3):
        yv = h - 44 + row * 13
        for i in range(7):
            xv = 14 + i * (w - 28) // 7 + row * 4
            d.rectangle([xv, yv, xv + 20, yv + 7], fill=(122, 92, 58))
            d.ellipse([xv + 7, yv - 6, xv + 13, yv], fill=(70, 56, 44))
            d.rectangle([xv + 4, yv + 2, xv + 16, yv + 5], fill=(240, 236, 224))
    tag(d, 6, 6, "ANTALYA", RED)
    tag(d, 6, h - 15, "COP31 · FINAL DAY", (0, 0, 0))
    d.text((8, 34), "DRAFT: 144 → 80", font=SANS_B(9), fill=(90, 60, 30))
    return img


def scene_asia_selloff(w, h):
    img, d = scene_canvas(w, h, (14, 20, 34), (30, 40, 58))
    # grid + plunging chart line
    for gx in range(0, w, 24):
        d.line([gx, 8, gx, h - 26], fill=(44, 56, 76))
    for gy in range(8, h - 20, 16):
        d.line([0, gy, w, gy], fill=(44, 56, 76))
    pts = [(6, 18), (52, 24), (96, 20), (140, 38), (182, 34), (w - 60, 62),
           (w - 14, h - 34)]
    d.line(pts, fill=(255, 92, 82), width=3)
    for (px, py) in pts:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(255, 150, 140))
    ax, ay = pts[-1]
    d.polygon([(ax, ay), (ax - 12, ay - 3), (ax - 4, ay - 11)], fill=(255, 92, 82))
    # skyline silhouette along the bottom
    rng = random.Random(7)
    bx = 0
    while bx < w:
        bw = rng.randrange(14, 30)
        bh = rng.randrange(8, 24)
        d.rectangle([bx, h - 14 - bh, bx + bw, h - 14], fill=(10, 14, 24))
        bx += bw + 2
    d.rectangle([0, h - 14, w, h], fill=(8, 10, 18))
    tag(d, 6, 6, "AI SELL-OFF · ASIA CLOSE", RED)
    rows = [("TAIEX", "-6.2%"), ("KOSPI", "-5.2%"), ("NIKKEI", "-5.1%")]
    for i, (nm, val) in enumerate(rows):
        yv = 26 + i * 17
        d.text((8, yv), nm, font=SANS_B(10), fill=(220, 228, 240))
        d.text((58, yv), val, font=SANS_B(10), fill=(255, 120, 110))
    d.text((w - 104, h - 13), "SOFTBANK -14.5%", font=SANS_B(8),
           fill=(255, 190, 120))
    return img


# ------------------------------------------------------------ card scenes
def scene_brussels(w, h):
    img, d = scene_canvas(w, h, (24, 52, 110), (44, 84, 150))
    for i in range(12):  # EU circle of stars
        a = math.radians(i * 30 - 90)
        sx, sy = 30 + 15 * math.cos(a), h // 2 + 15 * math.sin(a)
        d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(250, 205, 60))
    # Union Jack corner
    d.rectangle([w - 52, 6, w - 6, 32], fill=(36, 56, 130))
    d.line([w - 52, 6, w - 6, 32], fill=(255, 255, 255), width=4)
    d.line([w - 52, 32, w - 6, 6], fill=(255, 255, 255), width=4)
    d.line([w - 52, 6, w - 6, 32], fill=RED, width=2)
    d.line([w - 52, 32, w - 6, 6], fill=RED, width=2)
    d.line([w - 29, 6, w - 29, 32], fill=(255, 255, 255), width=7)
    d.line([w - 52, 19, w - 6, 19], fill=(255, 255, 255), width=7)
    d.line([w - 29, 6, w - 29, 32], fill=RED, width=3)
    d.line([w - 52, 19, w - 6, 19], fill=RED, width=3)
    # handshake: two sleeves meeting over a document
    d.polygon([(52, h - 6), (86, h - 22), (98, h - 12), (70, h - 2)],
              fill=(30, 34, 44))
    d.polygon([(w - 52, h - 6), (w - 86, h - 22), (w - 98, h - 12), (w - 70, h - 2)],
              fill=(90, 40, 36))
    d.ellipse([w // 2 - 10, h - 20, w // 2 + 10, h - 8], fill=SKIN)
    d.rectangle([w // 2 - 24, h - 8, w // 2 + 24, h - 2], fill=(240, 236, 224))
    tag(d, 4, 4, "£5.1BN/YR RESET DEAL", GREEN)
    return img


def scene_poland(w, h):
    img, d = scene_canvas(w, h, (168, 186, 150), (120, 140, 96))
    for i in range(6):  # field furrows
        d.line([0, h - 6 - i * 5, w, h - 16 - i * 5], fill=(96, 116, 74), width=2)
    # fallen missile body, diagonal, with a small crater and smoke
    d.polygon([(30, h - 14), (96, 12), (106, 16), (44, h - 8)], fill=(150, 152, 148))
    d.polygon([(96, 12), (112, 4), (106, 16)], fill=RED)
    d.ellipse([22, h - 16, 58, h - 4], fill=(74, 62, 48))
    for i in range(4):
        d.ellipse([30 + i * 4, h - 30 - i * 6, 40 + i * 5, h - 22 - i * 6],
                  fill=(200, 200, 196))
    # NATO star badge
    cx, cy = w - 22, 14
    d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=NAVY)
    for a in range(4):
        ang = math.radians(a * 90)
        d.polygon([(cx, cy), (cx + 8 * math.cos(ang - 0.2), cy + 8 * math.sin(ang - 0.2)),
                   (cx + 8 * math.cos(ang + 0.2), cy + 8 * math.sin(ang + 0.2))],
                  fill=(255, 255, 255))
    tag(d, 4, 4, "KH-101 IN POLAND", RED)
    s = "2 MISSILES · 1 DRONE"
    d.text((w - 4 - d.textlength(s, font=SANS_B(8)), h - 14), s,
           font=SANS_B(8), fill=(255, 250, 235), stroke_width=1,
           stroke_fill=(40, 44, 32))
    return img


def scene_wallst(w, h):
    img, d = scene_canvas(w, h, (16, 18, 26), (34, 36, 46))
    vals = [0.5, 0.62, 0.55, 0.7, 0.6, 0.78, 0.66, 0.85]
    for i, v in enumerate(vals):  # red candles sliding down-right
        x = 8 + i * 13
        top = 6 + i * 3
        d.rectangle([x, top, x + 7, top + int(16 * v) + 6], fill=(215, 70, 62))
        d.line([x + 3, top - 3, x + 3, top + int(16 * v) + 9], fill=(215, 70, 62))
    d.line([(6, 10), (52, 20), (96, 26), (w - 10, h - 12)], fill=(255, 120, 110), width=2)
    tag(d, 4, h - 17, "NASDAQ -2.85%", RED)
    d.text((w - 62, 6), "ANT -11%", font=SANS_B(10), fill=(255, 190, 120))
    return img


def scene_gta(w, h):
    img, d = scene_canvas(w, h, (250, 150, 90), (150, 60, 120))
    d.ellipse([w - 44, 4, w - 16, 32], fill=(255, 220, 130))  # sun
    for bx, bw, bh in [(6, 16, 24), (26, 12, 32), (42, 18, 20), (64, 12, 28)]:
        d.rectangle([bx, h - 10 - bh, bx + bw, h - 10], fill=(60, 30, 70))
    for px in (w - 60, w - 30):  # palms
        d.line([px, h - 8, px + 3, h - 30], fill=(40, 26, 40), width=3)
        for a in range(5):
            ang = math.radians(140 + a * 26)
            d.line([px + 3, h - 30, px + 3 + 12 * math.cos(ang),
                    h - 30 + 7 * math.sin(ang)], fill=(34, 90, 54), width=2)
    d.rectangle([0, h - 10, w, h], fill=(46, 22, 56))
    # controller
    cx, cy = 34, 20
    d.rounded_rectangle([cx - 17, cy - 8, cx + 17, cy + 9], 7, fill=(30, 30, 40))
    d.line([cx - 10, cy, cx - 4, cy], fill=(255, 255, 255), width=2)
    d.line([cx - 7, cy - 3, cx - 7, cy + 3], fill=(255, 255, 255), width=2)
    d.ellipse([cx + 7, cy - 4, cx + 11, cy], fill=(255, 120, 110))
    d.ellipse([cx + 11, cy + 1, cx + 15, cy + 5], fill=(120, 220, 150))
    tag(d, w - 76, h - 17, "$2.36BN DAY ONE", GOLD, fg=(30, 24, 10))
    d.text((58, 8), "VICE CITY", font=SANS_B(10), fill=(255, 255, 255))
    return img


def scene_gaza(w, h):
    img, d = scene_canvas(w, h, (226, 198, 158), (196, 164, 116))
    d.ellipse([w - 34, 4, w - 10, 28], fill=(250, 214, 130))
    # dashed Yellow Line across the sand
    for x in range(6, w - 6, 12):
        d.line([x, h // 2 + 4, x + 7, h // 2 + 4], fill=(240, 190, 30), width=3)
    # tank silhouette west of the line
    d.rectangle([14, h - 24, 52, h - 14], fill=(84, 80, 62))
    d.rectangle([24, h - 30, 44, h - 24], fill=(84, 80, 62))
    d.line([44, h - 27, 66, h - 29], fill=(60, 58, 44), width=3)
    for wx in range(17, 52, 8):
        d.ellipse([wx, h - 15, wx + 6, h - 9], fill=(50, 48, 38))
    # tents east of the line
    for tx in (w - 52, w - 30):
        d.polygon([(tx, h - 12), (tx + 8, h - 24), (tx + 16, h - 12)],
                  fill=(238, 232, 218))
    tag(d, 4, 4, "YELLOW LINE · 6,000 FLED", (150, 116, 10))
    d.text((w - 74, h - 15), "RAID ENDED", font=SANS_B(9), fill=(90, 70, 40))
    return img


def scene_mercury(w, h):
    img, d = scene_canvas(w, h, (6, 8, 18), (20, 24, 40))
    rng = random.Random(5)
    for _ in range(34):
        d.point((rng.randrange(w), rng.randrange(h)), fill=(200, 208, 226))
    gx, gy, gr = w - 42, h // 2 + 2, 24  # Mercury
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=(168, 158, 148))
    for (ox, oy, orr) in [(-9, -6, 5), (7, 3, 7), (-2, 10, 4), (11, -11, 3)]:
        d.ellipse([gx + ox - orr, gy + oy - orr, gx + ox + orr, gy + oy + orr],
                  outline=(128, 118, 106), width=1)
    d.arc([gx - gr - 8, gy - gr - 6, gx + gr + 8, gy + gr + 6], 200, 320,
          fill=(140, 160, 190), width=1)
    # the probe: bus, dish and two solar wings
    px, py = 40, h // 2 - 4
    d.rectangle([px - 16, py - 3, px - 4, py + 3], fill=(70, 110, 190))
    d.rectangle([px + 4, py - 3, px + 16, py + 3], fill=(70, 110, 190))
    d.rectangle([px - 4, py - 5, px + 4, py + 5], fill=(210, 200, 180))
    d.arc([px - 8, py - 14, px + 2, py - 4], 270, 360, fill=(230, 228, 220), width=2)
    d.line([(px, py), (gx - gr - 6, gy - 8)], fill=(120, 140, 170))
    tag(d, 4, 4, "MERCURY REACHED", TEAL)
    d.text((4, h - 14), "8 YEARS · 6BN MILES", font=SANS_B(8), fill=(200, 208, 226))
    return img


def scene_japan(w, h):
    img, d = scene_canvas(w, h, (240, 236, 226), (222, 214, 196))
    d.ellipse([10, 6, 38, 34], fill=RED)  # rising sun disc
    base = h - 10
    for i, v in enumerate((0.32, 0.45, 0.58, 0.8)):  # inflation bars climbing
        x = 58 + i * 20
        d.rectangle([x, base - int(30 * v), x + 13, base], fill=(58, 74, 110))
    d.line([(54, base - 8), (92, base - 18), (w - 14, base - 30)],
           fill=RED, width=2)
    d.polygon([(w - 14, base - 30), (w - 24, base - 29), (w - 16, base - 22)],
              fill=RED)
    tag(d, 4, h - 17, "CPI +2.3% OCT", RED)
    return img


def scene_strike(w, h):
    img, d = scene_canvas(w, h, (206, 214, 224), (168, 178, 192))
    rng = random.Random(3)
    for i in range(9):  # marching crowd: heads and shoulders
        x = 8 + i * (w - 16) // 9
        y = h - 18 - (i % 3) * 3
        d.ellipse([x, y - 8, x + 7, y - 1], fill=(52, 48, 44))
        d.rectangle([x - 1, y, x + 8, y + 8], fill=(90 + (i % 3) * 30, 70, 66))
    for (px, txt) in [(6, "SCIOPERO"), (w // 2 - 26, "BUDGET"), (w - 58, "CGIL")]:
        d.line([px + 26, 8, px + 26, h - 22], fill=(110, 88, 60), width=2)
        d.rectangle([px, 6, px + 52, 20], fill=(250, 248, 242), outline=INK)
        f = SANS_B(7.5)
        d.text((px + 26 - d.textlength(txt, font=f) / 2, 9), txt, font=f, fill=RED_DK)
    tag(d, 4, h - 17, "100 RALLIES", RED)
    return img


def scene_exam(w, h):
    img, d = scene_canvas(w, h, (238, 234, 222), (214, 208, 190))
    d.rectangle([10, 10, 66, h - 10], fill=(252, 250, 244), outline=(150, 142, 124))
    for i in range(4):  # exam paper lines with ticks
        y = 17 + i * 8
        d.line([15, y, 48, y], fill=(170, 164, 148))
        d.line([54, y, 58, y + 3], fill=GREEN, width=2)
        d.line([58, y + 3], fill=GREEN)
        d.line([58, y + 3, 62, y - 2], fill=GREEN, width=2)
    # banned phone with a red cross
    d.rounded_rectangle([w - 44, 8, w - 14, h - 8], 5, fill=(30, 32, 40))
    d.rectangle([w - 40, 13, w - 18, h - 16], fill=(90, 130, 170))
    d.line([w - 46, 6, w - 12, h - 6], fill=RED, width=4)
    d.line([w - 46, h - 6, w - 12, 6], fill=RED, width=4)
    tag(d, 4, h - 17, "111 CAUGHT", RED)
    return img


def scene_pill(w, h):
    img, d = scene_canvas(w, h, (232, 240, 238), (200, 220, 210))
    # capsule, tilted
    d.rounded_rectangle([12, 12, 74, 30], 9, fill=(240, 244, 246), outline=INK)
    d.rounded_rectangle([43, 12, 74, 30], 9, fill=RED)
    d.line([(84, 22), (100, 22)], fill=INK, width=2)  # arrow
    d.polygon([(100, 22), (94, 18), (94, 26)], fill=INK)
    # tumour cluster shrinking left to right
    for (cx, cy, r_) in [(118, 14, 6), (130, 24, 5), (122, 30, 4), (140, 16, 3),
                         (148, 26, 2)]:
        d.ellipse([cx - r_, cy - r_, cx + r_, cy + r_], fill=(150, 90, 140))
    tag(d, 4, h - 17, "EARLY TRIAL", (170, 100, 20))
    s = "1 IN 12 CLEAR"
    d.text((w - d.textlength(s, font=SANS_B(8)) - 4, h - 15), s,
           font=SANS_B(8), fill=(110, 60, 110))
    return img


def scene_kenya(w, h):
    img, d = scene_canvas(w, h, (250, 196, 110), (232, 150, 84))
    d.ellipse([w - 40, 4, w - 14, 30], fill=(255, 226, 150))
    d.rectangle([0, h - 12, w, h], fill=(150, 104, 58))  # savanna floor
    # drilling derrick
    cx = 44
    d.line([cx - 14, h - 10, cx, 8], fill=(60, 48, 40), width=3)
    d.line([cx + 14, h - 10, cx, 8], fill=(60, 48, 40), width=3)
    for i in range(3):
        y = 16 + i * 9
        d.line([cx - 10 + i * 2, y, cx + 10 - i * 2, y], fill=(60, 48, 40), width=2)
    d.line([cx, 8, cx, h - 16], fill=(60, 48, 40), width=2)
    # acacia tree
    d.line([w - 30, h - 10, w - 28, h - 24], fill=(80, 60, 40), width=3)
    d.ellipse([w - 48, h - 34, w - 8, h - 22], fill=(86, 110, 54))
    tag(d, 4, 4, "FIRST OIL WELL", (120, 70, 20))
    rtext(d, w, h - 14, "CRUDE DUE 1 DEC", (70, 40, 14))
    return img


def scene_tennis(w, h):
    img, d = scene_canvas(w, h, (52, 110, 66), (36, 84, 50))
    d.polygon([(10, h - 6), (44, 14), (w - 44, 14), (w - 10, h - 6)],
              fill=(64, 128, 78))  # court in perspective
    d.line([10, h - 6, w - 10, h - 6], fill=(255, 255, 255), width=2)
    d.line([44, 14, w - 44, 14], fill=(255, 255, 255), width=1)
    d.line([w // 2, 14, w // 2, h - 6], fill=(255, 255, 255), width=1)
    d.rectangle([30, 24, w - 30, 28], fill=(240, 240, 240))  # net
    for x in range(32, w - 30, 6):
        d.line([x, 24, x, 28], fill=(120, 120, 120))
    # ball trail arcing over the net
    pts = [(16, 10), (40, 4), (66, 6), (92, 14), (w - 18, 26)]
    d.line(pts, fill=(240, 230, 120), width=2)
    d.ellipse([w - 24, 22, w - 16, 30], fill=(220, 220, 90))
    tag(d, 4, h - 17, "ALCARAZ 6-4 6-1", GREEN)
    return img


# ================================================================ CONTENT
HEROES = [
    dict(n=1, scene=scene_kyiv, kick="KYIV · UKRAINE — WAR", chip=("OFFICIALS · UKRAINE", "OFFICIALS"),
         chip2=("CLAIM · MOSCOW", "CLAIM"),
         head="Russia's biggest blitz hits Kyiv's bridges",
         deck="110+ missiles and 400+ drones overnight; three Dnipro bridges hit; "
              "8 killed, 28 hurt; power and water cut. Putin had vowed revenge "
              "for the Crimean Bridge strikes. — Reuters"),
    dict(n=2, scene=scene_cyclone, kick="GOPALPUR · INDIA — CYCLONE", chip=("CONFIRMED · IMD", "CONFIRMED"),
         head="Cyclone Akvan comes ashore in Odisha",
         deck="Landfall 7:30–8:30am near Gopalpur at 70–80 km/h, gusting 90; "
              "300,000+ people moved to 9,341 shelters; 209mm of rain at "
              "Patrapur; no major damage reported. — IMD"),
    dict(n=3, scene=scene_cop, kick="ANTALYA · TÜRKIYE — CLIMATE", chip=("ONGOING · UN NEWS", "ONGOING"),
         head="COP31 ends its last day with no deal",
         deck="The draft drops fossil fuels and the $120bn adaptation pledge; "
              "a France- and Panama-led bloc demands a stronger text; the "
              "talks head into overtime. — UN News"),
    dict(n=4, scene=scene_asia_selloff, kick="TAIPEI · SEOUL · TOKYO — MARKETS", chip=("CLOSE · EXCHANGES", "CLOSE"),
         head="AI sell-off sinks Asia's stock markets",
         deck="Taiwan's worst week since 1991; SoftBank falls 14.5%, its worst "
              "day in two years; about $4tn is wiped from world stocks, gold "
              "and crypto in a day. — Exchanges"),
]

CARDS = [
    dict(n=5, scene=scene_brussels, kick="BRUSSELS · DIPLOMACY", chip=("AGREED · REUTERS", "AGREED"),
         head="UK and EU seal a “reset” deal",
         deck="Food checks eased, carbon markets linked, 100,000 youth places "
              "a year each way — from 2028. — Reuters"),
    dict(n=6, scene=scene_poland, kick="E. POLAND · SECURITY", chip=("CONFIRMED · POLAND", "CONFIRMED"),
         head="Russian missiles land in Poland",
         deck="Two missiles and a drone come down in the south-east; Tusk "
              "calls it a provocation; nobody hurt. — Reuters"),
    dict(n=7, scene=scene_wallst, kick="NEW YORK · MARKETS", chip=("CLOSE · NYSE", "CLOSE"),
         head="Anthropic dives as Wall Street slides",
         deck="Nasdaq −2.85% to 23,198 at the close; Anthropic −11% a day "
              "after its record debut. — NYSE"),
    dict(n=8, scene=scene_gta, kick="GAMES · BUSINESS", chip=("ESTIMATE · SENSOR TOWER", "ESTIMATE"),
         head="GTA VI's first day tops $2.36bn",
         deck="About 24.5m copies in 24 hours — the biggest entertainment "
              "launch ever, Sensor Tower estimates."),
    dict(n=9, scene=scene_gaza, kick="GAZA · WAR", chip=("REPORT · AL JAZEERA", "REPORT"),
         head="Israel ends its Gaza ground raid",
         deck="Troops withdraw beyond the Yellow Line; Hamas calls it a truce "
              "breach; the main road reopens. — Al Jazeera"),
    dict(n=10, scene=scene_mercury, kick="SPACE · SCIENCE", chip=("ARRIVED · ESA", "ARRIVED"),
         head="BepiColombo reaches Mercury",
         deck="After eight years the ESA–JAXA probe arrives; it enters orbit "
              "on Saturday. — ESA"),
    dict(n=11, scene=scene_japan, kick="TOKYO · ECONOMY", chip=("OFFICIAL · STATISTICS", "OFFICIAL"),
         head="Japan's inflation rises to 2.3%",
         deck="October prices +2.3%; a December rate rise in view as shares "
              "tumble. — Reuters"),
    dict(n=12, scene=scene_strike, kick="ROME · LABOUR", chip=("REPORT · REUTERS", "REPORT"),
         head="General strike over Italy's budget",
         deck="CGIL's 24-hour strike; workers and students march in about "
              "100 rallies, the union says."),
    dict(n=13, scene=scene_exam, kick="SEOUL · EXAM", chip=("OFFICIALS · SEOUL", "OFFICIALS"),
         head="111 caught cheating in Suneung",
         deck="Students caught with banned smart devices in the national "
              "university exam, officials say."),
    dict(n=14, scene=scene_pill, kick="HEALTH · SCIENCE", chip=("EARLY TRIAL", "EARLY"),
         head="Pill shrinks pancreatic tumours",
         deck="In an early trial, tumours vanished from scans in 1 of 12 "
              "patients; bigger trials to come."),
    dict(n=15, scene=scene_kenya, kick="TURKANA · ENERGY", chip=("CEREMONY · ALLAFRICA", "CEREMONY"),
         head="Kenya drills its first oil well",
         deck="Ceremony in Turkana; first crude is due on 1 December, the "
              "company says. — allAfrica"),
    dict(n=16, scene=scene_tennis, kick="TURIN · TENNIS", chip=("RESULT · ATP", "RESULT"),
         head="Alcaraz sweeps into the last four",
         deck="Beats Cobolli 6-4 6-1 at the ATP Finals; Medvedev beats "
              "Tiafoe 6-3 6-4. — ATP"),
]

BRIEFS = [
    ("Lviv:", "station strike kills two (BBC)"),
    ("Berlin:", "pupils strike against military service"),
    ("London:", "retail sales jump as households stockpile"),
    ("London:", "Oct borrowing £17bn, £1bn under forecast"),
    ("Beijing:", "China holds loan rates an 18th month"),
    ("Seoul:", "ruling party to impeach the top judge"),
    ("Lebanon:", "Israeli strikes hit south and east"),
    ("Yemen:", "gunmen fire on a cargo ship off coast"),
    ("Abuja:", "court bars new evidence against Tinubu"),
    ("Kampala:", "police enforce Ebola ban on rallies"),
    ("Malawi:", "fuel crisis brings night-long queues"),
    ("Africa:", "AfDB says 22 states in debt distress"),
    ("Las Vegas:", "Russell fastest in wet F1 practice"),
    ("Washington:", "Democrats query law firm's free work"),
    ("Wellington:", "Nicholls 175 in a stand of 216 (ICC)"),
    ("Sydney:", "shares fall 1.6% in the sell-off"),
    ("Antalya:", "EU official calls draft unacceptable"),
    ("Turin:", "ATP backs pay plan past $350m"),
    ("Budapest:", "Carlsen risks No. 1 after winless event"),
    ("Football:", "Ireland to face Croatia in play-off"),
    ("Tennis:", "Leon Smith quits as GB Davis Cup captain"),
    ("Gulf:", "US memo: Iran blockade lifts ship premiums"),
    ("Israel:", "Mossad chief urges new strikes on Iran"),
    ("S. Africa:", "nearly 600 women killed in 3 months"),
    ("Ethiopia:", "US warns citizens as troops mass"),
    ("Bangladesh:", "two ruling-party leaders killed"),
    ("Haiti:", "police say 34 gang members killed in raid"),
    ("California:", "coast waves top 9 metres"),
    ("New York:", "Mamdani plans to close Rikers by 2032"),
    ("Delhi:", "Pakistani minister, first since 2025 war"),
]

# region tag per brief, same order as BRIEFS (EUR/ASI/AME/AFR/MEA/OCE/GLO)
BRIEF_REGIONS = ["EUR", "EUR", "EUR", "EUR", "ASI", "ASI", "MEA", "MEA",
                 "AFR", "AFR", "AFR", "AFR", "AME", "AME", "OCE", "OCE",
                 "EUR", "GLO", "GLO", "EUR", "EUR", "MEA", "MEA", "AFR",
                 "AFR", "ASI", "AME", "AME", "AME", "ASI"]

# coarse dotted world map, 72 x 26 grid ('#' = land)
MAP_ROWS = [
    "                                                                        ",
    "      #########                                    ##                   ",
    "    #############        #           #################################  ",
    "   ###############                  ###############################   ",
    "    #############    ##             ################  #############     ",
    "     ##########   ########           ##############    ###########      ",
    "      ########   ##########           ############      #########       ",
    "       ######     ########             ##########        #######        ",
    "        ####       ######    ##         ########          #####         ",
    "         ###        ####  ########       ######            ###          ",
    "          ##         ##  ##########       ####                          ",
    "           #             ############      ##          #                ",
    "                        ##############                ##                ",
    "              #         ##############     #           ###   ##         ",
    "             ###         ############     ###           ########        ",
    "             ####         ##########     #####           ######         ",
    "              ####         ########       ###                         ",
    "              #####         ######                                     ",
    "               ####          ####                     ########        ",
    "               ###            ##                     ##########       ",
    "                #                                     ########          ",
    "                                                              ##        ",
    "                                                                        ",
]
# pin positions (grid col, row) for stories 1..16
PINS = {1: (41, 3), 2: (50, 10), 3: (43, 6), 4: (62, 7), 5: (34, 2),
        6: (39, 3), 7: (13, 5), 8: (12, 7), 9: (44, 8), 10: (68, 1),
        11: (64, 6), 12: (37, 6), 13: (61, 6), 14: (6, 2), 15: (43, 13),
        16: (36, 4)}


def draw_map(d, x0, y0, cw=4.0, rh=5.0):
    for ri, row in enumerate(MAP_ROWS):
        for ci, ch in enumerate(row):
            if ch == "#":
                cx, cy = x0 + ci * cw, y0 + ri * rh
                d.ellipse([cx - 1.4, cy - 1.4, cx + 1.4, cy + 1.4],
                          fill=(146, 128, 96))
    for n, (ci, ri) in PINS.items():
        cx, cy = x0 + ci * cw, y0 + ri * rh
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=RED)
        s = str(n)
        f = SANS_B(7)
        d.text((cx - d.textlength(s, font=f) / 2, cy - 4), s, font=f,
               fill=(255, 255, 255))


# ================================================================ THE PAGE
MX = 14           # page margin
CW = W - 2 * MX   # content width


def build_page():
    rng = random.Random(20261120)
    page = Image.new("RGB", (W, H), PAPER)
    # paper grain: narrow-band deterministic noise under everything
    # low-frequency paper mottling: a small noise tile upscaled smooth,
    # so it reads as texture yet still compresses well in the PNG
    tile = Image.new("L", (256, 256))
    tile.putdata([rng.randrange(222, 256) for _ in range(256 * 256)])
    noise = tile.resize((W, H), Image.BICUBIC)
    grain = Image.merge("RGB", (noise, noise, noise))
    page = Image.blend(page, grain, 0.07)
    d = ImageDraw.Draw(page)

    # ---- top strap + masthead
    d.text((MX, 8), "THE WORLD'S NEWS IN ONE PICTURE", font=SANS_B(10), fill=RED_DK)
    strap = "46 STORIES · 7 REGIONS · 10 FIELDS · COMPLETE DAY — INCL. EVENING RESULTS"
    d.text((W - MX - d.textlength(strap, font=SANS_B(10)), 8), strap,
           font=SANS_B(10), fill=INK)
    d.line([MX, 24, W - MX, 24], fill=INK, width=2)
    center(d, 30, "Friday 20 November 2026", SERIF(57), INK)
    d.line([MX, 100, W - MX, 100], fill=INK, width=1)
    sub = ("Russian missiles hit Kyiv's bridges · Cyclone Akvan strikes India · "
           "An AI sell-off sinks Asia's markets · UK and EU seal a deal")
    center(d, 105, sub, SANS_O(12.5), (60, 54, 44))

    # ---- big-number tally strip
    ty = 124
    tallies = [("3", "Dnipro bridges hit in Kyiv"), ("300,000+", "people moved before Akvan"),
               ("−6.2%", "Taiwan's Taiex at Friday's close"), ("100,000", "youth places a year in UK–EU deal"),
               ("$2.36bn", "GTA VI's first-day sales (est.)"), ("−2.85%", "Nasdaq at Friday's close")]
    colw = CW // 6
    for i, (big, small) in enumerate(tallies):
        x = MX + i * colw
        if i:
            d.line([x - 7, ty + 2, x - 7, ty + 40], fill=RED, width=2)
        d.text((x, ty), big, font=SERIF(21), fill=INK)
        text_block(d, x, ty + 27, small, SANS(8.5), MUTE, colw - 12, 10,
                   max_lines=2, tag=f"tally{i}")
    # ---- region tally bar
    by = ty + 46
    regions = [("Europe 11", (52, 84, 140)), ("Asia-Pacific 10", (178, 34, 30)),
               ("Americas 7", (23, 92, 96)), ("Africa 7", (196, 148, 38)),
               ("Middle East 5", (120, 70, 160)), ("Oceania 2", (38, 110, 62)),
               ("Global 4", (96, 90, 78))]
    widths = [11, 10, 7, 7, 5, 2, 4]
    d.rectangle([MX, by, MX + 46, by + 13], fill=INK)
    d.text((MX + 5, by + 2), "REGION", font=SANS_B(7.5), fill=(255, 255, 255))
    x = MX + 48
    total = sum(widths)
    avail = CW - 48
    for (label, col), wfrac in zip(regions, widths):
        seg = int(avail * wfrac / total)
        d.rectangle([x, by, x + seg - 2, by + 13], fill=col)
        f = SANS_B(8.5)
        if seg > 52:
            d.text((x + seg / 2 - d.textlength(label, font=f) / 2, by + 2),
                   label, font=f, fill=(255, 255, 255))
        x += seg

    # ---- field tally strip (breadth by subject, counted)
    fy2 = by + 16
    d.rectangle([MX, fy2, W - MX, fy2 + 15], fill=INK)
    fields = ("BY FIELD — Conflict 10 · Markets 8 · Politics 7 · Sport 7 · "
              "Science & Health 3 · Business 3 · Diplomacy 2 · Climate 2 · "
              "Weather & Disaster 2 · Society 2")
    d.text((MX + 8, fy2 + 3), fields, font=SANS_B(8.5), fill=(255, 255, 255))

    # ---- UTC timeline strip: hour-true positions, staggered labels
    ly = fy2 + 24
    d.text((MX, ly + 4), "THE DAY IN UTC", font=SANS_B(9), fill=RED_DK)
    d.line([MX + 96, ly + 9, W - MX, ly + 9], fill=(150, 142, 124), width=1)
    events = [(2 / 24, "02:00", "Akvan landfall", 0),
              (5.5 / 24, "05:30", "Kh-101 in Poland", 1),
              (6.5 / 24, "06:30", "Seoul close −5.2%", 0),
              (11 / 24, "11:00", "Brussels deal sealed", 1),
              (16 / 24, "16:00", "COP31 deadlocked", 0),
              (21 / 24, "21:00", "Wall St closes lower", 1)]
    for frac, tm, ev, row in events:
        ex = MX + 96 + frac * (CW - 110)
        d.ellipse([ex - 3, ly + 6, ex + 3, ly + 12], fill=RED)
        d.text((ex - 12, ly + 14), tm, font=SANS_B(8.5), fill=INK)
        f = SANS(8)
        d.text((ex - d.textlength(ev, font=f) / 2, ly + 25 + row * 11), ev,
               font=f, fill=MUTE)

    # ---- heroes
    hy = ly + 48
    hero_h, scene_h = 230, 104
    gap = 8
    hw = (CW - gap * 3) // 4
    for i, s in enumerate(HEROES):
        x = MX + i * (hw + gap)
        d = paste_scene(page, s["scene"](hw, scene_h), x, hy)
        num_badge(d, x + 5, hy + scene_h + 6, s["n"])
        d.text((x + 26, hy + scene_h + 8), s["kick"], font=SANS_B(8.5), fill=RED_DK)
        yy = text_block(d, x, hy + scene_h + 24, s["head"], SERIF(16.5), INK,
                        hw - 2, 18.5, max_lines=3, tag=f"hero{s['n']} head")
        yy = text_block(d, x, yy + 2, s["deck"], SANS(9.8), (52, 48, 40),
                        hw - 2, 12.0, max_lines=6, tag=f"hero{s['n']} deck")
        left = chip(d, x + hw - 2, hy + hero_h - 16, s["chip"][0], s["chip"][1])
        if s.get("chip2"):
            chip(d, left - 4, hy + hero_h - 16, s["chip2"][0], s["chip2"][1])
        if i:
            d.line([x - gap // 2, hy, x - gap // 2, hy + hero_h - 4],
                   fill=(190, 182, 164), width=1)

    # ---- cards, two rows of six
    cy = hy + hero_h + 6
    card_h, cscene_h = 140, 44
    cw6 = (CW - gap * 5) // 6
    for r in range(2):
        for c in range(6):
            s = CARDS[r * 6 + c]
            x = MX + c * (cw6 + gap)
            y = cy + r * (card_h + 5)
            d = paste_scene(page, s["scene"](cw6, cscene_h), x, y)
            num_badge(d, x + 3, y + cscene_h + 4, s["n"])
            d.text((x + 23, y + cscene_h + 6), s["kick"], font=SANS_B(7.5),
                   fill=RED_DK)
            yy = text_block(d, x, y + cscene_h + 19, s["head"], SERIF(12),
                            INK, cw6 - 1, 14, max_lines=3, tag=f"card{s['n']} head")
            text_block(d, x, yy + 1, s["deck"], SANS(8.6), (52, 48, 40),
                       cw6 - 1, 10.6, max_lines=4, tag=f"card{s['n']} deck")
            chip(d, x + cw6 - 1, y + card_h - 14, s["chip"][0], s["chip"][1])

    # ---- bottom: map + date check + legend (left), briefs (right)
    boty = cy + 2 * card_h + 13
    d.line([MX, boty - 6, W - MX, boty - 6], fill=INK, width=1)
    d.text((MX, boty), "WHERE IT HAPPENED", font=SANS_B(10), fill=INK)
    d.text((MX + 170, boty), "pins 1–16 = heroes & cards", font=SANS(8.5), fill=MUTE)
    draw_map(d, MX + 2, boty + 16, rh=3.5)
    dcy = boty + 101
    d.rectangle([MX, dcy, MX + 292, dcy + 58], outline=RED, width=1)
    d.text((MX + 6, dcy + 4), "DATE CHECK — LEFT OUT AS OLDER NEWS",
           font=SANS_B(8.5), fill=RED_DK)
    text_block(d, MX + 6, dcy + 17,
               "Thu 19 Nov: Shenzhen declaration; ICJ Myanmar ruling; "
               "Anthropic's debut (Fri fall shown); GTA VI launch "
               "(Fri sales shown). 16–17 Nov: Crimean strikes. "
               "NOT YET: Mercury orbit Sat 21 Nov; ATP final Sun 22 Nov; "
               "Las Vegas GP Sun 23 Nov.",
               SANS(8.0), (52, 48, 40), 280, 9.0, max_lines=5, tag="datecheck")
    lgy = dcy + 61
    d.rectangle([MX, lgy, MX + 292, lgy + 41], outline=(150, 142, 124), width=1)
    d.text((MX + 6, lgy + 3), "HOW SURE — THE CHIP ON EACH STORY",
           font=SANS_B(7.8), fill=INK)
    text_block(d, MX + 6, lgy + 13,
               "CONFIRMED = 2+ outlets · OFFICIAL = the body itself · "
               "REPORT = one outlet · CLAIM = one side's word · "
               "ESTIMATE = a firm's figure · CLOSE = exchange close",
               SANS(7.6), (52, 48, 40), 280, 9.0, max_lines=3, tag="legend")
    bx = MX + 308
    d.text((bx, boty), "ALSO ON FRIDAY 20 NOVEMBER", font=SANS_B(10), fill=INK)
    d.text((W - MX - 118, boty), "30 MORE STORIES · Nos 17–46", font=SANS_B(8.5),
           fill=MUTE)
    col_w = (W - MX - bx - 14) // 2
    for ci in range(2):
        yy = boty + 17
        for j in range(15):
            n = 17 + ci * 15 + j
            lead, rest = BRIEFS[ci * 15 + j]
            line = f"{n}. {BRIEF_REGIONS[ci * 15 + j]} {lead} {rest}"
            yy = text_block(d, bx + ci * (col_w + 14), yy, line, SANS(9.3),
                            (52, 48, 40), col_w, 11.2, max_lines=1,
                            tag=f"brief{n}")
    # ---- footer
    fy = H - 26
    d.line([MX, fy - 5, W - MX, fy - 5], fill=INK, width=1)
    d.text((MX, fy), "Every story here happened, or was first reported, on Friday "
                     "20 November 2026. Contested claims are marked as claims.",
           font=SANS(8.8), fill=(52, 48, 40))
    src = "Sources: Reuters · AP · AFP · BBC · UN News · IMD · ESA · ATP · Sensor Tower · Al Jazeera"
    d.text((W - MX - d.textlength(src, font=SANS(8.8)), fy + 11), src,
           font=SANS(8.8), fill=MUTE)
    d.text((MX, fy + 11), "One picture, one day: Friday 20 November 2026.",
           font=SANS_B(8.8), fill=INK)
    return page


def main():
    page = build_page()
    out = Path(__file__).resolve().parent / "entry.png"
    page.save(out, optimize=True)
    print(f"wrote {out} {out.stat().st_size} bytes; overflows: {OVERFLOWS}")


if __name__ == "__main__":
    main()
