#!/usr/bin/env python3
"""news-image-20261123 — deterministic broadsheet front page for 23 Nov 2026.

Renders at 2048x2048 with Pillow, then downscales (LANCZOS) to 1024x1024.
No network, no timestamps, no randomness: re-running produces byte-identical
entry.png. Every headline is a verified 23 November 2026 event (see
../dev/STORY-POOL.md); one-party claims stay attributed; tempting
neighbour-day stories are named in the DATE CHECK box, not on the page.
Winner-pattern layout: 44 stories, 3 heroes, stat strip, numbered stories,
world map with pins, per-story sources, DATE CHECK box.
"""
import math
from PIL import Image, ImageDraw, ImageFont

CANVAS = 2048
EDGE = 36

PAPER = (246, 241, 230)
INK = (24, 24, 30)
NAVY = (18, 38, 74)
RED = (178, 34, 34)
DARKRED = (122, 20, 20)
GOLD = (201, 162, 39)
TEAL = (16, 96, 110)
GREY = (110, 110, 116)
WHITE = (255, 255, 255)
CREAM = (252, 248, 238)
DARK = (16, 26, 40)
SEA = (24, 52, 92)
LAND = (120, 160, 110)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def F(path, size):
    return ImageFont.truetype(path, size)


def gradient(w, h, top, bottom):
    """Deterministic vertical gradient from a stretched 1x256 strip."""
    strip = Image.new("RGB", (1, 256))
    px = strip.load()
    for i in range(256):
        t = i / 255.0
        px[0, i] = tuple(int(top[c] + (bottom[c] - top[c]) * t)
                         for c in range(3))
    return strip.resize((w, h), Image.BILINEAR)


def wrap_text(d, text, fnt, max_w):
    lines, cur = [], ""
    for w in text.split():
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def block(d, x, y, text, fnt, fill, max_w, leading=None):
    """Draw wrapped text; returns (next_y, line_count)."""
    if leading is None:
        leading = int(fnt.size * 1.22)
    lines = wrap_text(d, text, fnt, max_w)
    for line in lines:
        d.text((x, y), line, font=fnt, fill=fill)
        y += leading
    return y, len(lines)


def hline(d, x0, y, x1, color=INK, width=4):
    d.line([(x0, y), (x1, y)], fill=color, width=width)


def tag(d, x, y, text, color=RED, size=28):
    d.text((x, y), text, font=F(SANS_B, size), fill=color)


def badge(d, x, y, n, r=24, fill=RED, fg=WHITE, size=30):
    d.ellipse([x - r, y - r, x + r, y + r], fill=fill, outline=INK, width=3)
    d.text((x, y), str(n), font=F(SANS_B, size), fill=fg, anchor="mm")


REGIONS = [
    ("MIDDLE EAST 6", (178, 34, 34)),
    ("EUROPE 13", (18, 60, 140)),
    ("ASIA 5", (16, 96, 110)),
    ("AMERICAS 8", (120, 60, 140)),
    ("AFRICA 5", (180, 120, 20)),
    ("OCEANIA 2", (40, 120, 60)),
    ("SPACE 1", (90, 90, 110)),
    ("GLOBAL 4", (110, 110, 116)),
]


