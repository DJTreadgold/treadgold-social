"""
Treadgold Finance review-card image generator.

Reusable testimonial-card pipeline. Reads posts/reviews.json and outputs
branded PNGs for each review (landscape 1200x628 + square 1080x1080).

reviews.json schema:
{
  "reviews": [
    {
      "slug": "natalie_danielle",      # output filename stem
      "quote": "Danielle is great ...", # the review text (verbatim, may be trimmed)
      "name": "Natalie",                # reviewer display name
      "context": "Car loan with Danielle"  # short attribution line under the name
    }
  ]
}

Layout (curved split, adopted 2 Oct 2026):
  - Bone field above a shallow arc, black field below, gold arc on the seam
  - Short gold bar top-left
  - Header row: Google "G" + 5 gold stars + "GOOGLE REVIEW" (gold) + grey divider
  - Large white quote (Montserrat-Bold, shrink-to-fit, opening/closing curly quotes)
  - Gold "— Name" + grey context line
  - Full-width gold rule above footer
  - Treadgold logo bottom-left + URL bottom-right

Reuses brand helpers from treadgold_social_template.py (same dir).
"""

import json
import math
import sys
from pathlib import Path
from PIL import Image, ImageDraw

from treadgold_social_template import (
    GOLD, BLACK, WHITE, GREY, URL_TEXT,
    ensure_fonts, font_black, font_bold, font_regular,
    measure, wrap_to_width, prepare_logo, LANCZOS,
)

# Google brand colours for the "G"
G_BLUE = (66, 133, 244)
G_RED = (234, 67, 53)
G_YELLOW = (251, 188, 5)
G_GREEN = (52, 168, 83)


def draw_star(draw, cx, cy, r_outer, fill):
    """Draw a 5-point star centred at (cx, cy) with given outer radius."""
    r_inner = r_outer * 0.42
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def draw_google_g(size):
    """Render a clean four-colour Google 'G' mark as an RGBA image of height=size.
    Approximation drawn from arcs — not Google's copyrighted asset file."""
    SS = 4  # supersample for smooth arcs
    d = size * SS
    img = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    dr = ImageDraw.Draw(img)
    cx = cy = d / 2
    outer = d / 2
    thick = d * 0.22          # ring thickness
    inner = outer - thick
    bbox_o = [cx - outer, cy - outer, cx + outer, cy + outer]

    dr.pieslice(bbox_o, 270, 360, fill=G_RED)
    dr.pieslice(bbox_o, 180, 270, fill=G_RED)
    dr.pieslice(bbox_o, 90, 180, fill=G_YELLOW)
    dr.pieslice(bbox_o, 0, 90, fill=G_BLUE)
    dr.pieslice(bbox_o, 130, 180, fill=G_YELLOW)
    dr.pieslice(bbox_o, 90, 150, fill=G_GREEN)
    dr.pieslice(bbox_o, 30, 90, fill=G_BLUE)

    bbox_i = [cx - inner, cy - inner, cx + inner, cy + inner]
    dr.ellipse(bbox_i, fill=(0, 0, 0, 0))

    dr.pieslice(bbox_o, -16, 14, fill=(0, 0, 0, 0))

    bar_h = thick
    bar_top = cy - bar_h / 2
    dr.rectangle([cx, bar_top, cx + inner + thick * 0.15, bar_top + bar_h], fill=G_BLUE)

    img = img.resize((size, size), LANCZOS)
    return img


# ---- Curved-split palette (adopted 2 Oct 2026) ----
BONE = (244, 241, 234)       # light field, top
INK = (20, 20, 18)           # quote text on bone
GOLD_DEEP = (198, 150, 38)   # gold that holds contrast against BONE
SS = 3                       # supersample factor for smooth curve edges


