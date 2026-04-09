"""Comprehensive Typst slide & document theme library.

Each theme is a dict of color tokens that can be passed to
TypstSlideRenderer or TypstDocumentRenderer. Themes are organized
by category for easy discovery.

Categories:
  - Consulting & Professional Services (MBB, Big 4 inspired)
  - Corporate & Finance
  - Tech & Startup
  - Dark Mode
  - Warm & Earthy
  - Cool & Teal
  - Nature & Green
  - Creative & Gradient
  - Editorial & Newspaper
  - Pastel & Soft
  - Gold & Luxury
  - Minimal & Monochrome
  - Brand-specific (Aigis variants)

Usage:
    from inkline.typst.themes import ALL_THEMES, STRIPE_DARK
    theme = ALL_THEMES["stripe_dark"]
"""

# ═══════════════════════════════════════════════════════════════════════
# CONSULTING & PROFESSIONAL SERVICES
# ═══════════════════════════════════════════════════════════════════════

MCKINSEY = {
    "name": "McKinsey",
    "desc": "Strategy consulting — blue ribbon, Georgia headings, data-forward",
    "bg": "#FFFFFF",
    "title_bg": "#051C2C",
    "title_fg": "#FFFFFF",
    "text": "#222222",
    "muted": "#A2AAAD",
    "accent": "#2251FF",
    "accent2": "#F3C13A",
    "border": "#D1D5DB",
    "surface": "#F5F5F5",
    "card_fill": "#F5F5F5",
    "heading_font": "Inter",
    "body_font": "Inter",
}

BCG = {
    "name": "BCG",
    "desc": "Boston Consulting Group — green accent, chart-forward",
    "bg": "#FFFFFF",
    "title_bg": "#000000",
    "title_fg": "#FFFFFF",
    "text": "#333333",
    "muted": "#666666",
    "accent": "#147B58",
    "accent2": "#147B58",
    "border": "#D1D5DB",
    "surface": "#F5F5F5",
    "card_fill": "#F5F5F5",
    "heading_font": "Inter",
    "body_font": "Inter",
}

BAIN = {
    "name": "Bain",
    "desc": "Bain & Company — red accent, clean white",
    "bg": "#FFFFFF",
    "title_bg": "#000000",
    "title_fg": "#FFFFFF",
    "text": "#333333",
    "muted": "#666666",
    "accent": "#CC0000",
    "accent2": "#CB2026",
    "border": "#D1D5DB",
    "surface": "#F5F5F5",
    "card_fill": "#F5F5F5",
    "heading_font": "Inter",
    "body_font": "Inter",
}

DELOITTE = {
    "name": "Deloitte",
    "desc": "Deloitte — green on black, professional services",
    "bg": "#FFFFFF",
    "title_bg": "#000000",
    "title_fg": "#FFFFFF",
    "text": "#000000",
    "muted": "#666666",
    "accent": "#86BC24",
    "accent2": "#86BC24",
    "border": "#D1D5DB",
    "surface": "#F5F5F5",
    "card_fill": "#F5F5F5",
    "heading_font": "Inter",
    "body_font": "Inter",
}

PWC = {
    "name": "PwC",
    "desc": "PricewaterhouseCoopers — warm orange, multi-accent",
    "bg": "#FFFFFF",
    "title_bg": "#000000",
    "title_fg": "#FFFFFF",
    "text": "#000000",
    "muted": "#666666",
    "accent": "#E88D14",
    "accent2": "#E669A2",
    "border": "#D1D5DB",
    "surface": "#F5F5F5",
    "card_fill": "#F5F5F5",
    "heading_font": "Inter",
    "body_font": "Inter",
}

EY = {
    "name": "Ernst & Young",
    "desc": "EY — yellow on charcoal, bold contrast",
    "bg": "#FFFFFF",
    "title_bg": "#161D23",
    "title_fg": "#FFFFFF",
    "text": "#161D23",
    "muted": "#6B7280",
    "accent": "#FFE600",
    "accent2": "#161D23",
    "border": "#D1D5DB",
    "surface": "#F5F5F5",
    "card_fill": "#F5F5F5",
    "heading_font": "Inter",
    "body_font": "Inter",
}

KPMG = {
    "name": "KPMG",
    "desc": "KPMG — deep blue, formal corporate",
    "bg": "#FFFFFF",
    "title_bg": "#00338D",
    "title_fg": "#FFFFFF",
    "text": "#000000",
    "muted": "#666666",
    "accent": "#00338D",
    "accent2": "#00338D",
    "border": "#D1D5DB",
    "surface": "#F5F5F5",
    "card_fill": "#F5F5F5",
    "heading_font": "Inter",
    "body_font": "Inter",
}

# Composite MBB-inspired theme
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

# ═══════════════════════════════════════════════════════════════════════
# CORPORATE & FINANCE
# ═══════════════════════════════════════════════════════════════════════