def masthead(d):
    hline(d, EDGE, 46, CANVAS - EDGE, INK, 6)
    d.text((CANVAS // 2, 56), "THE WORLD IN ONE PICTURE",
           font=F(SERIF_B, 88), fill=INK, anchor="ma")
    d.text((CANVAS // 2, 146),
           "M O N D A Y   2 3   N O V E M B E R   2 0 2 6   \u00b7   "
           "4 4   S T O R I E S   \u00b7   O N E   P A G E",
           font=F(SANS_B, 40), fill=RED, anchor="ma")
    fnt = F(SANS_B, 26)
    sep = "  \u00b7  "
    total = sum(d.textlength(t, font=fnt) for t, _ in REGIONS)
    total += d.textlength(sep, font=fnt) * (len(REGIONS) - 1)
    x = (CANVAS - total) / 2
    for i, (t, col) in enumerate(REGIONS):
        if i:
            d.text((x, 202), sep, font=fnt, fill=GREY)
            x += d.textlength(sep, font=fnt)
        d.text((x, 202), t, font=fnt, fill=col)
        x += d.textlength(t, font=fnt)
    hline(d, EDGE, 238, CANVAS - EDGE, RED, 5)


STATS = [
    ("+31%", "Nvidia shares"),
    ("258", "House seats"),
    ("7", "drones sink Merkury"),
    ("24", "dead in Banten fire"),
    ("M6.5", "Vanuatu quake, 598 km"),
    ("$44bn", "CrowdStrike deal"),
    ("700,000", "women in NHS AI trial"),
    ("11", "dead in Dymer strike"),
]


def stats_band(d, y0, y1):
    d.rectangle([EDGE, y0, CANVAS - EDGE, y1], fill=NAVY, outline=INK,
                width=4)
    n = len(STATS)
    w = (CANVAS - 2 * EDGE) / n
    for i, (big, label) in enumerate(STATS):
        x = EDGE + i * w
        if i:
            d.line([(x, y0 + 12), (x, y1 - 12)], fill=(90, 120, 170), width=3)
        d.text((x + w / 2, y0 + 10), big, font=F(SERIF_B, 48),
               fill=GOLD, anchor="ma")
        d.text((x + w / 2, y0 + 66), label, font=F(SANS, 21),
               fill=(215, 220, 230), anchor="ma")


# ---- heroes ---------------------------------------------------------------
# Box height 356: illustration strip 158px, then kicker, headline
# (serif 38, max 2 lines), dek (sans 24, max 2 lines).

def hero(img, d, box, n, kick, head, dek, draw_fn):
    x0, y0, x1, y1 = box
    art = Image.new("RGB", (x1 - x0, 158), PAPER)
    a = ImageDraw.Draw(art, "RGBA")
    draw_fn(art, a, (0, 0, x1 - x0, 158))
    img.paste(art, (x0, y0))
    d.rectangle([x0, y0 + 158, x1, y1], fill=PAPER)
    d.rounded_rectangle(box, radius=14, outline=INK, width=4)
    badge(d, x0 + 40, y0 + 180, n)
    tag(d, x0 + 76, y0 + 166, kick, RED, 26)
    _, hl = block(d, x0 + 24, y0 + 206, head, F(SERIF_B, 38), INK,
                  x1 - x0 - 48, leading=42)
    assert hl <= 2, "hero headline overflow: " + head
    _, dl = block(d, x0 + 24, y0 + 294, dek, F(SANS, 24), INK,
                  x1 - x0 - 48, leading=28)
    assert dl <= 2, "hero dek overflow: " + dek
    d.rounded_rectangle(box, radius=14, outline=INK, width=4)


def draw_nvidia(img, d, box):
    """Santa Clara boardroom, after the vote: a giant green chip stamped
    NVDA, a rally arrow climbing +31%, circuit traces behind."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (8, 20, 14), (20, 60, 40)),
              (x0, y0))
    # circuit traces
    for cy in (24, 60, 96, 132):
        d.line([(x0 + 10, y0 + cy), (x0 + 180, y0 + cy), (x0 + 200, y0 + cy - 14),
                (x0 + 260, y0 + cy - 14)], fill=(40, 120, 70), width=3)
        d.ellipse([x0 + 254, y0 + cy - 20, x0 + 266, y0 + cy - 8],
                  fill=(90, 200, 130))
    # the chip
    d.rectangle([x0 + 300, y0 + 34, x0 + 470, y0 + 130], fill=(24, 90, 50),
                outline=GOLD, width=4)
    for px in range(312, 470, 24):
        d.rectangle([x0 + px, y0 + 24, x0 + px + 12, y0 + 34], fill=GOLD)
        d.rectangle([x0 + px, y0 + 130, x0 + px + 12, y0 + 140], fill=GOLD)
    for py in range(46, 130, 22):
        d.rectangle([x0 + 290, y0 + py, x0 + 300, y0 + py + 10], fill=GOLD)
        d.rectangle([x0 + 470, y0 + py, x0 + 480, y0 + py + 10], fill=GOLD)
    d.text((x0 + 385, y0 + 62), "NVDA", font=F(SANS_B, 34), fill=WHITE,
           anchor="ma")
    d.text((x0 + 385, y0 + 96), "+31%", font=F(SANS_B, 26), fill=(140, 240, 170),
           anchor="ma")
    # rally arrow, right side
    pts = [(x0 + 500, y0 + 128), (x0 + 560, y0 + 96), (x0 + 600, y0 + 104),
           (x0 + 648, y0 + 44)]
    d.line(pts, fill=(120, 230, 140), width=7, joint="curve")
    d.polygon([(x0 + 648, y0 + 44), (x0 + 624, y0 + 52), (x0 + 640, y0 + 70)],
              fill=(120, 230, 140))
    d.text((x0 + 24, y0 + 10), "SANTA CLARA", font=F(SANS_B, 28),
           fill=(180, 230, 190))


def draw_merkury(img, d, box):
    """Benghazi at night: the corvette Merkury listing hard, smoke and flame
    at the waterline, a sea drone closing in, harbour lights behind."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (8, 10, 28), (50, 60, 90)),
              (x0, y0))
    # harbour lights along the far shore
    for lx in range(20, 660, 46):
        d.ellipse([x0 + lx, y0 + 58, x0 + lx + 10, y0 + 68],
                  fill=(255, 210, 110))
    d.rectangle([x0, y0 + 108, x1, y1], fill=(18, 42, 66))
    # corvette hull, listing to port
    d.polygon([(x0 + 120, y0 + 96), (x0 + 520, y0 + 78), (x0 + 500, y0 + 118),
               (x0 + 140, y0 + 128)], fill=(70, 76, 84))
    d.rectangle([x0 + 300, y0 + 48, x0 + 360, y0 + 82], fill=(110, 116, 124))
    d.rectangle([x0 + 318, y0 + 30, x0 + 342, y0 + 50], fill=(90, 96, 104))
    # fire and smoke amidships (tips kept clear of the top label)
    for fx, fh in [(200, 44), (250, 58), (300, 42)]:
        d.polygon([(x0 + fx - 18, y0 + 92), (x0 + fx, y0 + 92 - fh),
                   (x0 + fx + 18, y0 + 92)], fill=(255, 120, 20))
        d.polygon([(x0 + fx - 9, y0 + 92), (x0 + fx, y0 + 92 - fh // 2),
                   (x0 + fx + 9, y0 + 92)], fill=(255, 210, 60))
    for sx, sy, sr in [(230, 26, 18), (262, 12, 24), (296, 28, 16)]:
        d.ellipse([x0 + sx - sr, y0 + sy - sr, x0 + sx + sr, y0 + sy + sr],
                  fill=(70, 66, 66))
    # sea drone skimming in from the right
    d.ellipse([x0 + 560, y0 + 118, x0 + 620, y0 + 136], fill=(30, 30, 36))
    d.line([(x0 + 560, y0 + 127), (x0 + 520, y0 + 127)], fill=WHITE, width=3)
    for wy in range(0, 640, 70):
        d.line([(x0 + wy, y0 + 140), (x0 + wy + 36, y0 + 140)],
               fill=(120, 170, 200), width=3)
    d.text((x0 + 24, y0 + 10), "BENGHAZI",
           font=F(SANS_B, 28), fill=(255, 220, 150))


def draw_gulf(img, d, box):
    """The Strait of Hormuz at dusk: a tanker burning, a second hull low in
    the water, missile arcs overhead, a mine bobbing between them."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (220, 130, 70), (70, 60, 90)),
              (x0, y0))
    d.rectangle([x0, y0 + 104, x1, y1], fill=(28, 60, 88))
    # missile arcs overhead
    for mx, my, mr in [(120, 30, 60), (330, 16, 70), (520, 28, 55)]:
        d.arc([x0 + mx - mr, y0 + my - mr, x0 + mx + mr, y0 + my + mr],
              200, 340, fill=(255, 220, 140), width=4)
    # burning tanker, left
    d.polygon([(x0 + 60, y0 + 92), (x0 + 300, y0 + 92), (x0 + 284, y0 + 122),
               (x0 + 76, y0 + 122)], fill=(150, 32, 32))
    d.rectangle([x0 + 220, y0 + 62, x0 + 258, y0 + 92], fill=(210, 210, 205))
    for fx, fh in [(110, 52), (160, 68), (210, 48)]:
        d.polygon([(x0 + fx - 16, y0 + 94), (x0 + fx, y0 + 94 - fh),
                   (x0 + fx + 16, y0 + 94)], fill=(255, 120, 20))
        d.polygon([(x0 + fx - 8, y0 + 94), (x0 + fx, y0 + 94 - fh // 2),
                   (x0 + fx + 8, y0 + 94)], fill=(255, 210, 60))
    for sx, sy, sr in [(270, 18, 16), (305, 8, 20), (338, 20, 14)]:
        d.ellipse([x0 + sx - sr, y0 + sy - sr, x0 + sx + sr, y0 + sy + sr],
                  fill=(60, 56, 56))
    # second tanker, listing, right
    d.polygon([(x0 + 380, y0 + 100), (x0 + 600, y0 + 86), (x0 + 584, y0 + 120),
               (x0 + 396, y0 + 126)], fill=(90, 90, 96))
    d.rectangle([x0 + 500, y0 + 58, x0 + 540, y0 + 88], fill=(160, 160, 155))
    # mine between them
    d.ellipse([x0 + 322, y0 + 118, x0 + 350, y0 + 146], fill=INK)
    for ang in range(0, 360, 45):
        r = math.radians(ang)
        d.line([(x0 + 336 + 12 * math.cos(r), y0 + 132 + 12 * math.sin(r)),
                (x0 + 336 + 20 * math.cos(r), y0 + 132 + 20 * math.sin(r))],
               fill=INK, width=4)
    for wy in range(0, 660, 64):
        d.line([(x0 + wy, y0 + 138), (x0 + wy + 32, y0 + 138)],
               fill=(140, 200, 230), width=3)
    d.text((x0 + 24, y0 + 8), "HORMUZ", font=F(SANS_B, 28),
           fill=(255, 230, 170))

# ---- generic panel -------------------------------------------------------
# Box height 238: illustration strip 74px, kicker, headline (max 2 lines),
# dek (max 2 lines). Illustrations are drawn at 140px height then scaled.

def panel(img, d, box, n, kick, head, dek, src, draw_fn, hsize=29,
          dsize=22, illu_h=74):
    x0, y0, x1, y1 = box
    art = Image.new("RGB", (x1 - x0, 140), PAPER)
    a = ImageDraw.Draw(art, "RGBA")
    draw_fn(art, a, (0, 0, x1 - x0, 140))
    img.paste(art.resize((x1 - x0, illu_h), Image.LANCZOS), (x0, y0))
    d.rectangle([x0, y0 + illu_h, x1, y1], fill=PAPER)
    d.rounded_rectangle(box, radius=12, outline=INK, width=4)
    badge(d, x0 + 30, y0 + illu_h + 22, n, r=19, size=25)
    tag(d, x0 + 58, y0 + illu_h + 12, kick, RED, 22)
    _, hl = block(d, x0 + 18, y0 + illu_h + 42, head, F(SERIF_B, hsize), INK,
                  x1 - x0 - 36, leading=int(hsize * 1.2))
    assert hl <= 2, "panel headline overflow: " + head
    dy = y0 + illu_h + 42 + 2 * int(hsize * 1.2) + 2
    _, dl = block(d, x0 + 18, dy, dek + " \u2014 " + src, F(SANS, dsize), INK,
                  x1 - x0 - 36, leading=int(dsize * 1.22))
    assert dl <= 2, "panel dek overflow: " + dek
    d.rounded_rectangle(box, radius=12, outline=INK, width=4)


def illu_dymer(img, d, box):
    """Dymer at first light: a five-storey block with one entrance sheared
    away, dust, a rescue ladder against the rubble."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (60, 70, 90), (190, 170, 140)),
              (x0, y0))
    for bx in (40, 130, 220):
        d.rectangle([x0 + bx, y0 + 34, x0 + bx + 76, y0 + 140],
                    fill=(185, 165, 135), outline=INK, width=3)
        for wy in range(48, 132, 26):
            for wx in (bx + 10, bx + 42):
                d.rectangle([x0 + wx, y0 + wy, x0 + wx + 22, y0 + wy + 14],
                            fill=(90, 80, 70))
    # collapsed entrance: rubble slope
    d.polygon([(x0 + 310, y0 + 140), (x0 + 310, y0 + 96), (x0 + 360, y0 + 60),
               (x0 + 440, y0 + 140)], fill=(150, 130, 105))
    d.polygon([(x0 + 330, y0 + 140), (x0 + 348, y0 + 108),
               (x0 + 380, y0 + 140)], fill=(120, 100, 80))
    for sx, sy, sr in [(350, 46, 18), (380, 30, 24), (412, 48, 16)]:
        d.ellipse([x0 + sx - sr, y0 + sy - sr, x0 + sx + sr, y0 + sy + sr],
                  fill=(200, 190, 170))
    d.line([(x0 + 290, y0 + 140), (x0 + 336, y0 + 92)], fill=RED, width=6)
    d.line([(x0 + 304, y0 + 122), (x0 + 316, y0 + 108)], fill=RED, width=4)
    # two drones high up, right side
    for dx, dy in [(400, 16), (436, 28)]:
        d.ellipse([x0 + dx - 6, y0 + dy - 4, x0 + dx + 6, y0 + dy + 4],
                  fill=INK)
        d.line([(x0 + dx - 14, y0 + dy), (x0 + dx + 14, y0 + dy)], fill=INK,
               width=2)
    d.text((x0 + 24, y0 + 10), "TOLL 11  \u00b7  BOY, 7, ALIVE",
           font=F(SANS_B, 24), fill=(255, 230, 160))


def illu_cop31(img, d, box):
    """Antalya, the morning after: a conference hall with empty desks, a
    screen where the fossil-fuel flame is crossed out, one delegate
    walking out."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (28, 44, 78), (90, 110, 140)),
              (x0, y0))
    # projection screen, top centre
    d.rectangle([x0 + 140, y0 + 10, x0 + 360, y0 + 64], fill=(235, 232, 220),
                outline=INK, width=3)
    d.ellipse([x0 + 180, y0 + 22, x0 + 222, y0 + 52], fill=(255, 140, 40))
    d.polygon([(x0 + 194, y0 + 52), (x0 + 201, y0 + 22), (x0 + 208, y0 + 52)],
              fill=(255, 200, 80))
    d.line([(x0 + 176, y0 + 18), (x0 + 226, y0 + 56)], fill=RED, width=6)
    d.text((x0 + 244, y0 + 28), "NO DEAL", font=F(SANS_B, 20),
           fill=RED)
    # rows of delegate desks, mostly empty
    for row, ry in enumerate((92, 116)):
        for j, cx in enumerate(range(30, 460, 72)):
            d.ellipse([x0 + cx + 18, y0 + ry - 16, x0 + cx + 34,
                       y0 + ry + 2],
                      fill=(220, 180, 140) if (j + row) % 3 else (90, 90, 100))
            d.rectangle([x0 + cx, y0 + ry, x0 + cx + 52, y0 + ry + 12],
                        fill=(150, 140, 120), outline=INK, width=2)
    # one delegate walking out, right
    d.ellipse([x0 + 430, y0 + 84, x0 + 452, y0 + 106], fill=(60, 50, 45))
    d.rectangle([x0 + 426, y0 + 104, x0 + 456, y0 + 140], fill=(40, 60, 110))


def illu_nato(img, d, box):
    """Berlin at night: NATO flag rows, a satellite with a red warning ring
    above, and a shield over the skyline."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (10, 20, 50), (60, 80, 120)),
              (x0, y0))
    # skyline
    for bx, bh in [(30, 50), (90, 70), (160, 44), (360, 60), (420, 46)]:
        d.rectangle([x0 + bx, y0 + 130 - bh, x0 + bx + 44, y0 + 130],
                    fill=(30, 34, 60))
        for wy in range(0, bh - 10, 12):
            d.rectangle([x0 + bx + 8, y0 + 130 - bh + wy, x0 + bx + 18,
                         y0 + 130 - bh + wy + 6], fill=(255, 220, 100))
    # satellite with warning ring, top right
    d.rectangle([x0 + 300, y0 + 22, x0 + 350, y0 + 42], fill=(200, 200, 210),
                outline=INK, width=2)
    d.rectangle([x0 + 270, y0 + 28, x0 + 300, y0 + 36], fill=(30, 60, 140))
    d.rectangle([x0 + 350, y0 + 28, x0 + 380, y0 + 36], fill=(30, 60, 140))
    d.ellipse([x0 + 288, y0 + 8, x0 + 362, y0 + 56], outline=RED, width=4)
    d.text((x0 + 24, y0 + 10), "BERLIN", font=F(SANS_B, 26),
           fill=(200, 220, 255))
    # shield over the skyline
    d.polygon([(x0 + 220, y0 + 84), (x0 + 260, y0 + 84), (x0 + 260, y0 + 112),
               (x0 + 240, y0 + 128), (x0 + 220, y0 + 112)], fill=(30, 60, 140),
              outline=GOLD, width=3)
    d.rectangle([x0, y0 + 130, x1, y1], fill=(20, 24, 40))


