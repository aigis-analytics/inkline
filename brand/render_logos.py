"""
Inkline logo renderer — v3
Mark source of truth: brand/logo/mark.svg (ink drop + stem, via cairosvg).
PIL used only for wordmark text and lockup composition.
"""

import io
import os

import cairosvg
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/tmp/inkline_fonts/PlusJakartaSans-ExtraLight.ttf"

INK      = (10,  10,  10)
INDIGO   = (61,  43, 232)
INDIGO_L = (108, 95, 255)
VELLUM   = (247, 246, 242)
WHITE    = (255, 255, 255)
DARK_BG  = (10,  10,  16)

SVG_DIR = os.path.join(os.path.dirname(__file__), "logo")
OUT = os.path.join(os.path.dirname(__file__), "logo", "rendered")
os.makedirs(OUT, exist_ok=True)


# ── SVG mark renderer ─────────────────────────────────────────────────────────

def render_mark_svg(height, variant="gradient", bg=None):
    """
    Render the ink drop mark SVG to a PIL Image at the given height.

    variant:
      "gradient" → mark.svg        (ink drop with indigo gradient fill)
      "white"    → mark-white.svg  (white ink drop, for dark backgrounds)
      "icon"     → mark-icon.svg   (rounded square app icon — square output)

    For "icon" variant the output is square (height × height).
    For "gradient" and "white" the aspect ratio is preserved from the SVG.

    bg: optional tuple (R, G, B) to composite onto a solid background.
        If None, returns RGBA with transparency.
    """
    svg_map = {
        "gradient": os.path.join(SVG_DIR, "mark.svg"),
        "white":    os.path.join(SVG_DIR, "mark-white.svg"),
        "icon":     os.path.join(SVG_DIR, "mark-icon.svg"),
    }
    svg_path = svg_map[variant]

    if variant == "icon":
        # Square output — render at height × height
        png_bytes = cairosvg.svg2png(url=svg_path, output_width=height, output_height=height)
    else:
        # Preserve SVG aspect ratio by specifying only height
        png_bytes = cairosvg.svg2png(url=svg_path, output_height=height)

    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")

    if bg is not None:
        bg_layer = Image.new("RGBA", img.size, bg + (255,))
        return Image.alpha_composite(bg_layer, img)
    return img


def render_mark_icon(size, bg=None):
    """
    Render the app icon variant (rounded square) at size × size.
    Convenience wrapper around render_mark_svg with variant="icon".
    """
    return render_mark_svg(size, variant="icon", bg=bg)


# ── Wordmark ──────────────────────────────────────────────────────────────────

def draw_wordmark(height=160, bg=VELLUM, ink_col=INK, line_col=INDIGO):
    """
    'ink' in ink_col, 'line' in line_col, side by side.
    Renders at 4× then downscales for crisp anti-aliasing.
    """
    S = 4
    font_size = int(height * S * 0.72)
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except Exception:
        font = ImageFont.load_default()
        font_size = 40

    # Measure at 4× scale
    probe = Image.new("RGBA", (1, 1))
    pd = ImageDraw.Draw(probe)
    b_ink  = pd.textbbox((0, 0), "ink",     font=font)
    b_line = pd.textbbox((0, 0), "line",    font=font)
    b_full = pd.textbbox((0, 0), "inkline", font=font)

    w_ink  = b_ink[2]  - b_ink[0]
    w_line = b_line[2] - b_line[0]
    h_text = b_full[3] - b_full[1]
    pad_x  = int(font_size * 0.08)
    pad_y  = int(height * S * 0.12)

    canvas_w = w_ink + w_line + pad_x * 2
    canvas_h = height * S
    baseline = pad_y + h_text

    img = Image.new("RGBA", (canvas_w, canvas_h), bg + (255,))
    d   = ImageDraw.Draw(img)
    d.text((pad_x,         baseline), "ink",  font=font, fill=ink_col,  anchor="lb")
    d.text((pad_x + w_ink, baseline), "line", font=font, fill=line_col, anchor="lb")

    out_w = canvas_w // S
    out_h = height
    return img.resize((out_w, out_h), Image.LANCZOS)


# ── Lockups ───────────────────────────────────────────────────────────────────

def draw_lockup_h(height=120, bg=VELLUM, dark=False):
    """Horizontal lockup: ink drop mark + wordmark side by side."""
    bg_col = DARK_BG if dark else bg
    # Use white mark on dark, gradient mark on light
    mark_variant = "white" if dark else "gradient"
    mark = render_mark_svg(height, variant=mark_variant, bg=bg_col)
    word = draw_wordmark(height, bg=bg_col,
                         ink_col=(220, 218, 255) if dark else INK,
                         line_col=WHITE if dark else INDIGO)
    gap    = int(height * 0.30)
    W      = mark.width + gap + word.width
    canvas = Image.new("RGBA", (W, height), bg_col + (255,))
    canvas.paste(mark, (0, 0), mark)
    canvas.paste(word, (mark.width + gap, 0), word)
    return canvas