def build_review_card(width, height, quote, name, context, outfile):
    """Curved two-field card: bone above, black below, gold arc on the seam.

    The quote block is vertically centred inside the bone field, so a short
    review does not leave a hole at the bottom of it.
    """
    is_square = abs(width - height) < 50
    base = min(width, height)
    pad_x = int(width * 0.075)

    # ---- Two colour fields divided by a shallow arc -------------------
    split = int(height * (0.655 if is_square else 0.620))
    bulge = int(height * (0.085 if is_square else 0.110))
    over = int(width * 0.35)

    big = Image.new("RGB", (width * SS, height * SS), BLACK)
    bd = ImageDraw.Draw(big)
    ell = [-over * SS, -height * SS, (width + over) * SS, (split + bulge) * SS]
    bd.ellipse(ell, fill=BONE)
    arc = [ell[0], ell[1] + 14 * SS, ell[2], ell[3] + 14 * SS]
    bd.arc(arc, 0, 180, fill=GOLD, width=5 * SS)
    img = big.resize((width, height), LANCZOS)
    draw = ImageDraw.Draw(img)

    # ---- Header: Google G + stars + label (all on bone) ---------------
    head_y = int(height * 0.085)
    g_size = int(base * 0.072)
    g_img = draw_google_g(g_size)
    img.paste(g_img, (pad_x, head_y), g_img)

    star_r = int(base * 0.027)
    star_x = pad_x + g_size + int(base * 0.028) + star_r
    star_cy = head_y + g_size / 2
    for i in range(5):
        draw_star(draw, star_x + i * int(star_r * 2.35), star_cy, star_r, GOLD_DEEP)

    f_label = font_bold(max(14, int(base * 0.025)))
    label_y = head_y + g_size + int(base * 0.020)
    draw.text((pad_x, label_y), "GOOGLE REVIEW", font=f_label, fill=GOLD_DEEP)
    label_bottom = label_y + int(base * 0.025)

    # ---- Quote, shrink-to-fit, centred in the remaining bone space ----
    quote_text = "\u201c" + quote.strip().strip('"').strip("\u201c\u201d") + "\u201d"
    quote_max_w = width - 2 * pad_x
    field_top = label_bottom + int(base * 0.035)
    # the arc sits highest at the left and right edges, which is exactly where
    # the text starts, so keep a generous gap rather than hugging the seam
    field_bottom = split - int(height * 0.080)
    max_block_h = field_bottom - field_top
    start_size = int(base * (0.062 if is_square else 0.070))

    chosen, qlines = 22, [quote_text]
    for size in range(start_size, 20, -2):
        f_t = font_black(size)
        tl = wrap_to_width(draw, quote_text, f_t, quote_max_w)
        lh = int(size * 1.17)
        if tl and len(tl) * lh <= max_block_h and max(measure(draw, l, f_t)[0] for l in tl) <= quote_max_w:
            chosen, qlines = size, tl
            break
    f_q = font_black(chosen)
    qlh = int(chosen * 1.17)
    block_h = len(qlines) * qlh
    y = field_top + max(0, (max_block_h - block_h) // 2)
    for ln in qlines:
        draw.text((pad_x, y), ln, font=f_q, fill=INK)
        y += qlh

    # ---- Attribution on the black field -------------------------------
    attr_y = split + int(height * (0.075 if is_square else 0.095))
    draw.rectangle(
        [pad_x, attr_y, pad_x + int(base * 0.10), attr_y + max(4, int(base * 0.010))],
        fill=GOLD,
    )
    attr_y += int(base * 0.038)
    name_size = max(18, int(base * 0.040))
    draw.text((pad_x, attr_y), name, font=font_bold(name_size), fill=WHITE)
    if context:
        draw.text(
            (pad_x, attr_y + int(name_size * 1.45)),
            context, font=font_regular(max(15, int(base * 0.027))), fill=GREY,
        )

    # ---- Footer -------------------------------------------------------
    logo_h = int(height * 0.072)
    logo = prepare_logo(logo_h, for_dark_bg=True)
    if logo is not None:
        img.paste(logo, (pad_x, height - logo.height - int(height * 0.050)), logo)

    f_url = font_regular(max(14, int(base * 0.022)))
    uw, _ = measure(draw, URL_TEXT, f_url)
    draw.text((width - pad_x - uw, height - int(height * 0.078)), URL_TEXT, font=f_url, fill=GREY)

    img.save(outfile)
    print(f"Generated {outfile} ({width}x{height})")


def main():
    ensure_fonts()
    data = json.load(open("posts/reviews.json"))
    for rv in data.get("reviews", []):
        slug = rv["slug"]
        build_review_card(1200, 628, rv["quote"], rv["name"], rv.get("context", ""), f"{slug}_landscape.png")
        build_review_card(1080, 1080, rv["quote"], rv["name"], rv.get("context", ""), f"{slug}_square.png")


if __name__ == "__main__":
    main()