def illu_sanctions(img, d, box):
    """Brussels: a ring of gold EU stars on blue, a red ban sign over a
    Russian flag, and the package number 22."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (10, 30, 90), (30, 60, 130)),
              (x0, y0))
    # ring of stars, left
    cx, cy, r = 110, 70, 52
    for k in range(12):
        a = math.radians(k * 30 - 90)
        sx, sy = cx + r * math.cos(a), cy + r * math.sin(a)
        d.ellipse([x0 + sx - 5, y0 + sy - 5, x0 + sx + 5, y0 + sy + 5],
                  fill=GOLD)
    d.text((x0 + cx, y0 + cy), "22", font=F(SANS_B, 30), fill=WHITE,
           anchor="mm")
    # Russian flag with ban sign, right
    d.rectangle([x0 + 260, y0 + 30, x0 + 420, y0 + 110], fill=WHITE,
                outline=INK, width=3)
    d.rectangle([x0 + 260, y0 + 30, x0 + 420, y0 + 57], fill=(220, 220, 220))
    d.rectangle([x0 + 260, y0 + 57, x0 + 420, y0 + 84], fill=(30, 60, 160))
    d.rectangle([x0 + 260, y0 + 84, x0 + 420, y0 + 110], fill=(200, 40, 40))
    d.ellipse([x0 + 310, y0 + 18, x0 + 370, y0 + 122], outline=RED, width=6)
    d.line([(x0 + 318, y0 + 26), (x0 + 362, y0 + 114)], fill=RED, width=6)
    d.text((x0 + 24, y0 + 116), "PACKAGE 22", font=F(SANS_B, 20),
           fill=(220, 230, 255))


def illu_rabigh(img, d, box):
    """Rabigh refinery at night: flare stacks, a missile trail arcing in,
    and an interception burst above the towers."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (16, 16, 44), (90, 70, 110)),
              (x0, y0))
    # flare stacks
    for sx in (70, 150, 230, 330):
        d.rectangle([x0 + sx, y0 + 50, x0 + sx + 18, y0 + 130],
                    fill=(60, 60, 70), outline=INK, width=2)
        d.polygon([(x0 + sx - 6, y0 + 50), (x0 + sx + 9, y0 + 22),
                   (x0 + sx + 24, y0 + 50)], fill=(255, 140, 40))
        d.polygon([(x0 + sx, y0 + 50), (x0 + sx + 9, y0 + 32),
                   (x0 + sx + 18, y0 + 50)], fill=(255, 210, 60))
    # storage tanks
    for tx in (280, 380):
        d.ellipse([x0 + tx, y0 + 96, x0 + tx + 70, y0 + 130],
                  fill=(140, 140, 150), outline=INK, width=2)
    # missile trail + burst (kept clear of the RABIGH label, top left)
    d.line([(x0 + 150, y0 + 12), (x0 + 230, y0 + 44), (x0 + 300, y0 + 66)],
           fill=(255, 240, 160), width=4)
    for ang in range(0, 360, 45):
        r = math.radians(ang)
        d.line([(x0 + 300, y0 + 66),
                (x0 + 300 + 24 * math.cos(r), y0 + 66 + 24 * math.sin(r))],
               fill=(255, 200, 60), width=4)
    d.rectangle([x0, y0 + 130, x1, y1], fill=(20, 20, 28))
    d.text((x0 + 24, y0 + 8), "RABIGH", font=F(SANS_B, 24),
           fill=(255, 220, 150))


