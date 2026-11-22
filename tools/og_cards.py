#!/usr/bin/env python3
"""Draw the 1200x630 link-preview cards (iMessage, WhatsApp, Slack) for the docs site.

Usage: og_cards.py DOCS_DIR

Writes DOCS_DIR/assets/og/<name>.png for every page in DOCS_DIR/_nav.txt, plus
root.png for the system notebook at the site root. A nav title "Kicker — Title"
puts the kicker above the title. SUBTITLES below adds a line to chosen cards.
Needs Pillow and the Noto/DejaVu fonts (fonts-noto-core, fonts-dejavu-core).
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
BG, INK, MUTED, FAINT, ACCENT = "#f7f6f2", "#242424", "#5f5d58", "#8a8780", "#2d5be3"
FONTS = "/usr/share/fonts/truetype"
SERIF_BOLD = f"{FONTS}/noto/NotoSerif-Bold.ttf"
SANS = f"{FONTS}/noto/NotoSans-Regular.ttf"
GLYPHS = f"{FONTS}/dejavu/DejaVuSans.ttf"

SUBTITLES = {
    "index": "v38 final · 2,588 games · 0.554 · 21 Nov 2026",
    "status-20261120": "Deployed, retired, rejected: every component and experiment",
    "timeline": "Every arena version, what changed, and what happened",
    "root": "Fog of War chess bot · Obscuro-style search in C · arena v38",
}
TITLES = {
    "index": "A Fog of War chess bot, documented over time",
    "root": "How IAmAVirus plays chess in the dark",
}


def wrap(draw, text, font, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def board(draw, x0, y0, cell):
    """White's view on move 1: ranks 5-8 in fog, ranks 1-4 visible."""
    glyph = ImageFont.truetype(GLYPHS, int(cell * 0.72))
    back = "♖♘♗♕♔♗♘♖"
    for r in range(8):  # r = 0 is rank 8
        for f in range(8):
            x, y = x0 + f * cell, y0 + r * cell
            if r < 4:
                draw.rectangle([x, y, x + cell, y + cell], fill="#e4e3de")
                for k in range(-cell, cell, 9):  # diagonal hatch
                    draw.line([x + max(k, 0), y + max(-k, 0), x + min(k + cell, cell), y + min(cell, cell - k)], fill="#d3d1cb", width=3)
            else:
                draw.rectangle([x, y, x + cell, y + cell], fill="#ffffff" if (r + f) % 2 == 0 else "#ecebe6")
            piece = back[f] if r == 7 else ("♙" if r == 6 else "")
            if piece:
                draw.text((x + cell / 2, y + cell / 2 + 2), piece, font=glyph, fill=INK, anchor="mm")
    draw.rectangle([x0, y0, x0 + 8 * cell, y0 + 8 * cell], outline="#cfcdc6", width=2)


def card(path, kicker, title, subtitle):
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    board(d, 712, 107, 52)
    left, width = 72, 590
    label = ImageFont.truetype(SANS, 22)
    d.text((left, 70), "IAMAVIRUS  ·  MIT 6.7980 FOG OF WAR", font=label, fill=MUTED)
    d.rectangle([left, 108, left + 64, 112], fill=ACCENT)
    y = 140
    if kicker:
        d.text((left, y), kicker, font=ImageFont.truetype(SANS, 30), fill=ACCENT)
        y += 52
    for size in (64, 58, 52, 46, 42):
        font = ImageFont.truetype(SERIF_BOLD, size)
        lines = wrap(d, title, font, width)
        if len(lines) <= 3:
            break
    for line in lines:
        d.text((left, y), line, font=font, fill=INK)
        y += int(size * 1.18)
    if subtitle:
        y += 14
        for line in wrap(d, subtitle, ImageFont.truetype(SANS, 26), width):
            d.text((left, y), line, font=ImageFont.truetype(SANS, 26), fill=MUTED)
            y += 36
    d.text((left, 552), "htansetiawan.github.io/iamavirus", font=label, fill=FAINT)
    img.save(path, optimize=True)
    return os.path.getsize(path)


def main():
    docs = sys.argv[1]
    out = os.path.join(docs, "assets", "og")
    os.makedirs(out, exist_ok=True)
    pages = [("root", "")]
    for line in open(os.path.join(docs, "_nav.txt"), encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#"):
            name, title = line.split(":", 1)
            pages.append((name.strip(), title.strip()))
    for name, nav_title in pages:
        kicker, title = ("", nav_title)
        if " — " in nav_title:
            kicker, title = nav_title.split(" — ", 1)
        title = TITLES.get(name, title)
        size = card(os.path.join(out, name + ".png"), kicker, title, SUBTITLES.get(name, ""))
        print(f"{name}.png {size // 1024} KB")


if __name__ == "__main__":
    main()
