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

Layout:
  - Black background (#0D0D0D)
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


def build_review_card(width, height, quote, name, context, outfile):
    is_square = abs(width - height) < 50
    img = Image.new("RGB", (width, height), BLACK)
    draw = ImageDraw.Draw(img)
    base = min(width, height)
    pad_x = int(width * 0.07)

    bar_y = int(height * 0.07)
    draw.rectangle([pad_x, bar_y, pad_x + int(base * 0.16), bar_y + int(base * 0.012)], fill=GOLD)

    row_y = bar_y + int(base * 0.045)
    g_size = int(base * 0.075)
    g_img = draw_google_g(g_size)
    img.paste(g_img, (pad_x, row_y), g_img)

    star_r = int(base * 0.028)
    star_gap = int(star_r * 2.35)
    stars_x = pad_x + g_size + int(base * 0.03) + star_r
    stars_cy = row_y + g_size / 2
    for i in range(5):
        draw_star(draw, stars_x + i * star_gap, stars_cy, star_r, GOLD)

    label_size = max(15, int(base * 0.026))
    f_label = font_bold(label_size)
    label_text = "GOOGLE REVIEW"
    label_x = stars_x - star_r
    label_y = row_y + g_size + int(base * 0.018)
    draw.text((label_x, label_y), label_text, font=f_label, fill=GOLD)
    lw, _ = measure(draw, label_text, f_label)
    div_y = label_y + label_size // 2
    div_x0 = label_x + lw + int(base * 0.03)
    draw.line([div_x0, div_y, width - pad_x, div_y], fill=GREY, width=1)

    quote_text = "\u201c" + quote.strip().strip('"') + "\u201d"
    quote_max_w = width - 2 * pad_x
    max_block_h = int(height * (0.46 if is_square else 0.42))
    start_size = int(base * (0.072 if is_square else 0.085))
    chosen = 24
    qlines = [quote_text]
    for size in range(start_size, 22, -2):
        f_t = font_bold(size)
        tl = wrap_to_width(draw, quote_text, f_t, quote_max_w)
        lh = int(size * 1.18)
        if tl and len(tl) * lh <= max_block_h and max(measure(draw, ln, f_t)[0] for ln in tl) <= quote_max_w:
            chosen = size
            qlines = tl
            break
    f_q = font_bold(chosen)
    qlh = int(chosen * 1.18)
    quote_top = label_y + int(base * 0.07)
    y = quote_top
    for ln in qlines:
        draw.text((pad_x, y), ln, font=f_q, fill=WHITE)
        y += qlh
    quote_bottom = y

    attr_size = max(18, int(base * 0.034))
    f_name = font_bold(attr_size)
    f_ctx = font_regular(max(15, int(base * 0.026)))
    attr_y = quote_bottom + int(base * 0.025)
    draw.text((pad_x, attr_y), f"\u2014 {name}", font=f_name, fill=GOLD)
    if context:
        draw.text((pad_x, attr_y + int(attr_size * 1.35)), context, font=f_ctx, fill=GREY)

    rule_y = height - int(height * 0.135)
    draw.line([pad_x, rule_y, width - pad_x, rule_y], fill=GOLD, width=2)

    logo_h = int(height * 0.075)
    logo = prepare_logo(logo_h, for_dark_bg=True)
    if logo is not None:
        logo_y = height - logo.height - int(height * 0.045)
        img.paste(logo, (pad_x, logo_y), logo)

    url_size = max(14, int(base * 0.022))
    f_url = font_regular(url_size)
    uw, _ = measure(draw, URL_TEXT, f_url)
    draw.text((width - pad_x - uw, height - int(height * 0.075)), URL_TEXT, font=f_url, fill=GREY)

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