def illu_factory(img, d, box):
    """Candy factory at night: long shed roof, flames through the windows,
    smoke columns, a fire engine's ladder."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (40, 30, 30), (140, 60, 30)),
              (x0, y0))
    d.rectangle([x0 + 70, y0 + 70, x0 + 330, y0 + 140], fill=(170, 160, 150))
    d.rectangle([x0 + 70, y0 + 70, x0 + 330, y0 + 92], fill=(120, 40, 40))
    for wx in (100, 170, 240, 300):
        d.rectangle([x0 + wx, y0 + 100, x0 + wx + 22, y0 + 126],
                    fill=(255, 210, 90))
    for fx, fh in [(120, 60), (180, 84), (250, 64), (310, 50)]:
        d.polygon([(x0 + fx - 18, y0 + 74), (x0 + fx, y0 + 74 - fh),
                   (x0 + fx + 18, y0 + 74)], fill=(255, 120, 20))
        d.polygon([(x0 + fx - 9, y0 + 74), (x0 + fx, y0 + 74 - fh // 2),
                   (x0 + fx + 9, y0 + 74)], fill=(255, 210, 60))
    for sx, sy, sr in [(380, 30, 20), (410, 52, 26), (440, 28, 18)]:
        d.ellipse([x0 + sx - sr, y0 + sy - sr, x0 + sx + sr, y0 + sy + sr],
                  fill=(70, 66, 66))
    # candy stripe on the shed wall
    for sx in range(76, 326, 30):
        d.line([(x0 + sx, y0 + 128), (x0 + sx + 14, y0 + 140)],
               fill=(220, 60, 90), width=5)


def illu_belgium(img, d, box):
    """Brussels, strike day: an empty departures board flashing CANCELLED,
    a picket line with placards, and a grounded jet silhouette."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (60, 70, 90), (170, 170, 160)),
              (x0, y0))
    # departures board
    d.rectangle([x0 + 30, y0 + 16, x0 + 230, y0 + 64], fill=DARK,
                outline=WHITE, width=2)
    d.text((x0 + 130, y0 + 26), "CANCELLED", font=F(SANS_B, 24),
           fill=(255, 90, 90), anchor="ma")
    d.text((x0 + 130, y0 + 46), "ALL FLIGHTS", font=F(SANS_B, 14),
           fill=WHITE, anchor="ma")
    # grounded jet
    d.ellipse([x0 + 280, y0 + 40, x0 + 430, y0 + 62], fill=(230, 230, 235),
              outline=INK, width=2)
    d.polygon([(x0 + 420, y0 + 44), (x0 + 460, y0 + 34), (x0 + 460, y0 + 54)],
              fill=(200, 200, 205))
    d.rectangle([x0 + 320, y0 + 26, x0 + 360, y0 + 42], fill=(40, 80, 140))
    # picket line
    for px, col in [(60, (200, 40, 40)), (170, (30, 60, 140)),
                    (280, (40, 120, 60)), (390, (200, 40, 40))]:
        d.ellipse([x0 + px + 12, y0 + 84, x0 + px + 32, y0 + 104],
                  fill=(220, 180, 140))
        d.rectangle([x0 + px + 8, y0 + 102, x0 + px + 36, y0 + 140],
                    fill=col)
        d.line([(x0 + px + 22, y0 + 78), (x0 + px + 22, y0 + 104)], fill=INK,
               width=3)
        d.rectangle([x0 + px - 6, y0 + 66, x0 + px + 50, y0 + 80], fill=WHITE,
                    outline=INK, width=2)
    d.rectangle([x0, y0 + 130, x1, y1], fill=(90, 95, 100))


