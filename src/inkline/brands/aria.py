"""Aria brand definition.

Logo: Navy 'A' lettermark with amber waveform (voice/signal motif).
Palette: Navy + amber/gold — authoritative, modern, finance-tech.
Font: Inter (variable weight) — clean geometric sans-serif.
"""

from inkline.brands import BaseBrand

AriaBrand = BaseBrand(
    name="aria",
    display_name="Aria",

    # Palette — navy + amber, derived from the logo
    primary="#1E293B",          # Navy (main structural color)
    secondary="#E7971F",        # Amber/gold accent (from waveform)
    background="#FFFFFF",       # White documents
    surface="#0F172A",          # Deep navy (headers, dark surfaces)
    text="#1E293B",             # Navy body text
    muted="#64748B",            # Slate-grey captions
    light_bg="#F8FAFC",         # Very light slate background
    border="#CBD5E1",           # Light slate border

    # Typography — Inter for everything (clean, highly legible)
    heading_font="Inter",
    body_font="Inter",
    mono_font="JetBrains Mono",
    heading_size=28,
    body_size=14,

    # Assets
    logo_dark_path="aria_logo_dark.png",    # White A + amber — for dark backgrounds
    logo_light_path="aria_logo_light.png",  # Navy A + amber — for light backgrounds
    font_files=["InterVariable.ttf"],

    # Metadata
    confidentiality="",
    footer_text="Aria",
    tagline="",

    # Header style — dark bar with white logo
    header_style="bar",

    # Slide logo position (inches: x, y, width, height)
    logo_position=(8.2, 0.3, 1.5, 0.5),

    # Chart colors — navy/amber/slate palette
    chart_colors=[
        "#1E293B",  # navy
        "#E7971F",  # amber
        "#3B82F6",  # blue
        "#14B8A6",  # teal
        "#8B5CF6",  # violet
        "#F59E0B",  # warm yellow
    ],
)
