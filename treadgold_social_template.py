"""
Treadgold Finance social post image generator.

Reconstructed from the canonical version built in the Marketing Project Chat
(26 May 2026). Reads posts/current_week.json, outputs branded PNGs.

Layout (locked):
  - Black background (#0D0D0D)
  - Short gold bar top-left
  - Eyebrow row: gold square + UPPERCASE gold eyebrow + thin grey divider
  - Huge ALL CAPS white headline (Montserrat-Black, shrink-to-fit)
  - Grey sentence-case subtitle
  - Full-width gold rule above footer
  - Treadgold logo bottom-left (white-bg-transparent, dark-text->white)
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

# ---------- Fonts (downloaded at runtime) ----------
FONTS_DIR = Path("fonts")
FONT_BLACK_PATH = FONTS_DIR / "Montserrat-Black.ttf"
FONT_BOLD_PATH = FONTS_DIR / "Montserrat-Bold.ttf"
FONT_REGULAR_PATH = FONTS_DIR / "Montserrat-Regular.ttf"

FONT_URLS = {
    FONT_BLACK_PATH: "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Black.ttf",
    FONT_BOLD_PATH: "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf",
    FONT_REGULAR_PATH: "https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Regular.ttf",
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
                print(f"  Failed: {e}", file=sys.stderr)


def _try_font(candidates, size):
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def font_black(size):
    return _try_font([str(FONT_BLACK_PATH), FALLBACK_BOLD], size)


def font_bold(size):
    return _try_font([str(FONT_BOLD_PATH), FALLBACK_BOLD], size)


def font_regular(size):
    return _try_font([str(FONT_REGULAR_PATH), FALLBACK_REG], size)


def measure(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_to_width(draw, text, font, max_width):
    words = text.split()
    if not words:
        return []
    lines = []
    current = [words[0]]
    for w in words[1:]:
        trial = " ".join(current + [w])
        bbox = draw.textbbox((0, 0), trial, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current.append(w)
        else:
            lines.append(" ".join(current))
            current = [w]
    lines.append(" ".join(current))
    return lines


def prepare_logo(target_height_px, for_dark_bg=True):
    """Load logo, prepare for dark background:
    - white-ish background -> transparent
    - dark text -> white (so 'Tread' becomes readable on dark bg)
    - mid-grey text -> light grey
    - everything else (gold) preserved as-is
    """
    if not os.path.exists(LOGO_FILE):
        return None
    logo = Image.open(LOGO_FILE).convert("RGBA")
    data = list(logo.getdata())
    new_data = []
    for px in data:
        r, g, b, a = px
        # White-ish background -> transparent
        if r > 240 and g > 240 and b > 240:
            new_data.append((255, 255, 255, 0))
            continue
        if for_dark_bg:
            brightness = (r + g + b) / 3
            # Dark text (e.g. 'Tread' letters) -> white
            if brightness < 80:
                new_data.append((255, 255, 255, a))
                continue
            # Mid-grey (e.g. 'FINANCE') -> light grey
            if 80 <= brightness < 180 and abs(r - g) < 20 and abs(g - b) < 20:
                new_data.append((200, 200, 200, a))
                continue
        # Otherwise keep original (gold stays gold)
        new_data.append((r, g, b, a))
    logo.putdata(new_data)
    ratio = target_height_px / logo.height
    new_w = int(logo.width * ratio)
    logo = logo.resize((new_w, target_height_px), LANCZOS)
    return logo


def build_image(width, height, eyebrow, headline, subline, outfile):
    img = Image.new("RGB", (width, height), BLACK)
    draw = ImageDraw.Draw(img)

    is_square = abs(width - height) < 50
    base = min(width, height)
    pad_x = int(width * 0.07)

    # ---- Top: short gold bar against left edge
    top_bar_w = int(width * 0.15)
    top_bar_h = max(4, int(base * 0.008))
    top_bar_y = int(height * 0.05)
    draw.rectangle(
        [pad_x, top_bar_y, pad_x + top_bar_w, top_bar_y + top_bar_h],
        fill=GOLD,
    )

    # ---- Eyebrow row: gold square + uppercase gold eyebrow + grey divider line
    eyebrow_y = top_bar_y + top_bar_h + int(base * 0.030)
    square_size = max(8, int(base * 0.025))
    draw.rectangle(
        [pad_x, eyebrow_y, pad_x + square_size, eyebrow_y + square_size],
        fill=GOLD,
    )

    eyebrow_text = eyebrow.upper()
    eyebrow_size = max(14, int(base * 0.022))
    f_eyebrow = font_bold(eyebrow_size)
    eb_w, eb_h = measure(draw, eyebrow_text, f_eyebrow)
    eb_x = pad_x + square_size + int(base * 0.018)
    eb_y = eyebrow_y + (square_size - eb_h) // 2 - int(base * 0.003)
    draw.text((eb_x, eb_y), eyebrow_text, font=f_eyebrow, fill=GOLD)

    # Thin grey divider line continuing right to the page edge
    divider_start_x = eb_x + eb_w + int(base * 0.022)
    divider_end_x = width - pad_x
    divider_y = eyebrow_y + square_size // 2
    if divider_start_x < divider_end_x - 20:
        draw.line(
            [divider_start_x, divider_y, divider_end_x, divider_y],
            fill=GREY, width=1
        )

    # ---- Headline (ALL CAPS, white, very bold) - find largest size that fits
    headline_upper = headline.upper()
    headline_max_w = width - 2 * pad_x
    max_block_h = int(height * (0.55 if is_square else 0.60))
    start_size = int(base * (0.18 if is_square else 0.30))

    chosen_size = 30
    lines = [headline_upper]
    for size in range(start_size, 30, -2):
        f_test = font_black(size)
        test_lines = wrap_to_width(draw, headline_upper, f_test, headline_max_w)
        test_line_h = int(size * 1.02)
        test_block_h = len(test_lines) * test_line_h
        if test_lines:
            test_max_w = max(measure(draw, ln, f_test)[0] for ln in test_lines)
        else:
            test_max_w = 0
        if (
            test_max_w <= headline_max_w
            and test_block_h <= max_block_h
            and len(test_lines) <= 4
        ):
            chosen_size = size
            lines = test_lines
            break

    f_head = font_black(chosen_size)
    line_h = int(chosen_size * 1.02)
    headline_top = eyebrow_y + square_size + int(base * 0.04)
    y = headline_top
    for line in lines:
        draw.text((pad_x, y), line, font=f_head, fill=WHITE)
        y += line_h
    headline_bottom = y

    # ---- Subline (grey, sentence case)
    if subline:
        sub_size = max(16, int(base * 0.032))
        f_sub = font_regular(sub_size)
        sub_y = headline_bottom + int(base * 0.020)
        sub_lines = wrap_to_width(draw, subline, f_sub, headline_max_w)
        sub_line_h = int(sub_size * 1.30)
        for i, line in enumerate(sub_lines):
            draw.text((pad_x, sub_y + i * sub_line_h), line, font=f_sub, fill=GREY)

    # ---- Full-width gold rule above footer
    rule_y = height - int(height * 0.135)
    draw.line([pad_x, rule_y, width - pad_x, rule_y], fill=GOLD, width=2)

    # ---- Logo bottom-left (white bg transparent, dark text -> white)
    logo_h = int(height * 0.075)
    logo = prepare_logo(logo_h, for_dark_bg=True)
    if logo is not None:
        logo_y = height - logo.height - int(height * 0.045)
        img.paste(logo, (pad_x, logo_y), logo)

    # ---- URL bottom-right
    url_size = max(14, int(base * 0.022))
    f_url = font_regular(url_size)
    url_w, _ = measure(draw, URL_TEXT, f_url)
    url_x = width - pad_x - url_w
    url_y = height - int(height * 0.075)
    draw.text((url_x, url_y), URL_TEXT, font=f_url, fill=GREY)

    img.save(outfile, "PNG", optimize=True)
    print(f"Generated {outfile} ({width}x{height})")


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
        subline = post.get("subtitle", "")
        build_image(1200, 628, eyebrow, headline, subline, f"{slug}_landscape.png")
        build_image(1080, 1080, eyebrow, headline, subline, f"{slug}_square.png")

    # Also generate review cards if a reviews config exists.
    # Kept in its own module (treadgold_review_card.py); this just invokes it
    # so the existing CI workflow (which runs this script) produces them too.
    reviews_path = Path("posts/reviews.json")
    if reviews_path.exists():
        try:
            import treadgold_review_card as trc
            with open(reviews_path) as rf:
                rdata = json.load(rf)
            for rv in rdata.get("reviews", []):
                rslug = rv["slug"]
                trc.build_review_card(1200, 628, rv["quote"], rv["name"], rv.get("context", ""), f"{rslug}_landscape.png")
                trc.build_review_card(1080, 1080, rv["quote"], rv["name"], rv.get("context", ""), f"{rslug}_square.png")
        except Exception as e:
            print(f"Review-card generation skipped/failed: {e}")


if __name__ == "__main__":
    main()