def illu_bitcoin(img, d, box):
    """A chart that spikes, then fades: green up to $64,500 on the Huang
    news, red back down toward $61,100, with the coin."""
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=DARK)
    pts = [(x0 + 30, y0 + 104), (x0 + 110, y0 + 92), (x0 + 190, y0 + 96),
           (x0 + 270, y0 + 34), (x0 + 350, y0 + 62), (x0 + 420, y0 + 78)]
    d.line(pts, fill=(120, 220, 140), width=6, joint="curve")
    d.line([(x0 + 270, y0 + 34), (x0 + 350, y0 + 62), (x0 + 420, y0 + 78)],
           fill=(255, 90, 90), width=6, joint="curve")
    d.ellipse([x0 + 258, y0 + 22, x0 + 282, y0 + 46], fill=(120, 220, 140))
    d.ellipse([x0 + 380, y0 + 70, x0 + 440, y0 + 130], fill=GOLD,
              outline=(140, 100, 20), width=3)
    d.text((x0 + 410, y0 + 100), "B", font=F(SANS_B, 40), fill=(120, 80, 10),
           anchor="mm")
    d.text((x0 + 24, y0 + 10), "$64,500", font=F(SANS_B, 28),
           fill=(120, 220, 140))
    d.text((x0 + 300, y0 + 8), "$61,100", font=F(SANS_B, 26),
           fill=(255, 120, 120))

def illu_democrats(img, d, box):
    """The Capitol at dusk: dome and columns, a red-and-blue seat bar
    reading 258, and a rising sun behind it."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (200, 160, 110), (60, 70, 110)),
              (x0, y0))
    # sun disc behind the dome
    d.ellipse([x0 + 150, y0 + 8, x0 + 230, y0 + 88], fill=(255, 210, 120))
    # dome
    d.polygon([(x0 + 150, y0 + 40), (x0 + 190, y0 + 8), (x0 + 230, y0 + 40)],
              fill=(230, 230, 225))
    d.rectangle([x0 + 158, y0 + 40, x0 + 222, y0 + 60], fill=(230, 230, 225))
    d.rectangle([x0 + 120, y0 + 60, x0 + 260, y0 + 66], fill=(210, 210, 205))
    # columns
    for cx in range(120, 260, 28):
        d.rectangle([x0 + cx, y0 + 66, x0 + cx + 14, y0 + 110],
                    fill=(220, 220, 215), outline=INK, width=2)
    d.rectangle([x0 + 110, y0 + 110, x0 + 270, y0 + 118], fill=(200, 200, 195))
    # seat bar: 258 of 435 in blue
    d.rectangle([x0 + 290, y0 + 70, x0 + 370, y0 + 96], fill=(180, 40, 40),
                outline=INK, width=2)
    d.rectangle([x0 + 290, y0 + 70, x0 + 338, y0 + 96], fill=(30, 60, 160))
    d.text((x0 + 330, y0 + 98), "258", font=F(SERIF_B, 30), fill=INK,
           anchor="ma")


def illu_fury(img, d, box):
    """A boxing ring under warm lights: ropes, two gloves hanging, and a
    documentary camera on a tripod — the confession, not the fight."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (40, 30, 30), (140, 90, 50)),
              (x0, y0))
    # ring ropes
    for ry in (60, 84, 108):
        d.line([(x0 + 20, y0 + ry), (x0 + 240, y0 + ry)], fill=WHITE, width=4)
    for px in (20, 130, 240):
        d.line([(x0 + px, y0 + 48), (x0 + px, y0 + 120)], fill=INK, width=5)
    # two gloves hanging on the ropes
    for gx, gy, col in [(80, 66, (200, 40, 40)), (170, 66, (30, 60, 160))]:
        d.ellipse([x0 + gx, y0 + gy, x0 + gx + 44, y0 + gy + 44], fill=col,
                  outline=INK, width=2)
        d.rectangle([x0 + gx + 14, y0 + gy + 40, x0 + gx + 30, y0 + gy + 56],
                    fill=col, outline=INK, width=2)
    # camera on tripod, right
    d.rectangle([x0 + 280, y0 + 44, x0 + 340, y0 + 76], fill=(40, 40, 48),
                outline=INK, width=2)
    d.ellipse([x0 + 340, y0 + 52, x0 + 360, y0 + 68], fill=(120, 160, 200),
              outline=INK, width=2)
    d.line([(x0 + 310, y0 + 76), (x0 + 280, y0 + 130)], fill=INK, width=4)
    d.line([(x0 + 310, y0 + 76), (x0 + 310, y0 + 130)], fill=INK, width=4)
    d.line([(x0 + 310, y0 + 76), (x0 + 340, y0 + 130)], fill=INK, width=4)