NAVY_GOLD = {
    "name": "Navy & Gold",
    "desc": "Corporate navy with gold accent — finance, boardroom",
    "bg": "#FFFFFF",
    "title_bg": "#113F67",
    "title_fg": "#FFFFFF",
    "text": "#21325E",
    "muted": "#6B7280",
    "accent": "#113F67",
    "accent2": "#F1D00A",
    "border": "#D1D5DB",
    "surface": "#F3F9FB",
    "card_fill": "#F3F9FB",
    "heading_font": "Inter",
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

GOLDMAN = {
    "name": "Goldman Sachs",
    "desc": "Investment banking — blue on white, data-dense",
    "bg": "#FFFFFF",
    "title_bg": "#003A70",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
    "accent": "#003A70",
    "accent2": "#7BAFD4",
    "border": "#D1D5DB",
    "surface": "#F5F7FA",
    "card_fill": "#F5F7FA",
    "heading_font": "Inter",
    "body_font": "Inter",
}

JPMORGAN = {
    "name": "JP Morgan",
    "desc": "Private banking — dark navy, trust-building formality",
    "bg": "#FFFFFF",
    "title_bg": "#0C2340",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
    "accent": "#0C2340",
    "accent2": "#B39656",
    "border": "#D1D5DB",
    "surface": "#F5F5F5",
    "card_fill": "#F5F5F5",
    "heading_font": "Inter",
    "body_font": "Inter",
}

PRIVATE_EQUITY = {
    "name": "Private Equity",
    "desc": "PE / VC — dark slate, green accent for returns",
    "bg": "#FFFFFF",
    "title_bg": "#1B2A3D",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#64748B",
    "accent": "#059669",
    "accent2": "#1B2A3D",
    "border": "#E2E8F0",
    "surface": "#F8FAFC",
    "card_fill": "#F8FAFC",
    "heading_font": "Inter",
    "body_font": "Inter",
}

BOARDROOM = {
    "name": "Boardroom",
    "desc": "Executive board deck — charcoal, restrained, serif feel",
    "bg": "#FFFFFF",
    "title_bg": "#1F2937",
    "title_fg": "#FFFFFF",
    "text": "#111827",
    "muted": "#6B7280",
    "accent": "#1F2937",
    "accent2": "#D97706",
    "border": "#D1D5DB",
    "surface": "#F9FAFB",
    "card_fill": "#F9FAFB",
    "heading_font": "Inter",
    "body_font": "Inter",
}

# ═══════════════════════════════════════════════════════════════════════
# TECH & STARTUP
# ═══════════════════════════════════════════════════════════════════════

STRIPE = {
    "name": "Stripe",
    "desc": "Stripe-inspired — indigo accent on white, premium fintech",
    "bg": "#FFFFFF",
    "title_bg": "#0A2540",
    "title_fg": "#FFFFFF",
    "text": "#0A2540",
    "muted": "#6B7280",
    "accent": "#635BFF",
    "accent2": "#00D4AA",
    "border": "#E2E8F0",
    "surface": "#F6F9FC",
    "card_fill": "#F6F9FC",
    "heading_font": "Inter",
    "body_font": "Inter",
}

STRIPE_DARK = {
    "name": "Stripe Dark",
    "desc": "Stripe dark mode — deep navy, vibrant indigo accents",
    "bg": "#0A2540",
    "title_bg": "#0A2540",
    "title_fg": "#FFFFFF",
    "text": "#E6EDF3",
    "muted": "#8B949E",
    "accent": "#635BFF",
    "accent2": "#00D4AA",
    "border": "#1B3A5C",
    "surface": "#0F3460",
    "card_fill": "#0F3460",
    "heading_font": "Inter",
    "body_font": "Inter",
}

LINEAR = {
    "name": "Linear",
    "desc": "Linear-inspired — dark-first, indigo accent, developer tool",
    "bg": "#101012",
    "title_bg": "#101012",
    "title_fg": "#FFFFFF",
    "text": "#E6EDF3",
    "muted": "#878A94",
    "accent": "#5E6AD2",
    "accent2": "#8299FF",
    "border": "#222326",
    "surface": "#1A1A1E",
    "card_fill": "#1A1A1E",
    "heading_font": "Inter",
    "body_font": "Inter",
}

VERCEL = {
    "name": "Vercel",
    "desc": "Vercel / Geist — radical minimalism, black and white only",
    "bg": "#FFFFFF",
    "title_bg": "#000000",
    "title_fg": "#FFFFFF",
    "text": "#000000",
    "muted": "#666666",
    "accent": "#000000",
    "accent2": "#000000",
    "border": "#EAEAEA",
    "surface": "#FAFAFA",
    "card_fill": "#FAFAFA",
    "heading_font": "Inter",
    "body_font": "Inter",
}

VERCEL_DARK = {
    "name": "Vercel Dark",
    "desc": "Vercel dark — pure black, white text, zero decoration",
    "bg": "#000000",
    "title_bg": "#000000",
    "title_fg": "#FFFFFF",
    "text": "#EDEDED",
    "muted": "#888888",
    "accent": "#FFFFFF",
    "accent2": "#FFFFFF",
    "border": "#333333",
    "surface": "#111111",
    "card_fill": "#111111",
    "heading_font": "Inter",
    "body_font": "Inter",
}

NOTION = {
    "name": "Notion",
    "desc": "Notion-inspired — warm minimalism, paper-like canvas",
    "bg": "#FFFFFF",
    "title_bg": "#191919",
    "title_fg": "#FFFFFF",
    "text": "#191919",
    "muted": "#999999",
    "accent": "#0075DE",
    "accent2": "#0F7B6C",
    "border": "#E3E2DE",
    "surface": "#F7F6F3",
    "card_fill": "#F7F6F3",
    "heading_font": "Inter",
    "body_font": "Inter",
}

AIRBNB = {
    "name": "Airbnb",
    "desc": "Airbnb-inspired — coral red accent, clean white",
    "bg": "#FFFFFF",
    "title_bg": "#222222",
    "title_fg": "#FFFFFF",
    "text": "#484848",
    "muted": "#767676",
    "accent": "#FF385C",
    "accent2": "#00A699",
    "border": "#DDDDDD",
    "surface": "#F7F7F7",
    "card_fill": "#F7F7F7",
    "heading_font": "Inter",
    "body_font": "Inter",
}

MODERN_STARTUP = {
    "name": "Modern Startup",
    "desc": "Clean tech pitch — blue primary, coral accent, Inter",
    "bg": "#FFFFFF",
    "title_bg": "#1A1A2E",
    "title_fg": "#FFFFFF",
    "text": "#131314",
    "muted": "#6B7280",
    "accent": "#0045F8",
    "accent2": "#FF6B6B",
    "border": "#E5E7EB",
    "surface": "#F8F9FA",
    "card_fill": "#F8F9FA",
    "heading_font": "Inter",
    "body_font": "Inter",
}

GITHUB = {
    "name": "GitHub",
    "desc": "GitHub Primer — clean, developer-friendly, green accent",
    "bg": "#FFFFFF",
    "title_bg": "#24292F",
    "title_fg": "#FFFFFF",
    "text": "#24292F",
    "muted": "#656D76",
    "accent": "#0969DA",
    "accent2": "#1A7F37",
    "border": "#D0D7DE",
    "surface": "#F6F8FA",
    "card_fill": "#F6F8FA",
    "heading_font": "Inter",
    "body_font": "Inter",
}

GITHUB_DARK = {
    "name": "GitHub Dark",
    "desc": "GitHub dark mode — dark canvas, blue links",
    "bg": "#0D1117",
    "title_bg": "#0D1117",
    "title_fg": "#E6EDF3",
    "text": "#E6EDF3",
    "muted": "#8B949E",
    "accent": "#58A6FF",
    "accent2": "#3FB950",
    "border": "#30363D",
    "surface": "#161B22",
    "card_fill": "#161B22",
    "heading_font": "Inter",
    "body_font": "Inter",
}

# ═══════════════════════════════════════════════════════════════════════
# DARK MODE
# ═══════════════════════════════════════════════════════════════════════

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

MIDNIGHT = {
    "name": "Midnight",
    "desc": "Deep dark — navy black, subtle blue accent",
    "bg": "#0F172A",
    "title_bg": "#0F172A",
    "title_fg": "#F1F5F9",
    "text": "#E2E8F0",
    "muted": "#64748B",
    "accent": "#3B82F6",
    "accent2": "#8B5CF6",
    "border": "#1E293B",
    "surface": "#1E293B",
    "card_fill": "#1E293B",
    "heading_font": "Inter",
    "body_font": "Inter",
}

CARBON = {
    "name": "Carbon",
    "desc": "IBM Carbon-inspired — dark gray, blue accent, industrial",
    "bg": "#161616",
    "title_bg": "#161616",
    "title_fg": "#F4F4F4",
    "text": "#F4F4F4",
    "muted": "#8D8D8D",
    "accent": "#0F62FE",
    "accent2": "#42BE65",
    "border": "#393939",
    "surface": "#262626",
    "card_fill": "#262626",
    "heading_font": "Inter",
    "body_font": "Inter",
}

OBSIDIAN = {
    "name": "Obsidian",
    "desc": "Pitch black with violet accent — premium dark",
    "bg": "#0A0A0A",
    "title_bg": "#0A0A0A",
    "title_fg": "#FAFAFA",
    "text": "#E5E5E5",
    "muted": "#737373",
    "accent": "#A855F7",
    "accent2": "#F97316",
    "border": "#262626",
    "surface": "#171717",
    "card_fill": "#171717",
    "heading_font": "Inter",
    "body_font": "Inter",
}

DARK_EXECUTIVE = {
    "name": "Dark Executive",
    "desc": "Boardroom dark — charcoal with red accent",
    "bg": "#1A1A1A",
    "title_bg": "#1A1A1A",
    "title_fg": "#FFFFFF",
    "text": "#E5E5E5",
    "muted": "#999999",
    "accent": "#E33737",
    "accent2": "#CCCBCB",
    "border": "#333333",
    "surface": "#292929",
    "card_fill": "#292929",
    "heading_font": "Inter",
    "body_font": "Inter",
}

DARK_TEAL = {
    "name": "Dark Teal",
    "desc": "Dark mode with teal green accent — tech/finance",
    "bg": "#191A19",
    "title_bg": "#191A19",
    "title_fg": "#FFFFFF",
    "text": "#E5E5E5",
    "muted": "#8B949E",
    "accent": "#4E9F3D",
    "accent2": "#1E5128",
    "border": "#2D2D2D",
    "surface": "#1E2520",
    "card_fill": "#1E2520",
    "heading_font": "Inter",
    "body_font": "Inter",
}

DARK_ORANGE = {
    "name": "Dark Orange",
    "desc": "Dark charcoal with energy orange — startup, bold",
    "bg": "#222831",
    "title_bg": "#222831",
    "title_fg": "#FFFFFF",
    "text": "#F2F2F2",
    "muted": "#8B949E",
    "accent": "#F96D00",
    "accent2": "#F96D00",
    "border": "#393E46",
    "surface": "#393E46",
    "card_fill": "#393E46",
    "heading_font": "Inter",
    "body_font": "Inter",
}

NORD_DARK = {
    "name": "Nord Dark",
    "desc": "Nord polar night — arctic blue palette, calm dark",
    "bg": "#2E3440",
    "title_bg": "#2E3440",
    "title_fg": "#ECEFF4",
    "text": "#D8DEE9",
    "muted": "#7B88A1",
    "accent": "#88C0D0",
    "accent2": "#A3BE8C",
    "border": "#3B4252",
    "surface": "#3B4252",
    "card_fill": "#3B4252",
    "heading_font": "Inter",
    "body_font": "Inter",
}

DRACULA = {
    "name": "Dracula",
    "desc": "Dracula theme — purple on dark, developer aesthetic",
    "bg": "#282A36",
    "title_bg": "#282A36",
    "title_fg": "#F8F8F2",
    "text": "#F8F8F2",
    "muted": "#6272A4",
    "accent": "#BD93F9",
    "accent2": "#FF79C6",
    "border": "#44475A",
    "surface": "#44475A",
    "card_fill": "#44475A",
    "heading_font": "Inter",
    "body_font": "Inter",
}

CATPPUCCIN_MOCHA = {
    "name": "Catppuccin Mocha",
    "desc": "Catppuccin mocha — warm dark, mauve accent",
    "bg": "#1E1E2E",
    "title_bg": "#1E1E2E",
    "title_fg": "#CDD6F4",
    "text": "#CDD6F4",
    "muted": "#6C7086",
    "accent": "#CBA6F7",
    "accent2": "#F38BA8",
    "border": "#313244",
    "surface": "#313244",
    "card_fill": "#313244",
    "heading_font": "Inter",
    "body_font": "Inter",
}

# ═══════════════════════════════════════════════════════════════════════
# WARM & EARTHY
# ═══════════════════════════════════════════════════════════════════════

TERRACOTTA = {
    "name": "Terracotta",
    "desc": "Warm earth tones — beige, brown, organic feel",
    "bg": "#FDF8F4",
    "title_bg": "#5C3D2E",
    "title_fg": "#FFFFFF",
    "text": "#3D2B1F",
    "muted": "#8B7355",
    "accent": "#C67B5C",
    "accent2": "#8B5E3C",
    "border": "#D4C4B0",
    "surface": "#F5EDE4",
    "card_fill": "#F5EDE4",
    "heading_font": "Inter",
    "body_font": "Inter",
}

CREAM = {
    "name": "Cream",
    "desc": "Warm cream — elegant, minimalist, luxury feel",
    "bg": "#FBF9F1",
    "title_bg": "#2C2C2C",
    "title_fg": "#FFFFFF",
    "text": "#2C2C2C",
    "muted": "#8B8B7A",
    "accent": "#2C2C2C",
    "accent2": "#B89B6E",
    "border": "#E0DCD0",
    "surface": "#F5F0E6",
    "card_fill": "#F5F0E6",
    "heading_font": "Inter",
    "body_font": "Inter",
}

MOCHA = {
    "name": "Mocha",
    "desc": "Coffee tones — warm brown, gold accent, cozy",
    "bg": "#2B2118",
    "title_bg": "#2B2118",
    "title_fg": "#F5E6D3",
    "text": "#F5E6D3",
    "muted": "#A08B74",
    "accent": "#D4A76A",
    "accent2": "#C67B5C",
    "border": "#3D2E21",
    "surface": "#3D2E21",
    "card_fill": "#3D2E21",
    "heading_font": "Inter",
    "body_font": "Inter",
}

KRAFT = {
    "name": "Kraft",
    "desc": "Kraft paper — recycled look, sustainable, organic",
    "bg": "#EDE0D4",
    "title_bg": "#3E2723",
    "title_fg": "#FFFFFF",
    "text": "#3E2723",
    "muted": "#795548",
    "accent": "#3E2723",
    "accent2": "#795548",
    "border": "#BCAAA4",
    "surface": "#D7CCC8",
    "card_fill": "#D7CCC8",
    "heading_font": "Inter",
    "body_font": "Inter",
}

OATMEAL = {
    "name": "Oatmeal",
    "desc": "Light warm neutral — quiet, soft, classic elegance",
    "bg": "#F8F4EE",
    "title_bg": "#2D2926",
    "title_fg": "#FFFFFF",
    "text": "#2D2926",
    "muted": "#8A8580",
    "accent": "#2D2926",
    "accent2": "#A68A64",
    "border": "#DDD8D0",
    "surface": "#EFEBE4",
    "card_fill": "#EFEBE4",
    "heading_font": "Inter",
    "body_font": "Inter",
}

DUNE = {
    "name": "Dune",
    "desc": "Sandy desert — warm beige, gold accent, luxe minimal",
    "bg": "#F5F0E8",
    "title_bg": "#1A1611",
    "title_fg": "#F5F0E8",
    "text": "#1A1611",
    "muted": "#8B8170",
    "accent": "#B8860B",
    "accent2": "#1A1611",
    "border": "#D4CAB8",
    "surface": "#EDE5D8",
    "card_fill": "#EDE5D8",
    "heading_font": "Inter",
    "body_font": "Inter",
}

CLEMENTA = {
    "name": "Clementa",
    "desc": "Pumpkin and chocolate — warm retro, optimistic",
    "bg": "#FFF8F0",
    "title_bg": "#3C2415",
    "title_fg": "#FFFFFF",
    "text": "#3C2415",
    "muted": "#8B7355",
    "accent": "#D2691E",
    "accent2": "#E8A832",
    "border": "#D4C0A8",
    "surface": "#F5EDE0",
    "card_fill": "#F5EDE0",
    "heading_font": "Inter",
    "body_font": "Inter",
}

# ═══════════════════════════════════════════════════════════════════════
# COOL & TEAL / BLUE
# ═══════════════════════════════════════════════════════════════════════

ARCTIC = {
    "name": "Arctic",
    "desc": "Cool blue-white — fresh, clean, Nordic",
    "bg": "#F0F6FF",
    "title_bg": "#1E3A5F",
    "title_fg": "#FFFFFF",
    "text": "#1E3A5F",
    "muted": "#6B89A8",
    "accent": "#2196F3",
    "accent2": "#00BCD4",
    "border": "#C8DAE8",
    "surface": "#E3EDF7",
    "card_fill": "#E3EDF7",
    "heading_font": "Inter",
    "body_font": "Inter",
}

BREEZE = {
    "name": "Breeze",
    "desc": "Soft sky blue — gentle, modern, fresh",
    "bg": "#F5FAFF",
    "title_bg": "#1565C0",
    "title_fg": "#FFFFFF",
    "text": "#1A237E",
    "muted": "#5C6BC0",
    "accent": "#1565C0",
    "accent2": "#42A5F5",
    "border": "#BBDEFB",
    "surface": "#E3F2FD",
    "card_fill": "#E3F2FD",
    "heading_font": "Inter",
    "body_font": "Inter",
}

OCEAN = {
    "name": "Ocean",
    "desc": "Deep ocean — navy to teal gradient feel",
    "bg": "#FFFFFF",
    "title_bg": "#0D2137",
    "title_fg": "#FFFFFF",
    "text": "#0D2137",
    "muted": "#5A7A94",
    "accent": "#0077B6",
    "accent2": "#00B4D8",
    "border": "#C4DFE6",
    "surface": "#EAF4F8",
    "card_fill": "#EAF4F8",
    "heading_font": "Inter",
    "body_font": "Inter",
}

MARINE = {
    "name": "Marine",
    "desc": "Navy marine — dark blue, white, classic nautical",
    "bg": "#0B1D3A",
    "title_bg": "#0B1D3A",
    "title_fg": "#FFFFFF",
    "text": "#E5ECF4",
    "muted": "#7B93AD",
    "accent": "#3B82F6",
    "accent2": "#FFFFFF",
    "border": "#1E3A5F",
    "surface": "#132D5E",
    "card_fill": "#132D5E",
    "heading_font": "Inter",
    "body_font": "Inter",
}

TEAL_CORPORATE = {
    "name": "Teal Corporate",
    "desc": "Reliable teal — trust, branding, corporate",
    "bg": "#FFFFFF",
    "title_bg": "#05668D",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
    "accent": "#028090",
    "accent2": "#00A896",
    "border": "#D1D5DB",
    "surface": "#F0FAFA",
    "card_fill": "#F0FAFA",
    "heading_font": "Inter",
    "body_font": "Inter",
}

NORD_LIGHT = {
    "name": "Nord Light",
    "desc": "Nord snow storm — soft arctic blue, calm",
    "bg": "#ECEFF4",
    "title_bg": "#2E3440",
    "title_fg": "#ECEFF4",
    "text": "#2E3440",
    "muted": "#4C566A",
    "accent": "#5E81AC",
    "accent2": "#88C0D0",
    "border": "#D8DEE9",
    "surface": "#E5E9F0",
    "card_fill": "#E5E9F0",
    "heading_font": "Inter",
    "body_font": "Inter",
}

# ═══════════════════════════════════════════════════════════════════════
# NATURE & GREEN
# ═══════════════════════════════════════════════════════════════════════

SAGE = {
    "name": "Sage",
    "desc": "Sage green — calm, professional, nature-inspired",
    "bg": "#F5F7F4",
    "title_bg": "#2D4739",
    "title_fg": "#FFFFFF",
    "text": "#2D4739",
    "muted": "#6B7C6E",
    "accent": "#4A7C59",
    "accent2": "#2D4739",
    "border": "#C8D5C4",
    "surface": "#E8EDE6",
    "card_fill": "#E8EDE6",
    "heading_font": "Inter",
    "body_font": "Inter",
}

FOREST = {
    "name": "Forest",
    "desc": "Deep forest green — dark, rich, environmental",
    "bg": "#0B4524",
    "title_bg": "#0B4524",
    "title_fg": "#DAFAE5",
    "text": "#DAFAE5",
    "muted": "#6EAB7E",
    "accent": "#34D399",
    "accent2": "#DAFAE5",
    "border": "#166534",
    "surface": "#14532D",
    "card_fill": "#14532D",
    "heading_font": "Inter",
    "body_font": "Inter",
}

MOSS = {
    "name": "Moss",
    "desc": "Moss & mist — olive on black, sophisticated earth",
    "bg": "#FFFFFF",
    "title_bg": "#1A2E1A",
    "title_fg": "#FFFFFF",
    "text": "#1A2E1A",
    "muted": "#5C6B5C",
    "accent": "#3D5C3D",
    "accent2": "#7B9E6E",
    "border": "#C4D4B8",
    "surface": "#EEF2EA",
    "card_fill": "#EEF2EA",
    "heading_font": "Inter",
    "body_font": "Inter",
}

SPROUT = {
    "name": "Sprout",
    "desc": "Fresh mint green — clean, eco-friendly, modern",
    "bg": "#F0FFF4",
    "title_bg": "#065F46",
    "title_fg": "#FFFFFF",
    "text": "#064E3B",
    "muted": "#6B7280",
    "accent": "#10B981",
    "accent2": "#059669",
    "border": "#A7F3D0",
    "surface": "#D1FAE5",
    "card_fill": "#D1FAE5",
    "heading_font": "Inter",
    "body_font": "Inter",
}

# ═══════════════════════════════════════════════════════════════════════
# CREATIVE & GRADIENT
# ═══════════════════════════════════════════════════════════════════════

AURORA = {
    "name": "Aurora",
    "desc": "Northern lights — dark with fuchsia-to-blue gradient feel",
    "bg": "#0F0720",
    "title_bg": "#0F0720",
    "title_fg": "#FFFFFF",
    "text": "#E5E7EB",
    "muted": "#9CA3AF",
    "accent": "#C026D3",
    "accent2": "#3B82F6",
    "border": "#1E1040",
    "surface": "#1A0D35",
    "card_fill": "#1A0D35",
    "heading_font": "Inter",
    "body_font": "Inter",
}

NEBULA = {
    "name": "Nebula",
    "desc": "Space nebula — deep purple, cosmic blue accents",
    "bg": "#0D0221",
    "title_bg": "#0D0221",
    "title_fg": "#FFFFFF",
    "text": "#E5E7EB",
    "muted": "#8B8DA0",
    "accent": "#7C3AED",
    "accent2": "#2563EB",
    "border": "#1E0A3E",
    "surface": "#150838",
    "card_fill": "#150838",
    "heading_font": "Inter",
    "body_font": "Inter",
}

ELECTRIC = {
    "name": "Electric",
    "desc": "Electric neon — dark bg, vibrant pink-orange gradient feel",
    "bg": "#111111",
    "title_bg": "#111111",
    "title_fg": "#FFFFFF",
    "text": "#F5F5F5",
    "muted": "#999999",
    "accent": "#FF6B6B",
    "accent2": "#4ECDC4",
    "border": "#333333",
    "surface": "#1A1A1A",
    "card_fill": "#1A1A1A",
    "heading_font": "Inter",
    "body_font": "Inter",
}

NEON = {
    "name": "Neon",
    "desc": "Neon green on black — hacker, cyberpunk, terminal",
    "bg": "#0A0A0A",
    "title_bg": "#0A0A0A",
    "title_fg": "#39FF14",
    "text": "#E5E5E5",
    "muted": "#666666",
    "accent": "#39FF14",
    "accent2": "#00FFFF",
    "border": "#1A1A1A",
    "surface": "#111111",
    "card_fill": "#111111",
    "heading_font": "Inter",
    "body_font": "Inter",
}

CORAL = {
    "name": "Coral",
    "desc": "Coral glow — warm pink-peach, fresh and uplifting",
    "bg": "#FFF5F5",
    "title_bg": "#831843",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#9CA3AF",
    "accent": "#F43F5E",
    "accent2": "#FB923C",
    "border": "#FECDD3",
    "surface": "#FFE4E6",
    "card_fill": "#FFE4E6",
    "heading_font": "Inter",
    "body_font": "Inter",
}

SUNSET = {
    "name": "Sunset",
    "desc": "Sunset gradient feel — warm orange to pink",
    "bg": "#FFF7ED",
    "title_bg": "#7C2D12",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#9CA3AF",
    "accent": "#EA580C",
    "accent2": "#E11D48",
    "border": "#FED7AA",
    "surface": "#FFEDD5",
    "card_fill": "#FFEDD5",
    "heading_font": "Inter",
    "body_font": "Inter",
}

# ═══════════════════════════════════════════════════════════════════════
# EDITORIAL & NEWSPAPER
# ═══════════════════════════════════════════════════════════════════════

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

EDITORIAL = {
    "name": "Editorial",
    "desc": "Magazine editorial — graphite, taupe, sophisticated",
    "bg": "#FAFAF8",
    "title_bg": "#1A1A18",
    "title_fg": "#FAFAF8",
    "text": "#1A1A18",
    "muted": "#6B6B60",
    "accent": "#1A1A18",
    "accent2": "#C9A96E",
    "border": "#D8D5CC",
    "surface": "#F0EDE6",
    "card_fill": "#F0EDE6",
    "heading_font": "Inter",
    "body_font": "Inter",
}

FINANCIAL_TIMES = {
    "name": "Financial Times",
    "desc": "FT-inspired — salmon pink, serif feel, financial data",
    "bg": "#FFF1E5",
    "title_bg": "#1A0E00",
    "title_fg": "#FFF1E5",
    "text": "#33302E",
    "muted": "#726F6A",
    "accent": "#0D7680",
    "accent2": "#990F3D",
    "border": "#C9B39C",
    "surface": "#F2DFCE",
    "card_fill": "#F2DFCE",
    "heading_font": "Inter",
    "body_font": "Inter",
}

ECONOMIST = {
    "name": "Economist",
    "desc": "Economist-inspired — red accent, serious editorial",
    "bg": "#FFFFFF",
    "title_bg": "#1D1D1D",
    "title_fg": "#FFFFFF",
    "text": "#1D1D1D",
    "muted": "#6B6B6B",
    "accent": "#E3120B",
    "accent2": "#1D1D1D",
    "border": "#D5D5D5",
    "surface": "#F2F2F2",
    "card_fill": "#F2F2F2",
    "heading_font": "Inter",
    "body_font": "Inter",
}

# ═══════════════════════════════════════════════════════════════════════
# PASTEL & SOFT
# ═══════════════════════════════════════════════════════════════════════

LAVENDER = {
    "name": "Lavender",
    "desc": "Soft lavender — feminine, elegant, pastel purple",
    "bg": "#FAF5FF",
    "title_bg": "#581C87",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#9CA3AF",
    "accent": "#9333EA",
    "accent2": "#A855F7",
    "border": "#E9D5FF",
    "surface": "#F3E8FF",
    "card_fill": "#F3E8FF",
    "heading_font": "Inter",
    "body_font": "Inter",
}

BLUSH = {
    "name": "Blush",
    "desc": "Soft pink blush — warm, feminine, wedding/lifestyle",
    "bg": "#FFF5F7",
    "title_bg": "#881337",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#9CA3AF",
    "accent": "#DB2777",
    "accent2": "#F472B6",
    "border": "#FBCFE8",
    "surface": "#FCE7F3",
    "card_fill": "#FCE7F3",
    "heading_font": "Inter",
    "body_font": "Inter",
}

PEACH = {
    "name": "Peach",
    "desc": "Warm peach — friendly, playful, approachable",
    "bg": "#FFF7ED",
    "title_bg": "#9A3412",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#9CA3AF",
    "accent": "#F97316",
    "accent2": "#FB923C",
    "border": "#FDBA74",
    "surface": "#FFEDD5",
    "card_fill": "#FFEDD5",
    "heading_font": "Inter",
    "body_font": "Inter",
}

SEAFOAM = {
    "name": "Seafoam",
    "desc": "Pastel teal — fresh, aquatic, light and clean",
    "bg": "#F0FDFA",
    "title_bg": "#134E4A",
    "title_fg": "#FFFFFF",
    "text": "#134E4A",
    "muted": "#5EEAD4",
    "accent": "#14B8A6",
    "accent2": "#0D9488",
    "border": "#99F6E4",
    "surface": "#CCFBF1",
    "card_fill": "#CCFBF1",
    "heading_font": "Inter",
    "body_font": "Inter",
}

DAYDREAM = {
    "name": "Daydream",
    "desc": "Dreamy gradient pastel — purple-blue-pink soft",
    "bg": "#F8F5FF",
    "title_bg": "#312E81",
    "title_fg": "#FFFFFF",
    "text": "#1E1B4B",
    "muted": "#818CF8",
    "accent": "#6366F1",
    "accent2": "#EC4899",
    "border": "#C7D2FE",
    "surface": "#EEF2FF",
    "card_fill": "#EEF2FF",
    "heading_font": "Inter",
    "body_font": "Inter",
}

SPECTRUM = {
    "name": "Spectrum",
    "desc": "Rainbow pastel — playful, vibrant, inclusive",
    "bg": "#FEFEFE",
    "title_bg": "#2D1B69",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#9CA3AF",
    "accent": "#8B5CF6",
    "accent2": "#EC4899",
    "border": "#E5E7EB",
    "surface": "#F3F4F6",
    "card_fill": "#F3F4F6",
    "heading_font": "Inter",
    "body_font": "Inter",
    "chart_colors": ["#8B5CF6", "#EC4899", "#06B6D4", "#10B981", "#F59E0B", "#EF4444"],
}

# ═══════════════════════════════════════════════════════════════════════
# GOLD & LUXURY
# ═══════════════════════════════════════════════════════════════════════

AURUM = {
    "name": "Aurum",
    "desc": "Black and gold — luxury, premium, formal events",
    "bg": "#0A0A0A",
    "title_bg": "#0A0A0A",
    "title_fg": "#D4AF37",
    "text": "#E5E5E5",
    "muted": "#999999",
    "accent": "#D4AF37",
    "accent2": "#B8860B",
    "border": "#2A2A2A",
    "surface": "#1A1A1A",
    "card_fill": "#1A1A1A",
    "heading_font": "Inter",
    "body_font": "Inter",
}

GOLD_LEAF = {
    "name": "Gold Leaf",
    "desc": "Champagne and ivory — subtle luxury, elegant",
    "bg": "#FFFFF0",
    "title_bg": "#1C1C1C",
    "title_fg": "#D4AF37",
    "text": "#1C1C1C",
    "muted": "#8B8B7A",
    "accent": "#D4AF37",
    "accent2": "#B8860B",
    "border": "#E8E0C8",
    "surface": "#F5F0E0",
    "card_fill": "#F5F0E0",
    "heading_font": "Inter",
    "body_font": "Inter",
}

WINE = {
    "name": "Wine",
    "desc": "Deep burgundy — rich, sophisticated, luxury brand",
    "bg": "#1A0A0A",
    "title_bg": "#1A0A0A",
    "title_fg": "#F5E6E0",
    "text": "#F5E6E0",
    "muted": "#A08080",
    "accent": "#8B1A1A",
    "accent2": "#D4AF37",
    "border": "#2D1515",
    "surface": "#2D1515",
    "card_fill": "#2D1515",
    "heading_font": "Inter",
    "body_font": "Inter",
}

# ═══════════════════════════════════════════════════════════════════════
# MINIMAL & MONOCHROME
# ═══════════════════════════════════════════════════════════════════════

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

PEARL = {
    "name": "Pearl",
    "desc": "White pearl — pristine, high-contrast, luxe minimal",
    "bg": "#FFFFFF",
    "title_bg": "#000000",
    "title_fg": "#FFFFFF",
    "text": "#111111",
    "muted": "#888888",
    "accent": "#111111",
    "accent2": "#111111",
    "border": "#E5E5E5",
    "surface": "#F8F8F8",
    "card_fill": "#F8F8F8",
    "heading_font": "Inter",
    "body_font": "Inter",
}

SLATE = {
    "name": "Slate",
    "desc": "Gray slate — serious, corporate, geometric",
    "bg": "#F8FAFC",
    "title_bg": "#1E293B",
    "title_fg": "#FFFFFF",
    "text": "#1E293B",
    "muted": "#64748B",
    "accent": "#334155",
    "accent2": "#475569",
    "border": "#CBD5E1",
    "surface": "#F1F5F9",
    "card_fill": "#F1F5F9",
    "heading_font": "Inter",
    "body_font": "Inter",
}

ASH = {
    "name": "Ash",
    "desc": "Light ash — high contrast b&w, geometric, formal",
    "bg": "#FAFAFA",
    "title_bg": "#1A1A1A",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#757575",
    "accent": "#1A1A1A",
    "accent2": "#424242",
    "border": "#E0E0E0",
    "surface": "#F5F5F5",
    "card_fill": "#F5F5F5",
    "heading_font": "Inter",
    "body_font": "Inter",
}

ONYX = {
    "name": "Onyx",
    "desc": "Onyx — pure black and white, maximum contrast",
    "bg": "#000000",
    "title_bg": "#000000",
    "title_fg": "#FFFFFF",
    "text": "#FFFFFF",
    "muted": "#AAAAAA",
    "accent": "#FFFFFF",
    "accent2": "#FFFFFF",
    "border": "#333333",
    "surface": "#1A1A1A",
    "card_fill": "#1A1A1A",
    "heading_font": "Inter",
    "body_font": "Inter",
}

# ═══════════════════════════════════════════════════════════════════════
# BRAND-SPECIFIC (Aigis variants)
# ═══════════════════════════════════════════════════════════════════════

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

# ═══════════════════════════════════════════════════════════════════════
# CURATED PALETTES (from research — ready-to-use combos)
# ═══════════════════════════════════════════════════════════════════════

ENERGIZING_BLUE = {
    "name": "Energizing Blue",
    "desc": "Vibrant blue gradient — pitch meetings, sales",
    "bg": "#FFFFFF",
    "title_bg": "#03256C",
    "title_fg": "#FFFFFF",
    "text": "#03256C",
    "muted": "#6B7280",
    "accent": "#06BEE1",
    "accent2": "#1768AC",
    "border": "#D1D5DB",
    "surface": "#EFF8FF",
    "card_fill": "#EFF8FF",
    "heading_font": "Inter",
    "body_font": "Inter",
}

HIGH_END_NAVY = {
    "name": "High-End Navy",
    "desc": "Luxury navy — finance, wealth management, premium",
    "bg": "#FFFFFF",
    "title_bg": "#21295C",
    "title_fg": "#FFFFFF",
    "text": "#21295C",
    "muted": "#5A6688",
    "accent": "#1C7293",
    "accent2": "#065A82",
    "border": "#C8D6E5",
    "surface": "#EEF2F7",
    "card_fill": "#EEF2F7",
    "heading_font": "Inter",
    "body_font": "Inter",
}

CONFIDENT_RED = {
    "name": "Confident Red",
    "desc": "Bold red and purple — marketing, campaigns, impact",
    "bg": "#FFFFFF",
    "title_bg": "#3D2F68",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
    "accent": "#F8275B",
    "accent2": "#FF574A",
    "border": "#E5E7EB",
    "surface": "#FEF2F2",
    "card_fill": "#FEF2F2",
    "heading_font": "Inter",
    "body_font": "Inter",
}

CALMING_NATURE = {
    "name": "Calming Nature",
    "desc": "Soft greens — healthcare, wellness, environment",
    "bg": "#F5FAF5",
    "title_bg": "#2D4F4F",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
    "accent": "#50808E",
    "accent2": "#69A297",
    "border": "#C8D8D4",
    "surface": "#E8F0EC",
    "card_fill": "#E8F0EC",
    "heading_font": "Inter",
    "body_font": "Inter",
}

BLUE_ORANGE = {
    "name": "Blue & Orange",
    "desc": "Classic complementary — navy blue with orange pop",
    "bg": "#FFFFFF",
    "title_bg": "#224088",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
    "accent": "#224088",
    "accent2": "#F57325",
    "border": "#D1D5DB",
    "surface": "#E8E9E3",
    "card_fill": "#E8E9E3",
    "heading_font": "Inter",
    "body_font": "Inter",
}

TEAL_GOLD = {
    "name": "Teal & Gold",
    "desc": "Teal with gold accent — refined, distinctive",
    "bg": "#FFFFFF",
    "title_bg": "#0A4444",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
    "accent": "#188488",
    "accent2": "#D69500",
    "border": "#D1D5DB",
    "surface": "#F0F8F8",
    "card_fill": "#F0F8F8",
    "heading_font": "Inter",
    "body_font": "Inter",
}

VIOLET_GRADIENT = {
    "name": "Violet Gradient",
    "desc": "Purple gradient feel — creative, modern, SaaS",
    "bg": "#FFFFFF",
    "title_bg": "#5038A6",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
    "accent": "#5038A6",
    "accent2": "#7C3AED",
    "border": "#DDD8F7",
    "surface": "#F0EDFA",
    "card_fill": "#F0EDFA",
    "heading_font": "Inter",
    "body_font": "Inter",
}

MINT_ORANGE = {
    "name": "Mint & Orange",
    "desc": "Fresh mint with warm orange — energetic, modern",
    "bg": "#FFFFFF",
    "title_bg": "#111111",
    "title_fg": "#FFFFFF",
    "text": "#111111",
    "muted": "#6B7280",
    "accent": "#21E9C5",
    "accent2": "#FF8513",
    "border": "#E5E7EB",
    "surface": "#F5FFFE",
    "card_fill": "#F5FFFE",
    "heading_font": "Inter",
    "body_font": "Inter",
}

CREAM_GREEN = {
    "name": "Cream & Green",
    "desc": "Warm cream with forest green — elegant organic",
    "bg": "#FFF8ED",
    "title_bg": "#40695B",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
    "accent": "#40695B",
    "accent2": "#5C8A73",
    "border": "#E0D8C8",
    "surface": "#FFE1C7",
    "card_fill": "#F5EDE0",
    "heading_font": "Inter",
    "body_font": "Inter",
}

# ═══════════════════════════════════════════════════════════════════════
# INDUSTRY-SPECIFIC
# ═══════════════════════════════════════════════════════════════════════

HEALTHCARE = {
    "name": "Healthcare",
    "desc": "Medical blue-green — clean, trustworthy, clinical",
    "bg": "#FFFFFF",
    "title_bg": "#075985",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
    "accent": "#0891B2",
    "accent2": "#059669",
    "border": "#D1D5DB",
    "surface": "#F0F9FF",
    "card_fill": "#F0F9FF",
    "heading_font": "Inter",
    "body_font": "Inter",
}

ENERGY = {
    "name": "Energy",
    "desc": "Energy sector — orange and dark blue, industrial",
    "bg": "#FFFFFF",
    "title_bg": "#1A3050",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
    "accent": "#E97B14",
    "accent2": "#1A3050",
    "border": "#D1D5DB",
    "surface": "#FFF7ED",
    "card_fill": "#FFF7ED",
    "heading_font": "Inter",
    "body_font": "Inter",
}

REAL_ESTATE = {
    "name": "Real Estate",
    "desc": "Property — navy with warm gold, professional trust",
    "bg": "#FFFFFF",
    "title_bg": "#1B2838",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
    "accent": "#1B2838",
    "accent2": "#C8A45C",
    "border": "#D1D5DB",
    "surface": "#F8F6F0",
    "card_fill": "#F8F6F0",
    "heading_font": "Inter",
    "body_font": "Inter",
}

EDUCATION = {
    "name": "Education",
    "desc": "Academic — deep blue, accessible, scholarly",
    "bg": "#FFFFFF",
    "title_bg": "#1E3A5F",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
    "accent": "#2563EB",
    "accent2": "#DC2626",
    "border": "#D1D5DB",
    "surface": "#EFF6FF",
    "card_fill": "#EFF6FF",
    "heading_font": "Inter",
    "body_font": "Inter",
}

LEGAL = {
    "name": "Legal",
    "desc": "Legal / professional services — dark gray, conservative",
    "bg": "#FFFFFF",
    "title_bg": "#2D2D2D",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
    "accent": "#2D2D2D",
    "accent2": "#8B7355",
    "border": "#D1D5DB",
    "surface": "#F5F5F5",
    "card_fill": "#F5F5F5",
    "heading_font": "Inter",
    "body_font": "Inter",
}

DATA_SCIENCE = {
    "name": "Data Science",
    "desc": "Data viz palette — dark bg, multi-color chart support",
    "bg": "#FFFFFF",
    "title_bg": "#1B1B3A",
    "title_fg": "#FFFFFF",
    "text": "#1A1A1A",
    "muted": "#6B7280",
    "accent": "#4C78D8",
    "accent2": "#FF6B6B",
    "border": "#D1D5DB",
    "surface": "#F0F4FF",
    "card_fill": "#F0F4FF",
    "heading_font": "Inter",
    "body_font": "Inter",
    "chart_colors": ["#4C78D8", "#FF6B6B", "#4ECDC4", "#FFD93D", "#6C5CE7", "#A8E6CF"],
}


# ═══════════════════════════════════════════════════════════════════════
# ALL_THEMES — master registry
# ═══════════════════════════════════════════════════════════════════════

ALL_THEMES = {
    # Consulting & Professional Services
    "mckinsey": MCKINSEY,
    "bcg": BCG,
    "bain": BAIN,
    "deloitte": DELOITTE,
    "pwc": PWC,
    "ey": EY,
    "kpmg": KPMG,
    "consulting": CONSULTING,

    # Corporate & Finance
    "navy_gold": NAVY_GOLD,
    "investor": INVESTOR,
    "goldman": GOLDMAN,
    "jpmorgan": JPMORGAN,
    "private_equity": PRIVATE_EQUITY,
    "boardroom": BOARDROOM,

    # Tech & Startup
    "stripe": STRIPE,
    "stripe_dark": STRIPE_DARK,
    "linear": LINEAR,
    "vercel": VERCEL,
    "vercel_dark": VERCEL_DARK,
    "notion": NOTION,
    "airbnb": AIRBNB,
    "modern_startup": MODERN_STARTUP,
    "github": GITHUB,
    "github_dark": GITHUB_DARK,

    # Dark Mode
    "executive": EXECUTIVE,
    "midnight": MIDNIGHT,
    "carbon": CARBON,
    "obsidian": OBSIDIAN,
    "dark_executive": DARK_EXECUTIVE,
    "dark_teal": DARK_TEAL,
    "dark_orange": DARK_ORANGE,
    "nord_dark": NORD_DARK,
    "dracula": DRACULA,
    "catppuccin_mocha": CATPPUCCIN_MOCHA,

    # Warm & Earthy
    "terracotta": TERRACOTTA,
    "cream": CREAM,
    "mocha": MOCHA,
    "kraft": KRAFT,
    "oatmeal": OATMEAL,
    "dune": DUNE,
    "clementa": CLEMENTA,

    # Cool & Teal
    "arctic": ARCTIC,
    "breeze": BREEZE,
    "ocean": OCEAN,
    "marine": MARINE,
    "teal_corporate": TEAL_CORPORATE,
    "nord_light": NORD_LIGHT,

    # Nature & Green
    "sage": SAGE,
    "forest": FOREST,
    "moss": MOSS,
    "sprout": SPROUT,

    # Creative & Gradient
    "aurora": AURORA,
    "nebula": NEBULA,
    "electric": ELECTRIC,
    "neon": NEON,
    "coral": CORAL,
    "sunset": SUNSET,

    # Editorial & Newspaper
    "newspaper": NEWSPAPER,
    "editorial": EDITORIAL,
    "financial_times": FINANCIAL_TIMES,
    "economist": ECONOMIST,

    # Pastel & Soft
    "lavender": LAVENDER,
    "blush": BLUSH,
    "peach": PEACH,
    "seafoam": SEAFOAM,
    "daydream": DAYDREAM,
    "spectrum": SPECTRUM,

    # Gold & Luxury
    "aurum": AURUM,
    "gold_leaf": GOLD_LEAF,
    "wine": WINE,

    # Minimal & Monochrome
    "minimalism": MINIMALISM,
    "pearl": PEARL,
    "slate": SLATE,
    "ash": ASH,
    "onyx": ONYX,

    # Brand-specific
    "aigis": AIGIS,
    "aigis_dark": AIGIS_DARK,

    # Curated Palettes
    "energizing_blue": ENERGIZING_BLUE,
    "high_end_navy": HIGH_END_NAVY,
    "confident_red": CONFIDENT_RED,
    "calming_nature": CALMING_NATURE,
    "blue_orange": BLUE_ORANGE,
    "teal_gold": TEAL_GOLD,
    "violet_gradient": VIOLET_GRADIENT,
    "mint_orange": MINT_ORANGE,
    "cream_green": CREAM_GREEN,

    # Industry-Specific
    "healthcare": HEALTHCARE,
    "energy": ENERGY,
    "real_estate": REAL_ESTATE,
    "education": EDUCATION,
    "legal": LEGAL,
    "data_science": DATA_SCIENCE,
}

# Theme categories for discovery
THEME_CATEGORIES = {
    "consulting": ["mckinsey", "bcg", "bain", "deloitte", "pwc", "ey", "kpmg", "consulting"],
    "corporate": ["navy_gold", "investor", "goldman", "jpmorgan", "private_equity", "boardroom"],
    "tech": ["stripe", "stripe_dark", "linear", "vercel", "vercel_dark", "notion", "airbnb", "modern_startup", "github", "github_dark"],
    "dark": ["executive", "midnight", "carbon", "obsidian", "dark_executive", "dark_teal", "dark_orange", "nord_dark", "dracula", "catppuccin_mocha", "stripe_dark", "vercel_dark", "github_dark", "linear", "marine", "aurum", "wine", "onyx", "mocha", "forest", "aurora", "nebula", "electric", "neon"],
    "warm": ["terracotta", "cream", "mocha", "kraft", "oatmeal", "dune", "clementa", "cream_green"],
    "cool": ["arctic", "breeze", "ocean", "marine", "teal_corporate", "nord_light", "nord_dark", "seafoam"],
    "nature": ["sage", "forest", "moss", "sprout", "calming_nature"],
    "creative": ["aurora", "nebula", "electric", "neon", "coral", "sunset", "spectrum", "dracula", "catppuccin_mocha"],
    "editorial": ["newspaper", "editorial", "financial_times", "economist"],
    "pastel": ["lavender", "blush", "peach", "seafoam", "daydream", "spectrum"],
    "luxury": ["aurum", "gold_leaf", "wine", "high_end_navy"],
    "minimal": ["minimalism", "pearl", "slate", "ash", "onyx", "vercel", "vercel_dark"],
    "industry": ["healthcare", "energy", "real_estate", "education", "legal", "data_science"],
}


def get_theme(name: str) -> dict:
    """Get a theme by name. Raises KeyError if not found."""
    if name not in ALL_THEMES:
        raise KeyError(
            f"Unknown theme '{name}'. Available ({len(ALL_THEMES)}): "
            f"{', '.join(sorted(ALL_THEMES.keys()))}"
        )
    return ALL_THEMES[name]


def list_themes(category: str | None = None) -> list[str]:
    """List available theme names, optionally filtered by category."""
    if category:
        return THEME_CATEGORIES.get(category, [])
    return sorted(ALL_THEMES.keys())


def list_categories() -> list[str]:
    """List available theme categories."""
    return sorted(THEME_CATEGORIES.keys())


def search_themes(keyword: str) -> list[str]:
    """Search themes by keyword in name or description."""
    keyword_lower = keyword.lower()
    matches = []
    for name, theme in ALL_THEMES.items():
        if keyword_lower in name.lower() or keyword_lower in theme.get("desc", "").lower():
            matches.append(name)
    return sorted(matches)
