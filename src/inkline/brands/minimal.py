"""Minimal brand — clean, unbranded default.

This is the public default. It uses an indigo accent (#6366F1) with
warm off-white surfaces, Hubot Sans for headings, and Source Sans 3 for
body text — fonts that ship with the package.
"""

from inkline.brands import BaseBrand

MinimalBrand = BaseBrand(
    name="minimal",
    display_name="Inkline",

    # Modern, premium palette — indigo accent on warm off-white
    primary="#6366F1",          # indigo-500 — primary accent
    secondary="#F59E0B",        # amber-500 — secondary accent
    background="#FAFAFA",       # warm off-white
    surface="#0F172A",          # slate-900 (dark headers, title slide)
    text="#0F172A",             # slate-900 body text
    muted="#64748B",            # slate-500 captions
    light_bg="#F1F5F9",         # slate-100 alternating rows / card fill
    border="#E2E8F0",           # slate-200 borders

    # Use fonts that actually ship in src/inkline/assets/fonts/
    heading_font="Hubot Sans",
    body_font="Source Sans 3",
    mono_font="Roboto Mono",
    heading_size=28,
    body_size=14,

    font_files=[
        "fonts/HubotSans-Bold.ttf",
        "fonts/SourceSans3-VariableFont_wght.ttf",
    ],

    confidentiality="",
    footer_text="Branded documents and decks · github.com/u3126117/inkline",
    tagline="Because your output should be as good as your analysis",

    # A modern indigo + amber chart palette
    chart_colors=[
        "#6366F1",  # indigo
        "#F59E0B",  # amber
        "#10B981",  # emerald
        "#EC4899",  # pink
        "#06B6D4",  # cyan
        "#8B5CF6",  # violet
    ],
)