def illu_mercury(img, d, box):
    """Mercury's cratered crescent, the sun's glare, and BepiColombo with its
    two solar wings — the orbit entry that now needs software checks."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (6, 6, 16), (60, 40, 20)),
              (x0, y0))
    d.ellipse([x0 + 300, y0 + 12, x0 + 350, y0 + 62], fill=(255, 230, 150))
    d.ellipse([x0 + 308, y0 + 20, x0 + 342, y0 + 54], fill=(255, 200, 90))
    d.ellipse([x0 + 30, y0 + 60, x0 + 230, y0 + 190], fill=(150, 135, 120))
    for cx, cy, cr in [(90, 110, 12), (140, 92, 8), (180, 120, 14),
                       (120, 140, 7)]:
        d.ellipse([x0 + cx - cr, y0 + cy - cr, x0 + cx + cr, y0 + cy + cr],
                  fill=(110, 98, 86))
    # spacecraft: bus + wings, one wing tilted (the glitch)
    d.rectangle([x0 + 190, y0 + 44, x0 + 240, y0 + 76], fill=(200, 200, 210),
                outline=INK, width=2)
    d.rectangle([x0 + 130, y0 + 52, x0 + 190, y0 + 68], fill=(30, 60, 140))
    d.polygon([(x0 + 240, y0 + 52), (x0 + 300, y0 + 40), (x0 + 300, y0 + 62),
               (x0 + 240, y0 + 68)], fill=(30, 60, 140))
    d.text((x0 + 24, y0 + 10), "SOFTWARE CHECK", font=F(SANS_B, 20),
           fill=(255, 220, 150))


def illu_quake(img, d, box):
    """A seismograph trace spiking M6.5, and a depth arrow plunging 598 km
    into the mantle — the quake nobody felt."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (30, 40, 70), (120, 130, 150)),
              (x0, y0))
    # seismograph paper
    d.rectangle([x0 + 20, y0 + 16, x0 + 360, y0 + 84], fill=(240, 238, 228),
                outline=INK, width=2)
    pts = [(x0 + 30, y0 + 50), (x0 + 70, y0 + 50), (x0 + 90, y0 + 46),
           (x0 + 110, y0 + 54), (x0 + 130, y0 + 50), (x0 + 150, y0 + 50),
           (x0 + 170, y0 + 22), (x0 + 185, y0 + 78), (x0 + 200, y0 + 50),
           (x0 + 230, y0 + 46), (x0 + 260, y0 + 54), (x0 + 350, y0 + 50)]
    d.line(pts, fill=RED, width=3, joint="curve")
    d.text((x0 + 40, y0 + 22), "M6.5", font=F(SANS_B, 26), fill=RED)
    # depth arrow
    d.line([(x0 + 330, y0 + 96), (x0 + 330, y0 + 130)], fill=WHITE, width=4)
    d.polygon([(x0 + 330, y0 + 130), (x0 + 318, y0 + 114),
               (x0 + 342, y0 + 114)], fill=WHITE)
    d.text((x0 + 190, y0 + 104), "598 km DEEP", font=F(SANS_B, 22),
           fill=WHITE, anchor="ma")
    d.rectangle([x0, y0 + 132, x1, y1], fill=(40, 50, 70))


def illu_cricket(img, d, box):
    """Wellington at dusk: batsman mid-drive, stumps, and the scoreboard
    reading 720/9 — the draw that saved New Zealand."""
    x0, y0, x1, y1 = box
    img.paste(gradient(x1 - x0, y1 - y0, (200, 140, 80), (90, 60, 40)),
              (x0, y0))
    d.rectangle([x0, y0 + 108, x1, y1], fill=(60, 120, 60))
    # stumps
    for sx in (60, 72, 84):
        d.rectangle([x0 + sx, y0 + 78, x0 + sx + 5, y0 + 108], fill=(240, 220,
                    160))
    d.rectangle([x0 + 60, y0 + 72, x0 + 89, y0 + 78], fill=(240, 220, 160))
    # batsman: pads, bat swung high
    d.ellipse([x0 + 150, y0 + 44, x0 + 172, y0 + 66], fill=(220, 180, 140))
    d.rectangle([x0 + 148, y0 + 64, x0 + 174, y0 + 104], fill=WHITE)
    d.line([(x0 + 172, y0 + 74), (x0 + 222, y0 + 28)], fill=(200, 160, 100),
           width=7)
    # ball in flight
    d.ellipse([x0 + 244, y0 + 24, x0 + 262, y0 + 42], fill=(200, 40, 40))
    # scoreboard
    d.rectangle([x0 + 280, y0 + 74, x0 + 372, y0 + 116], fill=DARK,
                outline=WHITE, width=2)
    d.text((x0 + 326, y0 + 82), "720/9", font=F(SANS_B, 24), fill=GOLD,
           anchor="ma")
    d.text((x0 + 326, y0 + 100), "DRAW", font=F(SANS_B, 13), fill=WHITE,
           anchor="ma")


# ---- world map -----------------------------------------------------------

CONTINENTS = [
    [(-170, 70), (-140, 70), (-120, 72), (-95, 80), (-80, 73), (-60, 60),
     (-55, 47), (-70, 42), (-75, 35), (-80, 26), (-90, 21), (-97, 16),
     (-105, 20), (-115, 30), (-125, 40), (-125, 49), (-140, 60), (-165, 60)],
    [(-80, 10), (-60, 5), (-50, 0), (-35, -8), (-40, -20), (-50, -30),
     (-60, -40), (-70, -55), (-75, -35), (-80, -15)],
    [(-10, 35), (10, 37), (30, 32), (35, 28), (43, 12), (51, 10), (40, -5),
     (35, -20), (20, -35), (15, -20), (10, -5), (-5, 5), (-17, 15),
     (-17, 25)],
    [(-10, 36), (-9, 43), (0, 48), (-5, 50), (5, 53), (8, 57), (18, 56),
     (21, 55), (28, 60), (30, 70), (40, 68), (45, 55), (40, 45), (30, 36),
     (23, 36), (19, 40), (12, 44), (3, 42), (-2, 37)],
    [(40, 68), (60, 70), (90, 75), (120, 77), (160, 70), (180, 66),
     (162, 60), (158, 52), (142, 45), (135, 35), (127, 35), (120, 30),
     (110, 20), (105, 10), (100, 8), (95, 16), (90, 22), (80, 8), (75, 20),
     (65, 25), (55, 25), (50, 29), (43, 12), (40, 30)],
    [(113, -22), (114, -30), (120, -34), (130, -32), (140, -38), (150, -37),
     (153, -27), (146, -19), (142, -11), (135, -12), (130, -13), (122, -17)],
]

# (story number, longitude, latitude). 11 and 29 are markets (everywhere)
# and 14 is at Mercury, so none of those three has an Earth pin.
PINS = [
    (1, -121.96, 37.35), (2, 20.1, 32.1), (3, 56.5, 26.5),
    (4, 30.3, 50.8), (5, 30.7, 36.9), (6, 13.4, 52.5),
    (7, 4.35, 50.85), (8, 39.0, 22.8), (9, 106.2, -6.0),
    (10, 4.35, 50.85), (12, -77.0, 38.9), (13, -0.1, 51.5),
    (15, 172.3, -13.6), (16, 174.8, -41.3), (17, -0.1, 51.5),
    (18, -77.0, 38.9), (19, 30.3, 59.9), (20, 32.5, 15.6),
    (21, 34.5, 31.5), (22, 35.2, 31.9), (23, -77.5, 37.5),
    (24, 103.8, 1.35), (25, -122.4, 37.8), (26, -97.7, 30.3),
    (27, 5.7, 58.9), (28, -0.1, 51.5), (30, -77.0, 38.9),
    (31, 77.2, 28.6), (32, -3.7, 40.4), (33, 50.9, 34.6),
    (34, 15.6, -1.2), (35, 68.8, 38.6), (36, 28.7, 7.8),
    (37, 7.0, 9.0), (38, 12.6, 55.7), (39, -74.1, 4.7),
    (40, 30.06, -1.94), (41, 12.5, 41.9), (42, -47.9, -15.8),
    (43, -0.3, 51.5), (44, 139.7, 35.7),
]
# Marker nudges (px) for pins that would otherwise sit on top of each
# other; a thin leader line joins the marker to its true spot.
PIN_OFFSETS = {
    7: (-38, -26), 10: (36, 24), 12: (-40, -28), 13: (-48, -28),
    17: (42, -32), 18: (38, -26), 21: (-34, 22), 22: (34, -22),
    23: (40, 24), 28: (48, 22), 30: (-38, 28), 43: (-44, 28),
}


