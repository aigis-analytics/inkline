"""Pre-built Typst slide themes.

Each theme is a dict of color tokens that can be passed to
TypstSlideRenderer or TypstDocumentRenderer. These are the same
themes proven in the Typst POC files.
"""

EXECUTIVE = {
    "name": "Executive",
    "desc": "Premium dark title, purple accent, yellow highlights",
    "bg": "#FAFAFA",
    "title_bg": "#0D0D0D",
    "title_fg": "#FFFFFF",
    "text": "#111111",
    "muted": "#999999",
    "accent": "#8D59E9",
    "accent2": "#EBE021",
    "border": "#E0E0E0",
    "surface": "#FFFFFF",
    "card_fill": "#FFFFFF",
    "heading_font": "Hubot Sans",
    "body_font": "Inter",
}

MINIMALISM = {
    "name": "Minimalism",
    "desc": "Sharp-edged, light gray, black text, no decoration",
    "bg": "#E9E9E9",
    "title_bg": "#111111",
    "title_fg": "#FFFFFF",
    "text": "#111111",
    "muted": "#666666",
    "accent": "#111111",
    "accent2": "#111111",
    "border": "#CCCCCC",
    "surface": "#F5F5F5",
    "card_fill": "#F5F5F5",
    "heading_font": "Inter",
    "body_font": "Inter",
}

NEWSPAPER = {
    "name": "Newspaper",
    "desc": "Modern editorial, white bg, yellow highlights",
    "bg": "#FFFFFF",
    "title_bg": "#111111",
    "title_fg": "#FFFFFF",
    "text": "#111111",
    "muted": "#666666",
    "accent": "#111111",
    "accent2": "#FFCC00",
    "border": "#DDDDDD",
    "surface": "#F5F5F5",
    "card_fill": "#F5F5F5",
    "heading_font": "Hubot Sans",
    "body_font": "Inter",
}

INVESTOR = {
    "name": "Investor",
    "desc": "Fundraising deck — clean, data-focused, blue accent",
    "bg": "#FFFFFF",
    "title_bg": "#1E293B",
    "title_fg": "#FFFFFF",
    "text": "#0F172A",
    "muted": "#64748B",
    "accent": "#2563EB",
    "accent2": "#10B981",
    "border": "#E2E8F0",
    "surface": "#F8FAFC",
    "card_fill": "#F8FAFC",
    "heading_font": "Inter",
    "body_font": "Inter",
}

CONSULTING = {
    "name": "Consulting",
    "desc": "McKinsey-style — white bg, action titles, teal accent",
    "bg": "#FFFFFF",
    "title_bg": "#1A2332",
    "title_fg": "#FFFFFF",
    "text": "#1A2332",
    "muted": "#94A3B8",
    "accent": "#0891B2",
    "accent2": "#EA580C",
    "border": "#CBD5E1",
    "surface": "#F1F5F9",
    "card_fill": "#F1F5F9",
    "heading_font": "Inter",
    "body_font": "Inter",
}

AIGIS = {
    "name": "Aigis Analytics",
    "desc": "Warm beige, Hubot Sans, advisor pitch aesthetic",
    "bg": "#e8e8e3",
    "title_bg": "#e8e8e3",
    "title_fg": "#0c0d0f",
    "text": "#0c0d0f",
    "muted": "#55575a",
    "accent": "#1a3a5c",
    "accent2": "#39d3bb",
    "border": "#c8cac1",
    "surface": "#e8e8e3",
    "card_fill": "#e8e8e3",
    "heading_font": "Hubot Sans",
    "body_font": "Roboto Condensed",
}

AIGIS_DARK = {
    "name": "Aigis Analytics",
    "desc": "Dark variant — dashboards and title slides",
    "bg": "#0d1117",
    "title_bg": "#0d1117",
    "title_fg": "#e6edf3",
    "text": "#e6edf3",
    "muted": "#8b949e",
    "accent": "#39d3bb",
    "accent2": "#1A7FA0",
    "border": "#30363d",
    "surface": "#161b22",
    "card_fill": "#161b22",
    "heading_font": "Hubot Sans",
    "body_font": "Roboto Condensed",
}


# All themes accessible by name
ALL_THEMES = {
    "executive": EXECUTIVE,
    "minimalism": MINIMALISM,
    "newspaper": NEWSPAPER,
    "investor": INVESTOR,
    "consulting": CONSULTING,
    "aigis": AIGIS,
    "aigis_dark": AIGIS_DARK,
}
