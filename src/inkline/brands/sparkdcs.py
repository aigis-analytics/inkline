"""SparkDCS brand definition.

SparkDCS — Data Centre Solutions. Clean, modern, tech-forward branding
with electric blue accent on white. Professional utility-sector aesthetic.
"""

from inkline.brands import BaseBrand

SparkDcsBrand = BaseBrand(
    name="sparkdcs",
    display_name="SparkDCS",

    # Palette — electric blue, clean white, tech-forward
    primary="#0066FF",          # Electric blue
    secondary="#00D4AA",        # Teal-green accent
    background="#FFFFFF",       # White documents
    surface="#0A1628",          # Deep navy (headers, dark surfaces)
    text="#1A1A2E",             # Near-black body
    muted="#6B7B8D",            # Cool grey captions
    light_bg="#F0F4F8",         # Cool light background
    border="#D0D8E0",           # Cool border

    # Typography — clean geometric sans
    heading_font="Inter",
    body_font="Inter",
    mono_font="JetBrains Mono",
    heading_size=28,
    body_size=14,

    # Assets — placeholder until logos are provided
    logo_dark_path="",
    logo_light_path="",
    font_files=[],

    # Metadata
    confidentiality="Confidential",
    footer_text="SparkDCS",
    tagline="Powering the Future of Data",

    # Header style
    header_style="bar",

    # Slide logo position
    logo_position=(8.2, 0.3, 1.5, 0.5),

    # Chart colors — electric blue palette
    chart_colors=[
        "#0066FF",  # electric blue
        "#00D4AA",  # teal-green
        "#FF6B35",  # warm orange
        "#7C3AED",  # violet
        "#06B6D4",  # cyan
        "#F59E0B",  # amber
    ],
)
