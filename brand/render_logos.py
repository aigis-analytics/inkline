"""
Inkline logo renderer — v2
Fixes: mark proportions (ink drop not balloon), wordmark scale bug.
"""

import math, os
from PIL import Image, ImageDraw, ImageFont

FONT_PATH = "/tmp/inkline_fonts/PlusJakartaSans-ExtraLight.ttf"

INK      = (10,  10,  10)
INDIGO   = (61,  43, 232)
INDIGO_L = (108, 95, 255)
VELLUM   = (247, 246, 242)
WHITE    = (255, 255, 255)
DARK_BG  = (10,  10,  16)

OUT = os.path.join(os.path.dirname(__file__), "logo", "rendered")
os.makedirs(OUT, exist_ok=True)


# ── Geometry helpers ──────────────────────────────────────────────────────────

def lerp(a, b, t):
    return a + (b - a) * t

def quad_pt(p0, p1, p2, t):
    return (lerp(lerp(p0[0],p1[0],t), lerp(p1[0],p2[0],t), t),
            lerp(lerp(p0[1],p1[1],t), lerp(p1[1],p2[1],t), t))

def arc_pts(cx, cy, r, a0, a1, n=120):
    """Points along a clockwise arc from a0→a1 degrees."""
    a0r, a1r = math.radians(a0), math.radians(a1)
    if a1r < a0r: a1r += 2*math.pi
    return [(cx + r*math.cos(a0r + (a1r-a0r)*i/n),
             cy + r*math.sin(a0r + (a1r-a0r)*i/n)) for i in range(n+1)]

def ink_drop_poly(cx, cy, r, tail_len, stem_w, n=100):
    """Legacy — not used in main mark."""
    pass

def rrect_poly(x, y, w, h, rx, n=12):
    corners = [
        (x+rx,   y+rx,   180, 270),
        (x+w-rx, y+rx,   270, 360),
        (x+w-rx, y+h-rx,   0,  90),
        (x+rx,   y+h-rx,  90, 180),
    ]
    pts = []
    for cx, cy, a0, a1 in corners:
        pts += arc_pts(cx, cy, rx, a0, a1, n)
    return pts


# ── Gradient helper ───────────────────────────────────────────────────────────

def vert_gradient(size, top_col, bot_col):
    w, h = size
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(h-1, 1)
        d.line([(0,y),(w,y)], fill=tuple(int(a+(b-a)*t) for a,b in zip(top_col, bot_col)))
    return img

def composite_gradient_mark(mask_img, top_col, bot_col, bg):
    w, h = mask_img.size
    grad = vert_gradient((w,h), top_col, bot_col).convert("RGBA")
    alpha = mask_img.split()[3]
    grad.putalpha(alpha)
    bg_layer = Image.new("RGBA", (w,h), bg+(255,))
    return Image.alpha_composite(bg_layer, grad)


# ── Mark ──────────────────────────────────────────────────────────────────────

def draw_mark(size=512, bg=VELLUM, flat_color=None):
    """
    Inkline mark: gradient rounded-square containing the letter 'i' in white.

    This is the app-icon / brand-mark pattern used by Linear, Notion, Figma:
    a distinctive coloured tile with the brand initial, scalable 16px→1024px.

    The gradient runs top-left (Indigo Light) → bottom-right (Indigo).
    The 'i' is set in Plus Jakarta Sans ExtraLight — same font as the wordmark,
    so mark + wordmark are typographically unified.
    Corner radius = 22.5% of size (matches iOS/Android icon rounding).
    """
    S = 4
    W = H = size * S

    tile_col_tl = INDIGO_L   # #6C5FFF  top-left
    tile_col_br = INDIGO     # #3D2BE8  bottom-right

    # ── Gradient tile ──────────────────────────────────────────────────────────
    # Diagonal gradient: blend each pixel by (x+y)/(W+H)
    tile = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = tile.load()
    for y in range(H):
        for x in range(W):
            t = (x + y) / (W + H - 2)
            r = int(tile_col_tl[0] + (tile_col_br[0] - tile_col_tl[0]) * t)
            g = int(tile_col_tl[1] + (tile_col_br[1] - tile_col_tl[1]) * t)
            b = int(tile_col_tl[2] + (tile_col_br[2] - tile_col_tl[2]) * t)
            px[x, y] = (r, g, b, 255)

    # ── Rounded-square mask ────────────────────────────────────────────────────
    radius = int(W * 0.225)   # 22.5% corner rounding
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, W-1, H-1], radius=radius, fill=255)
    tile.putalpha(mask)

    # ── Letter 'i' in white ────────────────────────────────────────────────────
    font_size = int(W * 0.60)
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except Exception:
        font = ImageFont.load_default()

    d = ImageDraw.Draw(tile)
    # Centre the glyph — use textbbox for precise metrics
    bbox = d.textbbox((0, 0), "i", font=font)
    gw = bbox[2] - bbox[0]
    gh = bbox[3] - bbox[1]
    tx = (W - gw) // 2 - bbox[0]
    ty = (H - gh) // 2 - bbox[1] - int(H * 0.03)  # slight optical lift
    d.text((tx, ty), "i", font=font, fill=(255, 255, 255, 245))

    # ── Composite onto background and downscale ────────────────────────────────
    bg_layer = Image.new("RGBA", (W, H), bg + (255,))
    result = Image.alpha_composite(bg_layer, tile)
    return result.resize((size, size), Image.LANCZOS)


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
    probe = Image.new("RGBA", (1,1))
    pd = ImageDraw.Draw(probe)
    b_ink  = pd.textbbox((0,0), "ink",     font=font)
    b_line = pd.textbbox((0,0), "line",    font=font)
    b_full = pd.textbbox((0,0), "inkline", font=font)

    w_ink  = b_ink[2]  - b_ink[0]
    w_line = b_line[2] - b_line[0]
    h_text = b_full[3] - b_full[1]
    pad_x  = int(font_size * 0.08)
    pad_y  = int(height * S * 0.12)

    canvas_w = w_ink + w_line + pad_x * 2
    canvas_h = height * S
    baseline = pad_y + h_text

    img = Image.new("RGBA", (canvas_w, canvas_h), bg+(255,))
    d   = ImageDraw.Draw(img)
    d.text((pad_x,          baseline), "ink",  font=font, fill=ink_col,  anchor="lb")
    d.text((pad_x + w_ink,  baseline), "line", font=font, fill=line_col, anchor="lb")

    # Downscale both dimensions by S
    out_w = canvas_w // S
    out_h = height           # = canvas_h // S
    return img.resize((out_w, out_h), Image.LANCZOS)


