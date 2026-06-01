"""
Treadgold Finance social post image generator.

Reads posts/current_week.json and outputs branded PNGs (landscape + square)
per post. Run by .github/workflows/generate-posts.yml or locally:
    python treadgold_social_template.py

Locked brand layout (memory #5 — do not modify without explicit instruction):
  - Black background (#0D0D0D)
  - Gold bar top-left (#E8B84B)
  - Gold rectangle eyebrow (caps text, black on gold)
  - Grey divider line under eyebrow (#8A8A8A)
  - Huge all-caps white headline
  - Grey subtitle paragraph
  - Full-width gold rule above footer
  - Logo bottom-left (treadgold_signature_logo.png)
  - URL bottom-right (treadgoldfinance.com.au)
"""

import json
import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---------- Brand constants (locked) ----------
GOLD = (232, 184, 75)        # #E8B84B
BLACK = (13, 13, 13)         # #0D0D0D
WHITE = (255, 255, 255)
GREY = (138, 138, 138)       # #8A8A8A
URL_TEXT = "treadgoldfinance.com.au"
LOGO_FILE = "treadgold_signature_logo.png"

# ---------- Font discovery ----------
FONT_BOLD_PATHS = [
    "/usr/share/fonts/truetype/montserrat/Montserrat-Bold.ttf",
    "/usr/share/fonts/truetype/montserrat/Montserrat-Bold.otf",
    "/usr/share/fonts/opentype/montserrat/Montserrat-Bold.otf",
    "/usr/share/fonts/truetype/montserrat/static/Montserrat-Bold.ttf",
]
FONT_REG_PATHS = [
    "/usr/share/fonts/truetype/montserrat/Montserrat-Regular.ttf",
    "/usr/share/fonts/truetype/montserrat/Montserrat-Regular.otf",
    "/usr/share/fonts/opentype/montserrat/Montserrat-Regular.otf",
    "/usr/share/fonts/truetype/montserrat/static/Montserrat-Regular.ttf",
]
FALLBACK_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FALLBACK_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

try:
    LANCZOS = Image.Resampling.LANCZOS
except AttributeError:
    LANCZOS = Image.LANCZOS


def find_font(paths, fallback, size):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.truetype(fallback, size)


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width or not current:
            current = test
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_post(eyebrow, headline, subtitle, width, height):
    img = Image.new("RGB", (width, height), BLACK)
    draw = ImageDraw.Draw(img)

    margin = int(min(width, height) * 0.06)

    # Gold bar top-left
    bar_w = int(width * 0.08)
    bar_h = max(6, int(height * 0.014))
    draw.rectangle([margin, margin, margin + bar_w, margin + bar_h], fill=GOLD)

    # Eyebrow: gold rectangle with black caps text
    eyebrow_text = eyebrow.upper()
    eb_font_size = max(14, int(height * 0.028))
    eb_font = find_font(FONT_BOLD_PATHS, FALLBACK_BOLD, eb_font_size)
    eb_bbox = draw.textbbox((0, 0), eyebrow_text, font=eb_font)
    eb_text_w = eb_bbox[2] - eb_bbox[0]
    eb_text_h = eb_bbox[3] - eb_bbox[1]
    eb_pad_x = int(eb_font_size * 0.7)
    eb_pad_y = int(eb_font_size * 0.5)
    eb_x = margin
    eb_y = margin + bar_h + int(height * 0.05)
    eb_box_w = eb_text_w + 2 * eb_pad_x
    eb_box_h = eb_text_h + 2 * eb_pad_y
    draw.rectangle([eb_x, eb_y, eb_x + eb_box_w, eb_y + eb_box_h], fill=GOLD)
    draw.text((eb_x + eb_pad_x - eb_bbox[0], eb_y + eb_pad_y - eb_bbox[1]),
              eyebrow_text, font=eb_font, fill=BLACK)

    # Grey divider under eyebrow
    div_y = eb_y + eb_box_h + int(height * 0.035)
    div_len = int(width * 0.10)
    draw.line([margin, div_y, margin + div_len, div_y], fill=GREY, width=2)

    # Headline (huge all-caps white)
    headline_text = headline.upper()
    headline_size = max(28, int(height * 0.085))
    headline_font = find_font(FONT_BOLD_PATHS, FALLBACK_BOLD, headline_size)
    headline_y = div_y + int(height * 0.04)
    max_w = width - 2 * margin
    lines = wrap_text(draw, headline_text, headline_font, max_w)
    line_h = int(headline_size * 1.08)
    for i, line in enumerate(lines):
        draw.text((margin, headline_y + i * line_h), line, font=headline_font, fill=WHITE)
    headline_bottom = headline_y + len(lines) * line_h

    # Subtitle (grey)
    if subtitle:
        sub_size = max(16, int(height * 0.030))
        sub_font = find_font(FONT_REG_PATHS, FALLBACK_REG, sub_size)
        sub_y = headline_bottom + int(height * 0.025)
        sub_lines = wrap_text(draw, subtitle, sub_font, max_w)
        sub_line_h = int(sub_size * 1.35)
        for i, line in enumerate(sub_lines):
            draw.text((margin, sub_y + i * sub_line_h), line, font=sub_font, fill=GREY)

    # Full-width gold rule above footer
    rule_y = height - int(height * 0.13)
    draw.line([margin, rule_y, width - margin, rule_y], fill=GOLD, width=3)

    # Logo bottom-left
    if os.path.exists(LOGO_FILE):
        try:
            logo = Image.open(LOGO_FILE).convert("RGBA")
            target_h = int(height * 0.07)
            ratio = target_h / logo.height
            target_w = int(logo.width * ratio)
            logo = logo.resize((target_w, target_h), LANCZOS)
            img.paste(logo, (margin, height - int(height * 0.10)), logo)
        except Exception as e:
            print(f"  Warning: could not paste logo: {e}", file=sys.stderr)

    # URL bottom-right
    url_size = max(14, int(height * 0.025))
    url_font = find_font(FONT_REG_PATHS, FALLBACK_REG, url_size)
    url_bbox = draw.textbbox((0, 0), URL_TEXT, font=url_font)
    url_w = url_bbox[2] - url_bbox[0]
    draw.text((width - margin - url_w, height - int(height * 0.085)),
              URL_TEXT, font=url_font, fill=GREY)

    return img


def main():
    config_path = Path("posts/current_week.json")
    if not config_path.exists():
        print(f"No config at {config_path} \u2014 nothing to do.")
        return

    with open(config_path) as f:
        config = json.load(f)

    posts = config.get("posts", [])
    if not posts:
        print("Config has no posts.")
        return

    for post in posts:
        slug = post["slug"]
        eyebrow = post["eyebrow"]
        headline = post["headline"]
        subtitle = post.get("subtitle", "")

        landscape = render_post(eyebrow, headline, subtitle, 1200, 628)
        landscape.save(f"{slug}_landscape.png", "PNG")
        print(f"Generated {slug}_landscape.png")

        square = render_post(eyebrow, headline, subtitle, 1080, 1080)
        square.save(f"{slug}_square.png", "PNG")
        print(f"Generated {slug}_square.png")


if __name__ == "__main__":
    main()
