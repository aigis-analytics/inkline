"""Aigis Analytics brand definition."""

from inkline.brands import BaseBrand

AigisBrand = BaseBrand(
    name="aigis",
    display_name="Aigis Analytics",

    # Palette — matches aigis_agents/shared/theme.py + html_exporter.py
    primary="#1A7FA0",        # Readable teal (WCAG AA on white)
    secondary="#39D3BB",      # Bright teal accent
    background="#FFFFFF",     # White documents
    surface="#1B283B",        # Dark navy (table headers, slide headers)
    text="#1A1A1A",           # Near-black body
    muted="#6B7280",          # Grey footer/captions
    light_bg="#F4F6F8",       # Light grey alternating rows
    border="#D1D5DB",         # Light border

    # Typography — Source Sans 3 matches investor pitch branding
    heading_font="Source Sans 3",
    body_font="Source Sans 3",
    mono_font="Consolas",
    heading_size=28,
    body_size=14,

    # Assets
    logo_dark_path="aigis_logo_dark.png",     # White text, for navy bg
    logo_light_path="aigis_logo_light.png",   # Navy text, for white bg
    font_files=["SourceSans3-VariableFont_wght.ttf"],

    # Metadata
    confidentiality="Private & Confidential",
    footer_text="Aigis Analytics Pty Ltd",
    tagline="Domain Intelligence, Deal Certainty",

    # Header — clean document style (logo on white, border separator)
    header_style="document",

    # Slide logo position (x, y, w, h in inches)
    logo_position=(8.5, 0.3, 1.2, 0.4),

    # Chart colors (from theme.py)
    chart_colors=[
        "#3fb950",  # green (oil)
        "#1A7FA0",  # teal
        "#f0883e",  # orange (BOE)
        "#58a6ff",  # blue (gas)
        "#d2a8ff",  # purple
        "#e6c069",  # amber
    ],
)

# Dark-theme palette variant (for slide title slides, dashboards)
AIGIS_DARK = {
    "bg": "#0d1117",
    "surface": "#161b22",
    "border": "#30363d",
    "text": "#e6edf3",
    "muted": "#8b949e",
}
