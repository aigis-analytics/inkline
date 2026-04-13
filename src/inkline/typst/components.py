"""Reusable Typst markup components.

Each function returns a Typst markup string that can be embedded in
slide or document templates. All colors are passed as hex strings and
converted to Typst ``rgb()`` calls.
"""

from __future__ import annotations


def _rgb(hex_color: str) -> str:
    """Convert '#RRGGBB' to Typst rgb() call."""
    return f'rgb("{hex_color}")'


def _esc_content(text: str) -> str:
    """Escape special Typst characters in content (inside [...] brackets)."""
    if not text:
        return ""
    return (
        text
        .replace("\\", "\\\\")
        .replace("#", "\\#")
        .replace("$", "\\$")
        .replace("@", "\\@")
        .replace("<", "\\<")
        .replace(">", "\\>")
    )


# ---------------------------------------------------------------------------
# Slide components
# ---------------------------------------------------------------------------

def section_badge(label: str, muted: str) -> str:
    """Upper-case section label in a bordered pill."""
    return f"""box(
    stroke: 0.75pt + {_rgb(muted)},
    radius: 2pt,
    inset: (x: 8pt, y: 3pt),
    text(size: 9pt, fill: {_rgb(muted)})[#upper("{_esc_content(label)}")]
  )"""


def slide_title(title: str, text_color: str) -> str:
    """Bold slide title — sentence case, 22pt to fit 2 lines on dense layouts."""
    return f'text(weight: "bold", size: 22pt, fill: {_rgb(text_color)})[{_esc_content(title)}]'


def card(
    body: str,
    *,
    fill: str,
    border: str | None = None,
    text_color: str = "#111111",
    radius: int = 3,
) -> str:
    """Content card with optional border.

"""
    stroke = f"stroke: 0.75pt + {_rgb(border)}," if border else ""
    return f"""block(
      fill: {_rgb(fill)},
      {stroke}
      radius: {radius}pt,
      inset: 14pt,
      width: 100%,
    )[
      {body}
    ]"""


def card_title(title: str, text_color: str) -> str:
    """Bold upper-case card heading."""
    return f'#text(weight: "bold", size: 13pt, fill: {_rgb(text_color)})[#upper("{_esc_content(title)}")]'


def hero_stat(value: str, label: str, desc: str, text_color: str, muted: str, accent: str | None = None) -> str:
    """Big number stat display (centered)."""
    value_color = _rgb(accent) if accent else _rgb(text_color)
    return f"""align(center)[
      #text(weight: "bold", size: 40pt, fill: {value_color})[{_esc_content(value)}]
      #v(6pt)
      #text(weight: "bold", size: 12pt, fill: {_rgb(muted)})[#upper("{_esc_content(label)}")]
      #v(4pt)
      #text(size: 10pt, fill: {_rgb(muted)})[{_esc_content(desc)}]
    ]"""


def footer_bar(content: str, border_color: str, muted: str) -> str:
    """Bottom bar with divider line."""
    return f"""v(1fr)
  line(length: 100%, stroke: 0.5pt + {_rgb(border_color)})
  v(4pt)
  text(size: 7pt, fill: {_rgb(muted)})[{_esc_content(content)}]"""


def accent_bar(color: str, position: str = "top") -> str:
    """Thin accent bar at top or bottom of slide."""
    return f'place({position} + left, block(fill: {_rgb(color)}, width: 100%, height: 4pt))'


# ---------------------------------------------------------------------------
# Document components
# ---------------------------------------------------------------------------

def callout(title: str, body: str, color: str, bg: str) -> str:
    """Left-bordered alert/callout box."""
    return f"""block(
    width: 100%,
    inset: (left: 14pt, rest: 10pt),
    stroke: (left: 3pt + {_rgb(color)}),
    fill: {_rgb(bg)},
    radius: (right: 4pt),
  )[
    #text(weight: "bold", fill: {_rgb(color)})[{title}]
    #v(4pt)
    {body}
  ]"""