def world_map(img, d, box):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=14, fill=SEA, outline=INK, width=4)
    d.text((x0 + 20, y0 + 10), "WHERE IT HAPPENED",
           font=F(SANS_B, 30), fill=GOLD)
    mx0, my0, mx1, my1 = x0 + 16, y0 + 50, x1 - 16, y1 - 44
    mw, mh = mx1 - mx0, my1 - my0

    def proj(lon, lat):
        return (mx0 + (lon + 180) / 360 * mw,
                my0 + (90 - lat) / 180 * mh)

    for cont in CONTINENTS:
        d.polygon([proj(lon, lat) for lon, lat in cont],
                  fill=LAND, outline=(200, 210, 190))
    for n, lon, lat in PINS:
        px, py = proj(lon, lat)
        dx, dy = PIN_OFFSETS.get(n, (0, 0))
        if (dx, dy) != (0, 0):
            d.line([(px, py), (px + dx, py + dy)], fill=WHITE, width=3)
            px, py = px + dx, py + dy
        d.ellipse([px - 12, py - 12, px + 12, py + 12], fill=RED,
                  outline=WHITE, width=2)
        d.text((px, py), str(n), font=F(SANS_B, 17), fill=WHITE, anchor="mm")
    d.text((x0 + 20, y1 - 36),
           "11, 29: markets \u2014 everywhere.  14: Mercury.",
           font=F(SANS, 20), fill=(215, 220, 230))


BRIEFS = [
    (17, "NHS starts AI breast-screening trial for 700,000 women \u2014 BBC"),
    (18, "US sanctions Iranian 'shadow banking' networks \u2014 Al Jazeera"),
    (19, "Sparta II reaches St Petersburg under tow \u2014 Straits Times"),
    (20, "UN reports Monday: Sunday strikes killed 4 in Khartoum \u2014 OCHA"),
    (21, "Oxfam: Gaza a 'toxic wasteland'; UN worker killed \u2014 BBC"),
    (22, "Eisenkot calls settler attacks 'Jewish terrorism' \u2014 ANSA"),
    (23, "States sue Musk firms over Grok sexualised images \u2014 CNBC"),
    (24, "US blacklists Megaspeed; $1.1bn NK crypto seizure \u2014 BBC"),
    (25, "Anthropic mathematician posts claimed Riemann proof \u2014 Phys.org"),
    (26, "CrowdStrike to buy Zscaler for $44bn \u2014 CNBC"),
    (27, "ConocoPhillips exits Norway in $4.43bn deal \u2014 OilPrice"),
    (28, "Capita shares plunge 70% as boss quits \u2014 BBC"),
    (29, "European gas +8.6%; oil slides, Brent $86.72 \u2014 OilPrice"),
    (30, "Trump calls Putin 'my friend'; DNI defends remark \u2014 PBS"),
    (31, "India pledges $1.6bn as Nepal PM wraps visit \u2014 Al Jazeera"),
    (32, "Spain's Supreme Court grants amnesty to Puigdemont \u2014 CNN"),
    (33, "Iran flogs singer Ahmadi 74 lashes over hijab \u2014 BBC"),
    (34, "Kenya and DR Congo agree to restore full ties \u2014 BBC"),
    (35, "Tajikistan begins withdrawing from the ICC \u2014 UPI"),
    (36, "Attack kills 24 civilians in South Sudan \u2014 CTV"),
    (37, "Boat carrying mourners capsizes in Nigeria; 24 dead \u2014 BBC"),
    (38, "Schools in Germany and Denmark get bomb threats \u2014 DW"),
    (39, "Colombia asks X to suspend ex-president Petro \u2014 MercoPress"),
    (40, "Five EU states back Rwanda deportation centres \u2014 Al Jazeera"),
    (41, "WFP: wars put food aid for 7.3m more at risk \u2014 Straits Times"),
    (42, "Brazil cuts 2027 growth forecast to 1.8% \u2014 MercoPress"),
    (43, "Brentford beat 10-man Everton 4\u20130 \u2014 Sky Sports"),
    (44, "Tamagotchi marks its 30th anniversary \u2014 Japan Times"),
]


def briefs_band(d, x0, y0, x1, y1):
    d.text((x0, y0 + 6), "IN BRIEF  \u2014  17\u201344",
           font=F(SERIF_B, 32), fill=INK)
    hline(d, x0, y0 + 50, x1, RED, 4)
    col_w = (x1 - x0 - 40) / 2
    fnt = F(SANS, 19)
    for i, (n, text) in enumerate(BRIEFS):
        col = i // 14
        row = i % 14
        bx = x0 + col * (col_w + 40)
        by = y0 + 60 + row * 20
        line = f"{n}. {text}"
        assert d.textlength(line, font=fnt) <= col_w, \
            "brief overflow: " + line
        d.text((bx, by), line, font=fnt, fill=INK)


EXCLUDED_LEFT = [
    "COP31 ends without a deal \u2014 Sunday 22 Nov",
    "BepiColombo enters Mercury orbit \u2014 Friday 21 Nov",
    "Alcaraz wins his first ATP Finals \u2014 Sunday 22 Nov",
    "Liverpool 4\u20130 Manchester United \u2014 Sunday 22 Nov",
    "Hunger Games $225m opening \u2014 Sunday 22 Nov",
]
EXCLUDED_RIGHT = [
    "Verstappen wins the Las Vegas GP \u2014 Saturday 21 Nov",
    "Euro area inflation 4.0% \u2014 OCTOBER data, 18 Nov",
    "'Chapo Isidro' captured in Sinaloa \u2014 Sunday 22 Nov",
    "Shenzhen summit (Trump\u2013Xi\u2013Putin) \u2014 20\u201321 Nov",
    "Lewis Pugh's Hormuz swim \u2014 Friday 21 Nov",
]


