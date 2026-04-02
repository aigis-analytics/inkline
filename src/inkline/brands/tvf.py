"""Tamarind Village Foundation brand definition."""

from inkline.brands import BaseBrand

TvfBrand = BaseBrand(
    name="tvf",
    display_name="The Tamarind Village Foundation",

    # Palette — from t-v.foundation/index.html CSS vars
    primary="#3D5A3E",        # Olive dark
    secondary="#B8960C",      # Gold
    background="#FAF8F5",     # Cream
    surface="#3D5A3E",        # Olive dark (headers)
    text="#2C2C2C",           # Dark text
    muted="#8A8A7A",          # Muted text
    light_bg="#E8F0E8",       # Olive pale
    border="#D4CFC4",         # Warm border

    # Typography — Cormorant Garamond headings, Lato body
    heading_font="Cormorant Garamond",
    body_font="Lato",
    mono_font="Roboto Mono",
    heading_size=28,
    body_size=14,

    # Assets
    logo_dark_path="tvf_logo_dark.png",    # For olive backgrounds
    logo_light_path="tvf_logo_light.png",  # For cream backgrounds

    # Metadata
    confidentiality="Private & Confidential",
    footer_text="The Tamarind Village Foundation — DIFC",
    tagline="Nurturing Legacy, Sustaining Growth",

    # Slide logo position
    logo_position=(8.5, 0.3, 1.2, 0.4),

    # Chart colors
    chart_colors=[
        "#3D5A3E",  # olive dark
        "#B8960C",  # gold
        "#5B7F5C",  # olive
        "#8BAF8C",  # olive light
        "#D4B94E",  # gold light
        "#6B8A6C",  # mid olive
    ],
)
