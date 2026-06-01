"""
Treadgold Finance social post image generator.

Reads posts/current_week.json and outputs branded PNGs.
Downloads Montserrat at runtime; adapts logo for dark backgrounds.

Brand layout (memory #5):
  - Black background (#0D0D0D)
  - Gold bar top-left (#E8B84B)
  - Gold square + caps gold eyebrow text + thin grey rule
  - Huge all-caps white headline (Montserrat-Black)
  - Grey subtitle paragraph
  - Full-width gold rule above footer
  - Logo bottom-left (black pixels auto-converted to white)
  - URL bottom-right (treadgoldfinance.com.au)
"""

import json
import os
import sys
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---------- Brand ----------
GOLD = (232, 184, 75)
BLACK = (13, 13, 13)
WHITE = (255, 255, 255)
GREY = (138, 138, 138)
URL_TEXT = "treadgoldfinance.com.au"
LOGO_FILE = "treadgold_signature_logo.png"

# ---------- Fonts (downloaded at runtime from Google Fonts repo) ----------
FONTS_DIR = Path("fonts")
FONT_BLACK = FONTS_DIR / "Montserrat-Black.ttf"
FONT_BOLD = FONTS_DIR / "Montserrat-Bold.ttf"
FONT_REGULAR = FONTS_DIR / "Montserrat-Regular.ttf"

FONT_URLS = {
    FONT_BLACK: "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Black.ttf",
    FONT_BOLD: "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf",
    FONT_REGULAR: "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Regular.ttf",
}

FALLBACK_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FALLBACK_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

try:
    LANCZOS = Image.Resampling.LANCZOS
except AttributeError:
    LANCZOS = Image.LANCZOS


def ensure_fonts():
    FONTS_DIR.mkdir(exist_ok=True)
    for path, url in FONT_URLS.items():
        if not path.exists():
            print(f"Downloading {path.name}...")
            try:
                urllib.request.urlretrieve(url, path)
                print(f"  Saved {path}")
            except Exception as e:
                print(f"  Failed to download {path.name}: {e}", file=sys.stderr)


def safe_font(path, fallback, size):
    path_str = str(path)
    if os.path.exists(path_str):
        try:
            return ImageFont.truetype(path_str, size)
        except Exception as e:
            print(f"  Font {path_str} failed to load: {e}", file=sys.stderr)
    return ImageFont.truetype(fallback, size)


def adapt_logo_for_dark_bg(logo):
    """Replace black-ish pixels with white so light-bg logo works on dark bg.
    Preserves gold and any other coloured pixels, plus alpha."""
    if logo.mode != "RGBA":
        logo = logo.convert("RGBA")
    pixels = list(logo.getdata())
    new_pixels = []
    for r, g, b, a in pixels:
        if a == 0:
            new_pixels.append((r, g, b, a))
        elif r < 70 and g < 70 and b < 70:
            new_pixels.append((255, 255, 255, a))
        else:
            new_pixels.append((r, g, b, a))
    logo.putdata(new_pixels)
    return logo


def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width or not current:
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

    margin = int(width * 0.060)

    # ---- Top: gold bar ----
    bar_w = int(width * 0.045)
    bar_h = max(4, int(height * 0.010))
    draw.rectangle([margin, margin, margin + bar_w, margin + bar_h], fill=GOLD)

    # ---- Eyebrow row: gold square + gold caps text + thin grey rule ----
    sq_size = max(8, int(height * 0.022))
    sq_y = margin + bar_h + int(height * 0.030)
    draw.rectangle([margin, sq_y, margin + sq_size, sq_y + sq_size], fill=GOLD)

    eb_size = max(14, int(height * 0.030))
    eb_font = safe_font(FONT_BOLD, FALLBACK_BOLD, eb_size)
    eb_text = eyebrow.upper()
    eb_bbox = draw.textbbox((0, 0), eb_text, font=eb_font)
    eb_text_h = eb_bbox[3] - eb_bbox[1]
    eb_x = margin + sq_size + int(eb_size * 0.65)
    # Vertically centre text baseline with square middle
    eb_y = sq_y + (sq_size // 2) - (eb_text_h // 2) - eb_bbox[1]
    draw.text((eb_x, eb_y), eb_text, font=eb_font, fill=GOLD)

    eb_text_w = eb_bbox[2] - eb_bbox[0]
    rule_start_x = eb_x + eb_text_w + int(eb_size * 1.0)
    rule_y = sq_y + (sq_size // 2)
    if rule_start_x < width - margin - 20:
        draw.line([rule_start_x, rule_y, width - margin, rule_y], fill=GREY, width=1)

    # ---- Headline (huge, Montserrat-Black, white) ----
    headline_text = headline.upper()
    headline_size = int(height * 0.150)
    headline_font = safe_font(FONT_BLACK, FALLBACK_BOLD, headline_size)
    headline_y = int(height * 0.20)
    max_w = width - 2 * margin
    lines = wrap_text(draw, headline_text, headline_font, max_w)
    line_h = int(headline_size * 1.00)
    for i, line in enumerate(lines):
        draw.text((margin, headline_y + i * line_h), line, font=headline_font, fill=WHITE)
    headline_bottom = headline_y + len(lines) * line_h

    # ---- Subtitle (grey) ----
    if subtitle:
        sub_size = max(16, int(height * 0.032))
        sub_font = safe_font(FONT_REGULAR, FALLBACK_REG, sub_size)
        sub_y = headline_bottom + int(height * 0.020)
        sub_lines = wrap_text(draw, subtitle, sub_font, max_w)
        sub_line_h = int(sub_size * 1.3)
        for i, line in enumerate(sub_lines):
            draw.text((margin, sub_y + i * sub_line_h), line, font=sub_font, fill=GREY)

    # ---- Gold rule above footer ----
    rule_y2 = height - int(height * 0.135)
    draw.line([margin, rule_y2, width - margin, rule_y2], fill=GOLD, width=2)

    # ---- Logo bottom-left (auto-adapted) ----
    if os.path.exists(LOGO_FILE):
        try:
            logo = Image.open(LOGO_FILE).convert("RGBA")
            logo = adapt_logo_for_dark_bg(logo)
            target_h = int(height * 0.080)
            ratio = target_h / logo.height
            target_w = int(logo.width * ratio)
            logo = logo.resize((target_w, target_h), LANCZOS)
            img.paste(logo, (margin, height - int(height * 0.115)), logo)
        except Exception as e:
            print(f"  Warning: could not paste logo: {e}", file=sys.stderr)

    # ---- URL bottom-right ----
    url_size = max(14, int(height * 0.026))
    url_font = safe_font(FONT_REGULAR, FALLBACK_REG, url_size)
    url_bbox = draw.textbbox((0, 0), URL_TEXT, font=url_font)
    url_w = url_bbox[2] - url_bbox[0]
    draw.text((width - margin - url_w, height - int(height * 0.083)),
              URL_TEXT, font=url_font, fill=GREY)

    return img


def main():
    ensure_fonts()
    config_path = Path("posts/current_week.json")
    if not config_path.exists():
        print(f"No config at {config_path}")
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