def date_check(d, box):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=14, fill=(232, 226, 208), outline=INK,
                        width=4)
    d.text((x0 + 24, y0 + 10), "DATE CHECK \u2014 LEFT OUT ON PURPOSE",
           font=F(SANS_B, 28), fill=DARKRED)
    fnt = F(SANS, 22)
    for i, t in enumerate(EXCLUDED_LEFT):
        d.text((x0 + 24, y0 + 48 + i * 22), "\u2715  " + t, font=fnt, fill=INK)
    for i, t in enumerate(EXCLUDED_RIGHT):
        d.text((x0 + 1010, y0 + 48 + i * 22), "\u2715  " + t, font=fnt,
               fill=INK)
    d.text((x0 + 24, y0 + 162),
           "Every story on this page happened, or was first reported, on "
           "Monday 23 November 2026.",
           font=F(SANS_B, 23), fill=INK)
    d.text((x0 + 24, y0 + 190),
           "Sources: Reuters \u00b7 AP \u00b7 AFP \u00b7 BBC \u00b7 CNBC "
           "\u00b7 CBS \u00b7 Al Jazeera \u00b7 France 24 \u00b7 Guardian "
           "\u00b7 SCMP \u00b7 OilPrice \u00b7 USGS \u00b7 ESA \u00b7 "
           "OCHA \u00b7 IANS \u00b7 PBS \u00b7 UPI \u00b7 DW",
           font=F(SANS, 18), fill=GREY)


def main():
    img = Image.new("RGB", (CANVAS, CANVAS), PAPER)
    d = ImageDraw.Draw(img, "RGBA")
    masthead(d)
    stats_band(d, 250, 342)
    # three heroes
    hero(img, d, (EDGE, 354, 700, 710), 1, "SANTA CLARA \u2014 TECH",
         "Huang returns as Nvidia chief; shares soar 31%",
         "Board reinstates him 11 days after his exit; S&P jumps 4.7%, "
         "best day since April 2025. \u2014 CNBC",
         draw_nvidia)
    hero(img, d, (716, 354, 1380, 710), 2, "BENGHAZI \u2014 WAR",
         "Zelenskyy: sea drones sank Russian corvette off Libya",
         "Seven drones sank the Merkury, Kyiv says; a cargo ship hit, "
         "10 hurt. \u2014 BBC",
         draw_merkury)
    hero(img, d, (1396, 354, 2012, 710), 3, "HORMUZ \u2014 GULF",
         "Iran vows 'all means' against US blockade",
         "Trump: Iran fired its heaviest missile week in a year; "
         "Tehran unveils a missile city. \u2014 CBS",
         draw_gulf)
    # panel row 1: four panels
    xs1 = [36, 534, 1032, 1530]
    xe1 = [518, 1016, 1514, 2012]
    panel(img, d, (xs1[0], 722, xe1[0], 960), 4, "DYMER \u2014 WAR",
          "Kyiv toll climbs as boy, 7, pulled alive",
          "11 dead; boy, 7, and woman, 79, freed from the rubble "
          "after 22 hours.",
          "BBC", illu_dymer)
    panel(img, d, (xs1[1], 722, xe1[1], 960), 5, "ANTALYA \u2014 CLIMATE",
          "COP31 failure: the morning after",
          "China: 'disappointing'; Albanese defends Bowen.",
          "BBC", illu_cop31)
    panel(img, d, (xs1[2], 722, xe1[2], 960), 6, "BERLIN \u2014 NATO",
          "NATO vows to defend 'every inch'",
          "Rutte warns on space; Russia 'may orbit a nuclear weapon'.",
          "SCMP", illu_nato)
    panel(img, d, (xs1[3], 722, xe1[3], 960), 7, "BRUSSELS \u2014 EU",
          "EU proposes 22nd Russia sanctions",
          "Flags banned at EU sport; visas barred for ex-combatants.",
          "Guardian", illu_sanctions)
    # panel row 2: four panels
    panel(img, d, (xs1[0], 972, xe1[0], 1210), 8, "RABIGH \u2014 WAR",
          "Houthis claim Rabigh refinery hit; 17 killed",
          "Saudi strikes kill 17 telecom workers in Lahj, Houthis say.",
          "CNBC", illu_rabigh)
    panel(img, d, (xs1[1], 972, xe1[1], 1210), 9, "BANTEN \u2014 FIRE",
          "Candy factory fire kills 24, 34 missing",
          "Toll rises Monday; DNA needed to identify victims.",
          "Guardian", illu_factory)
    panel(img, d, (xs1[2], 972, xe1[2], 1210), 10, "BELGIUM \u2014 STRIKE",
          "Strike shuts Belgian airports",
          "Thousands march in Brussels; PM sets a year-end budget "
          "deadline.",
          "France 24", illu_belgium)
    panel(img, d, (xs1[3], 972, xe1[3], 1210), 11, "CRYPTO \u2014 MARKETS",
          "Bitcoin spikes to $64,500, then fades to $61,100",
          "Huang rally lifts it, then fades; ETFs shed $1.79bn.",
          "Bitcoin Insider", illu_bitcoin)
    # panel row 3: five panels
    xs3 = [36, 434, 832, 1230, 1628]
    xe3 = [418, 816, 1214, 1612, 2012]
    panel(img, d, (xs3[0], 1222, xe3[0], 1460), 12, "WASHINGTON \u2014 POLITICS",
          "Democrats reach 258 House seats",
          "Largest majority since 1992; Senate 56\u201344.",
          "BBC", illu_democrats, hsize=28, dsize=21)
    panel(img, d, (xs3[1], 1222, xe3[1], 1460), 13, "LONDON \u2014 BOXING",
          "Fury reveals his diagnosis",
          "Fury tells of the darkness after his 2015 title win.",
          "TMZ", illu_fury, hsize=28, dsize=21)
    panel(img, d, (xs3[2], 1222, xe3[2], 1460), 14, "MERCURY \u2014 SPACE",
          "BepiColombo needs software checks",
          "ESA flags a software caveat after the orbit entry.",
          "Reuters", illu_mercury, hsize=28, dsize=21)
    panel(img, d, (xs3[3], 1222, xe3[3], 1460), 15, "VANUATU \u2014 QUAKE",
          "M6.5 quake strikes 598 km deep",
          "Deep focus, no damage, no tsunami.",
          "USGS", illu_quake, hsize=28, dsize=21)
    panel(img, d, (xs3[4], 1222, xe3[4], 1460), 16, "WELLINGTON \u2014 CRICKET",
          "India's 720/9 ends in a Wellington draw",
          "Pant's 128 sets a record; NZ survive Day 5 on 239/5.",
          "IANS", illu_cricket, hsize=28, dsize=21)
    # map + briefs band
    world_map(img, d, (EDGE, 1472, 560, 1816))
    briefs_band(d, 580, 1472, 2012, 1816)
    # date check footer
    date_check(d, (EDGE, 1828, 2012, 2036))
    small = img.resize((1024, 1024), Image.LANCZOS)
    small.save("entry.png", optimize=True)
    print("wrote entry.png")


if __name__ == "__main__":
    main()