# ── Lockups ───────────────────────────────────────────────────────────────────

def draw_lockup_h(height=120, bg=VELLUM, dark=False):
    bg_col = DARK_BG if dark else bg
    mark = draw_mark(height, bg=bg_col)
    word = draw_wordmark(height, bg=bg_col,
                         ink_col=(220,218,255) if dark else INK,
                         line_col=WHITE if dark else INDIGO)
    gap  = int(height * 0.30)
    W    = height + gap + word.width
    canvas = Image.new("RGBA", (W, height), bg_col+(255,))
    canvas.paste(mark, (0,0), mark)
    canvas.paste(word, (height+gap, 0), word)
    return canvas

def draw_lockup_stacked(width=560, bg=VELLUM):
    mark_size = int(width * 0.38)
    mark = draw_mark(mark_size, bg=bg)
    word = draw_wordmark(int(width * 0.20), bg=bg)
    gap  = int(width * 0.07)
    H    = mark_size + gap + word.height
    canvas = Image.new("RGBA", (width, H), bg+(255,))
    canvas.paste(mark, ((width-mark_size)//2, 0), mark)
    canvas.paste(word, ((width-word.width)//2, mark_size+gap), word)
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
        ((10, 10, 10),   "Ink",      "#0A0A0A"),
        ((61, 43,232),   "Indigo",   "#3D2BE8"),
        ((108,95,255),   "Indigo·L", "#6C5FFF"),
        ((100,116,139),  "Slate",    "#64748B"),
        ((226,225,220),  "Rule",     "#E2E1DC"),
    ]
    accents = [
        ((124, 58,237), "Violet",    "#7C3AED"),
        (( 30, 64,175), "Cobalt",    "#1E40AF"),
        ((220, 38, 38), "Vermilion", "#DC2626"),
        (( 22,163, 74), "Sage",      "#16A34A"),
        ((217,119,  6), "Amber",     "#D97706"),
    ]

    d.text((36, 22), "COLOUR SYSTEM", font=tf, fill=(160,160,155))

    sw, sh, gap, x0, y0 = 148, 140, 22, 36, 50
    for i, (col, name, hex_v) in enumerate(primaries):
        x = x0 + i*(sw+gap)
        outline = (200,198,192) if sum(col) > 600 else None
        d.rounded_rectangle([x, y0, x+sw, y0+sh], radius=10, fill=col,
                             outline=outline, width=1)
        d.text((x, y0+sh+12), name,   font=lf, fill=INK)
        d.text((x, y0+sh+36), hex_v,  font=hf, fill=(120,120,115))

    d.line([(36,240),(W-36,240)], fill=(220,218,212), width=1)
    d.text((36, 255), "ACCENTS", font=tf, fill=(160,160,155))

    sw2, sh2, x0b, y0b = 148, 70, 36, 265
    for i, (col, name, hex_v) in enumerate(accents):
        x = x0b + i*(sw2+22)
        d.rounded_rectangle([x, y0b, x+sw2, y0b+sh2], radius=6, fill=col)
        d.text((x, y0b+sh2+10), name,   font=lf, fill=INK)
        d.text((x, y0b+sh2+30), hex_v,  font=hf, fill=(120,120,115))

    return img


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Rendering Inkline brand assets…")

    draw_mark(512).save(f"{OUT}/mark-512.png")
    draw_mark(1024).save(f"{OUT}/mark-1024.png")
    draw_mark(512, bg=WHITE).save(f"{OUT}/mark-on-white.png")
    draw_mark(512, bg=DARK_BG).save(f"{OUT}/mark-dark.png")
    print("  ✓ mark variants")

    draw_wordmark(200).save(f"{OUT}/wordmark.png")
    draw_wordmark(200, bg=DARK_BG, ink_col=(220,218,255), line_col=WHITE).save(
        f"{OUT}/wordmark-dark.png")
    print("  ✓ wordmark")

    draw_lockup_h(140).save(f"{OUT}/lockup-horizontal.png")
    draw_lockup_h(140, dark=True).save(f"{OUT}/lockup-horizontal-dark.png")
    print("  ✓ lockup horizontal")

    draw_lockup_stacked(600).save(f"{OUT}/lockup-stacked.png")
    print("  ✓ lockup stacked")

    draw_palette().save(f"{OUT}/colours.png")
    print("  ✓ colour palette")

    print(f"\nAll assets → {OUT}")
