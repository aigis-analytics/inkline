"""Ex Machina Investment Partners brand definition.

Fonts: Ailerons (title/display), Agency FB (subheadings/body).
Logo: EMIP_logo.png (dark bg variant), vectorstock logo (light bg variant).
Palette: Sophisticated dark navy/charcoal with gold accents — investment firm aesthetic.
"""

from inkline.brands import BaseBrand

ExMachinaBrand = BaseBrand(
    name="exmachina",
    display_name="Ex Machina Investment Partners",

    # Palette — dark, premium investment firm aesthetic
    primary="#C5A55A",          # Gold (primary accent)
    secondary="#1A1A2E",        # Deep navy
    background="#FFFFFF",       # White documents
    surface="#1A1A2E",          # Deep navy (headers, title slides)
    text="#1A1A1A",             # Near-black body
    muted="#6B7280",            # Grey captions
    light_bg="#F5F5F0",         # Warm off-white
    border="#D4D0C8",           # Warm grey border

    # Typography
    heading_font="Ailerons",
    body_font="Agency FB",
    mono_font="Roboto Mono",
    heading_size=32,
    body_size=14,

    # Assets — copy logos to assets/ directory
    logo_dark_path="emip_logo_dark.png",     # For dark backgrounds
    logo_light_path="emip_logo_light.png",   # For light backgrounds
    font_files=[],

    # Metadata
    confidentiality="Private & Confidential",
    footer_text="Ex Machina Investment Partners",
    tagline="",

    # Slide logo position
    logo_position=(7.8, 0.3, 1.8, 0.6),

    # Chart colors — gold/navy palette
    chart_colors=[
        "#C5A55A",  # gold
        "#1A1A2E",  # navy
        "#4A90A4",  # steel blue
        "#8B7355",  # bronze
        "#2E4057",  # dark blue
        "#D4A574",  # light bronze
    ],
)