def rag_badge(status: str) -> str:
    """RED / AMBER / GREEN inline badge."""
    colors = {
        "RED": "#dc2626",
        "AMBER": "#f59e0b",
        "GREEN": "#10b981",
    }
    color = colors.get(status.upper(), "#6b7280")
    return f"""box(
    fill: {_rgb(color)},
    radius: 2pt,
    inset: (x: 6pt, y: 2pt),
    text(size: 8pt, weight: "bold", fill: white)[{status.upper()}]
  )"""


def source_note(content: str, muted: str) -> str:
    """Grey italic source attribution."""
    return f'text(size: 8pt, style: "italic", fill: {_rgb(muted)})[Source: {content}]'


# ---------------------------------------------------------------------------
# Chart components (native Typst)
# ---------------------------------------------------------------------------

def bar_row(label: str, value: str, pct: float, color: str, muted: str) -> str:
    """Single horizontal bar row for bar charts."""
    return f"""grid(
    columns: (3.5cm, 1fr, 2cm),
    gutter: 6pt,
    align(right, text(size: 10pt, fill: {_rgb(muted)})[{label}]),
    block(
      width: {pct} * 1%,
      height: 18pt,
      fill: {_rgb(color)},
      radius: 2pt,
    ),
    text(size: 10pt, weight: "bold")[{value}],
  )"""


def kpi_card(value: str, label: str, fill: str, text_color: str) -> str:
    """KPI metric card for stat strips."""
    return f"""block(
    fill: {_rgb(fill)},
    radius: 4pt,
    inset: 10pt,
    width: 100%,
  )[
    #align(center)[
      #text(weight: "bold", size: 22pt, fill: {_rgb(text_color)})[{_esc_content(value)}]
      #v(4pt)
      #text(size: 8pt, fill: {_rgb(text_color)})[#upper("{_esc_content(label)}")]
    ]
  ]"""


def data_table(
    headers: list[str],
    rows: list[list[str]],
    *,
    header_fill: str,
    header_text: str = "#FFFFFF",
    bg: str = "#FFFFFF",
    alt_bg: str = "#F5F5F5",
    border: str = "#DDDDDD",
    col_widths: str | None = None,
) -> str:
    """Branded data table with auto-shrink font based on row count.

    Standard practice: as more rows are added, font size is reduced so
    everything fits on one slide. Same for cell padding.
    """
    n_cols = len(headers)
    n_rows = len(rows)
    widths = col_widths or ", ".join(["1fr"] * n_cols)

    # Auto-shrink: more rows → smaller font + tighter padding
    if n_rows <= 6:
        body_size, header_size, inset = 11, 10, 7
    elif n_rows <= 9:
        body_size, header_size, inset = 10, 9, 6
    elif n_rows <= 12:
        body_size, header_size, inset = 9, 8, 5
    else:
        body_size, header_size, inset = 8, 8, 4

    # Auto-shrink: many columns → narrower cells need smaller font
    if n_cols >= 8:
        body_size = min(body_size, 8)
        header_size = min(header_size, 8)
        inset = min(inset, 5)
    elif n_cols >= 6:
        body_size = min(body_size, 9)
        header_size = min(header_size, 9)
        inset = min(inset, 6)

    # Build header cells (comma-separated, with Typst escaping)
    header_cells = ",\n    ".join(
        f'table.cell(fill: {_rgb(header_fill)})[#text(fill: {_rgb(header_text)}, weight: "bold", size: {header_size}pt)[{_esc_content(h)}]]'
        for h in headers
    )

    # Build data cells (with auto-shrunk text size)
    data_cells = []
    for row in rows:
        for cell in row:
            data_cells.append(f'[#text(size: {body_size}pt)[{_esc_content(cell)}]]')
    data_str = ", ".join(data_cells)

    return f"""table(
    columns: ({widths}),
    inset: {inset}pt,
    stroke: 0.5pt + {_rgb(border)},
    fill: (_, y) => if y == 0 {{ {_rgb(header_fill)} }} else if calc.odd(y) {{ {_rgb(bg)} }} else {{ {_rgb(alt_bg)} }},
    align: (x, _) => if x == 0 {{ left }} else {{ right }},
    {header_cells},
    {data_str},
  )"""
