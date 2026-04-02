"""Statler Energy brand definition.

Logo: Statler_Logo.png (from Dropbox).
Palette: Energy-sector professional — deep green/teal tones.
Fonts: Pending brand guide — using clean defaults.
"""

from inkline.brands import BaseBrand

StatlerBrand = BaseBrand(
    name="statler",
    display_name="Statler Energy",

    # Palette — energy sector professional
    primary="#1B4D3E",          # Deep forest green
    secondary="#2E8B57",        # Sea green accent
    background="#FFFFFF",       # White documents
    surface="#1B4D3E",          # Deep green (headers)
    text="#1A1A1A",             # Near-black body
    muted="#6B7280",            # Grey captions
    light_bg="#F0F5F2",         # Light green-tinted background
    border="#C8D5CF",           # Soft green border

    # Typography
    heading_font="Inter",
    body_font="Inter",
    mono_font="Roboto Mono",
    heading_size=28,
    body_size=14,

    # Assets — copy logo to assets/ directory
    logo_dark_path="statler_logo_dark.png",
    logo_light_path="statler_logo_light.png",
    font_files=[],

    # Metadata
    confidentiality="Confidential",
    footer_text="Statler Energy",
    tagline="",

    # Slide logo position
    logo_position=(8.2, 0.3, 1.5, 0.5),

    # Chart colors — green/earth tones
    chart_colors=[
        "#1B4D3E",  # forest green
        "#2E8B57",  # sea green
        "#4A90A4",  # steel blue
        "#8B6914",  # dark gold
        "#5F9EA0",  # cadet blue
        "#6B8E23",  # olive
    ],
)