def draw_lockup_stacked(width=560, bg=VELLUM):
    """Stacked lockup: ink drop mark centred above wordmark."""
    mark_h = int(width * 0.38)
    mark   = render_mark_svg(mark_h, variant="gradient", bg=bg)
    word   = draw_wordmark(int(width * 0.20), bg=bg)
    gap    = int(width * 0.07)
    H      = mark.height + gap + word.height
    canvas = Image.new("RGBA", (width, H), bg + (255,))
    canvas.paste(mark, ((width - mark.width) // 2, 0), mark)
    canvas.paste(word, ((width - word.width) // 2, mark.height + gap), word)
    return canvas


# ── Colour palette ────────────────────────────────────────────────────────────

def draw_palette():
    W, H = 1100, 430
    img  = Image.new("RGB", (W, H), VELLUM)
    d    = ImageDraw.Draw(img)

    try:
        lf = ImageFont.truetype(FONT_PATH, 20)
        hf = ImageFont.truetype(FONT_PATH, 16)
        tf = ImageFont.truetype(FONT_PATH, 13)
    except Exception:
        lf = hf = tf = ImageFont.load_default()

    primaries = [
        ((10,  10,  10),  "Ink",       "#0A0A0A"),
        ((61,  43, 232),  "Indigo",    "#3D2BE8"),
        ((108, 95, 255),  "Indigo·L",  "#6C5FFF"),
        ((100, 116, 139), "Slate",     "#64748B"),
        ((226, 225, 220), "Rule",      "#E2E1DC"),
    ]
    accents = [
        ((124, 58, 237), "Violet",    "#7C3AED"),
        (( 30, 64, 175), "Cobalt",    "#1E40AF"),
        ((220, 38,  38), "Vermilion", "#DC2626"),
        (( 22, 163, 74), "Sage",      "#16A34A"),
        ((217, 119,   6), "Amber",    "#D97706"),
    ]

    d.text((36, 22), "COLOUR SYSTEM", font=tf, fill=(160, 160, 155))

    sw, sh, gap, x0, y0 = 148, 140, 22, 36, 50
    for i, (col, name, hex_v) in enumerate(primaries):
        x = x0 + i * (sw + gap)
        outline = (200, 198, 192) if sum(col) > 600 else None
        d.rounded_rectangle([x, y0, x + sw, y0 + sh], radius=10, fill=col,
                             outline=outline, width=1)
        d.text((x, y0 + sh + 12), name,  font=lf, fill=INK)
        d.text((x, y0 + sh + 36), hex_v, font=hf, fill=(120, 120, 115))

    d.line([(36, 240), (W - 36, 240)], fill=(220, 218, 212), width=1)
    d.text((36, 255), "ACCENTS", font=tf, fill=(160, 160, 155))

    sw2, sh2, x0b, y0b = 148, 70, 36, 265
    for i, (col, name, hex_v) in enumerate(accents):
        x = x0b + i * (sw2 + 22)
        d.rounded_rectangle([x, y0b, x + sw2, y0b + sh2], radius=6, fill=col)
        d.text((x, y0b + sh2 + 10), name,  font=lf, fill=INK)
        d.text((x, y0b + sh2 + 30), hex_v, font=hf, fill=(120, 120, 115))

    return img


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Rendering Inkline brand assets...")

    # Mark variants — standalone ink drop
    render_mark_svg(512, "gradient", bg=VELLUM).save(f"{OUT}/mark-512.png")
    render_mark_svg(1024, "gradient", bg=VELLUM).save(f"{OUT}/mark-1024.png")
    render_mark_svg(512, "gradient", bg=WHITE).save(f"{OUT}/mark-on-white.png")
    render_mark_svg(512, "white", bg=DARK_BG).save(f"{OUT}/mark-dark.png")
    print("  mark variants (ink drop)")

    # App icon variants — rounded square
    render_mark_icon(512).save(f"{OUT}/mark-icon-512.png")
    render_mark_icon(1024).save(f"{OUT}/mark-icon-1024.png")
    print("  mark icon variants (app icon)")

    # Wordmark
    draw_wordmark(200).save(f"{OUT}/wordmark.png")
    draw_wordmark(200, bg=DARK_BG, ink_col=(220, 218, 255), line_col=WHITE).save(
        f"{OUT}/wordmark-dark.png")
    print("  wordmark")

    # Lockups
    draw_lockup_h(140).save(f"{OUT}/lockup-horizontal.png")
    draw_lockup_h(140, dark=True).save(f"{OUT}/lockup-horizontal-dark.png")
    print("  lockup horizontal")

    draw_lockup_stacked(600).save(f"{OUT}/lockup-stacked.png")
    print("  lockup stacked")

    draw_palette().save(f"{OUT}/colours.png")
    print("  colour palette")

    # Report dimensions and file sizes
    print(f"\nOutput directory: {OUT}")
    import os as _os
    for fname in sorted(_os.listdir(OUT)):
        fpath = _os.path.join(OUT, fname)
        size_kb = _os.path.getsize(fpath) // 1024
        try:
            img = Image.open(fpath)
            print(f"  {fname:40s}  {img.size[0]}x{img.size[1]}  {size_kb} KB")
        except Exception:
            print(f"  {fname:40s}  {size_kb} KB")
