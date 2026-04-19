"""Typst document renderer — generates A4/Letter report markup.

Produces branded documents with:
- Cover page with logo + title block
- Auto-generated TOC with heading numbering
- Branded headers (logo + doc title) and footers (confidentiality + page numbers)
- Dark header tables with alternating row fills
- Callout boxes, RAG badges, source notes
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from inkline.typst.components import _rgb, _force_breakable


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class DocumentSpec:
    """Specification for a branded document."""
    title: str = ""
    subtitle: str = ""
    date: str = ""
    author: str = ""
    sections: list[dict[str, Any]] = field(default_factory=list)
    paper: str = "a4"  # "a4" or "us-letter"
    cover_panel: dict[str, str] | None = None  # key/value pairs for cover metrics (up to 6)
    toc_panel: dict[str, Any] | None = None  # keys: title, cards, how_to_read, confidentiality_notice
    section_dividers: bool = False  # insert full-bleed divider pages before level-1 sections (3+ required)


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

class TypstDocumentRenderer:
    """Renders DocumentSpec to Typst markup for A4/Letter reports."""

    def __init__(self, theme: dict):
        self.t = theme

    def render_document(self, spec: DocumentSpec) -> str:
        """Render a full document to Typst source."""
        parts = [
            self._preamble(spec),
            self._heading_styles(),
            self._component_defs(),
            self._cover_page(spec),
            self._toc_page(spec),
        ]

        # Count level-1 sections to determine if dividers are appropriate
        l1_sections = [s for s in spec.sections if s.get("level", 1) == 1]
        use_dividers = spec.section_dividers and len(l1_sections) >= 3

        l1_counter = 0
        for section in spec.sections:
            if use_dividers and section.get("level", 1) == 1:
                l1_counter += 1
                parts.append(
                    self._section_divider_page(l1_counter, section.get("heading", ""))
                )
            parts.append(self._render_section(section))

        return "\n\n".join(parts)

    def render_from_markdown(self, markdown: str, spec: DocumentSpec) -> str:
        """Render a document from Markdown content.

        Converts Markdown headings, lists, bold, italic, and tables to
        Typst markup, then wraps in branded document chrome.
        """
        parts = [
            self._preamble(spec),
            self._heading_styles(),
            self._component_defs(),
            self._cover_page(spec),
            self._toc_page(spec),
        ]

        # Count # headings to determine if dividers are appropriate
        l1_headings = [ln for ln in markdown.split("\n") if re.match(r"^# ", ln)]
        use_dividers = spec.section_dividers and len(l1_headings) >= 3

        if use_dividers:
            # Interleave section divider pages before each level-1 heading
            md_lines = markdown.split("\n")
            l1_counter = 0
            current_chunk: list[str] = []
            for line in md_lines:
                if re.match(r"^# ", line):
                    if current_chunk:
                        parts.append(self._markdown_to_typst("\n".join(current_chunk)))
                        current_chunk = []
                    l1_counter += 1
                    heading_text = line.lstrip("# ").strip()
                    parts.append(self._section_divider_page(l1_counter, heading_text))
                current_chunk.append(line)
            if current_chunk:
                parts.append(self._markdown_to_typst("\n".join(current_chunk)))
        else:
            parts.append(self._markdown_to_typst(markdown))

        return "\n\n".join(parts)

    # -- Preamble ----------------------------------------------------------

    def _preamble(self, spec: DocumentSpec) -> str:
        t = self.t
        heading_font = t.get("heading_font", "Inter")
        body_font = t.get("body_font", "Inter")
        body_size = t.get("body_size", 11)
        accent = t.get("accent", "#1a3a5c")
        muted = t.get("muted", "#6B7280")
        border = t.get("border", "#D1D5DB")
        conf = t.get("confidentiality", "")
        footer_text = t.get("footer_text", "")
        doc_title = _esc(spec.title)
        date = _esc(spec.date)
        logo_path = t.get("logo_light_path", "")

        if logo_path:
            header_right = f'align(right, image("{logo_path}", height: 0.7cm, fit: "contain"))'
        else:
            header_right = f'align(right, text(size: 8pt, fill: {_rgb(muted)})[{_esc(conf)}])'

        return f"""// Generated by Inkline - Typst Document Engine
#set page(
  paper: "{spec.paper}",
  fill: white,
  margin: (top: 3cm, bottom: 2.5cm, left: 2.5cm, right: 2.5cm),
  header: context {{
    let pg = counter(page).get().first()
    if pg > 2 {{
      // Suppress on cover (pg 0 has no header), TOC (pg 1), and first content page
      let headings = query(heading.where(level: 1).before(here()))
      let section-name = if headings.len() > 0 {{
        upper(headings.last().body)
      }} else {{
        ""
      }}
      let page-display = [
        #counter(page).display() of #context counter(page).final().first()
      ]
      grid(
        columns: (1fr, auto),
        align: (left + horizon, right + horizon),
        text(
          font: "{heading_font}",
          size: 8pt,
          fill: {_rgb(muted)},
          tracking: 0.05em,
        )[#section-name],
        text(
          font: "{heading_font}",
          size: 8pt,
          fill: {_rgb(muted)},
        )[#section-name #sym.dot.c Page #page-display],
      )
      v(4pt)
      line(length: 100%, stroke: 0.5pt + {_rgb(border)})
    }}
  }},
  footer: context {{
    line(length: 100%, stroke: 0.3pt + {_rgb(border)})
    v(4pt)
    grid(
      columns: (1fr, 1fr),
      text(size: 7pt, fill: {_rgb(muted)})[{_esc(footer_text)} - {date}],
      align(right, text(size: 8pt, fill: {_rgb(muted)})[Page #counter(page).display() of #context counter(page).final().first()]),
    )
  }},
)

#set text(font: "{body_font}", size: {body_size}pt, fill: {_rgb(t.get('text', '#1A1A1A'))})
#set par(leading: 1.5em, justify: true, spacing: 0.65em)
#set table(stroke: 0.5pt + {_rgb(border)}, inset: 6pt)

// OpenType figure variants — applied at style level
// Tabular figures in all table cells (fixed-width, columns align)
#show table.cell: set text(features: ("tnum": 1))

// Old-style figures in body paragraphs (proportional, typographically correct)
// Applied only to par content, not headings or table cells.
// Headings use lining figures (OpenType default) — no override needed.
#show par: set text(features: ("onum": 1))"""

    # -- Heading styles ----------------------------------------------------

    def _heading_styles(self) -> str:
        t = self.t
        accent = t.get("accent", "#1a3a5c")
        accent2 = t.get("accent2", "#39d3bb")
        heading_font = t.get("heading_font", "Inter")
        text_color = t.get("text", "#1A1A1A")

        return f"""// Heading styles
#set heading(numbering: none)

#show heading.where(level: 1): it => {{
  set par(leading: 1.15em)
  v(16pt)
  text(font: "{heading_font}", weight: "bold", size: 18pt, fill: {_rgb(accent)})[#it]
  v(4pt)
  line(length: 100%, stroke: 1pt + {_rgb(accent2)})
  v(8pt)
}}

#show heading.where(level: 2): it => {{
  set par(leading: 1.15em)
  v(12pt)
  text(font: "{heading_font}", weight: "bold", size: 14pt, fill: {_rgb(accent)})[#it]
  v(6pt)
}}

#show heading.where(level: 3): it => {{
  set par(leading: 1.15em)
  v(8pt)
  text(font: "{heading_font}", weight: "bold", size: 12pt, fill: {_rgb(text_color)})[#it]
  v(4pt)
}}"""

    # -- Component definitions ---------------------------------------------

    def _component_defs(self) -> str:
        t = self.t
        accent = t.get("accent", "#1a3a5c")
        accent2 = t.get("accent2", "#39d3bb")
        muted = t.get("muted", "#6B7280")
        bg = t.get("bg", "#FFFFFF")
        light_bg = t.get("surface", "#F4F6F8")
        border = t.get("border", "#D1D5DB")

        slate = t.get("slate", "#64748B")
        return f"""// Reusable components

// Uppercase label with standard tracking
#let label-text(content, size: 8pt, color: rgb("#6B7280")) = {{
  text(size: size, tracking: 0.08em, fill: color)[#upper(content)]
}}

// Exhibit counters and wrappers
#let figure-counter = counter("figures")
#let table-counter = counter("tables")

// Figure: caption BELOW, incrementing Figure counter
#let fig(image-content, caption: none, source: none) = {{
  figure-counter.step()
  block(width: 100%)[
    #image-content
    #v(4pt)
    #text(size: 9pt, weight: "bold")[Figure #figure-counter.display()]
    #if caption != none [ --- #text(size: 9pt)[#caption]]
    #if source != none [
      #v(2pt)
      #text(size: 8pt, fill: {_rgb(slate)}, style: "italic")[Source: #source]
    ]
  ]
}}

// Table: caption ABOVE, incrementing Table counter
#let tbl(table-content, caption: none, source: none) = {{
  table-counter.step()
  block(width: 100%)[
    #text(size: 9pt, weight: "bold")[Table #table-counter.display()]
    #if caption != none [ --- #text(size: 9pt)[#caption]]
    #v(4pt)
    #table-content
    #if source != none [
      #v(2pt)
      #text(size: 8pt, fill: {_rgb(slate)}, style: "italic")[Source: #source]
    ]
  ]
}}

#let rag-badge(status) = {{
  let color = if status == "RED" {{ rgb("#dc2626") }} else if status == "AMBER" {{ rgb("#f59e0b") }} else if status == "GREEN" {{ rgb("#10b981") }} else {{ rgb("#6b7280") }}
  box(fill: color, radius: 2pt, inset: (x: 6pt, y: 2pt), text(size: 8pt, weight: "bold", tracking: 0.08em, fill: white)[#upper(status)])
}}

#let callout(title, body, color: {_rgb(accent)}) = {{
  block(
    width: 100%,
    inset: (left: 14pt, rest: 10pt),
    stroke: (left: 3pt + color),
    fill: {_rgb(light_bg)},
    radius: (right: 4pt),
  )[
    #text(weight: "bold", fill: color)[#title]
    #v(4pt)
    #body
  ]
}}

#let source-note(content) = {{
  text(size: 8pt, style: "italic", fill: {_rgb(muted)})[Source: #content]
}}

#let metric-box(value, label) = {{
  align(center)[
    #text(weight: "bold", size: 24pt, fill: {_rgb(accent)})[#value]
    #v(2pt)
    #text(size: 9pt, tracking: 0.08em, fill: {_rgb(muted)})[#upper(label)]
  ]
}}"""

    # -- Cover page --------------------------------------------------------

    def _cover_page(self, spec: DocumentSpec) -> str:
        t = self.t
        accent = t.get("accent", "#1a3a5c")
        accent2 = t.get("accent2", "#39d3bb")
        muted = t.get("muted", "#6B7280")
        heading_font = t.get("heading_font", "Inter")
        conf = t.get("confidentiality", "")

        logo_path = t.get("logo_light_path", "")

        # Build document metadata table rows
        info_rows = []
        if spec.date:
            info_rows.append(f'  table.cell(fill: {_rgb(accent)})[#text(fill: white, weight: "bold", size: 9pt)[Date]], [{_esc(spec.date)}],')
        if spec.author:
            info_rows.append(f'  table.cell(fill: {_rgb(accent)})[#text(fill: white, weight: "bold", size: 9pt)[Prepared by]], [{_esc(spec.author)}],')
        if conf:
            info_rows.append(f'  table.cell(fill: {_rgb(accent)})[#text(fill: white, weight: "bold", size: 9pt)[Classification]], [{_esc(conf)}],')
        info_rows.append(f'  table.cell(fill: {_rgb(accent)})[#text(fill: white, weight: "bold", size: 9pt)[Status]], [Strictly Private — Not for Distribution],')
        light_bg = t.get("light_bg", "#f0f4f8")
        rows_str = "\n".join(info_rows)
        border = t.get("border", "#D1D5DB")
        info_table = f"""#align(left)[
  #set text(size: 10pt)
  #table(
    columns: (4.5cm, 1fr),
    stroke: 0.5pt + {_rgb(border)},
    fill: (_, y) => if calc.odd(y) {{ white }} else {{ {_rgb(light_bg)} }},
    inset: (x: 10pt, y: 7pt),
{rows_str}
  )
]"""

        if logo_path:
            cover_top = f'#align(center)[#image("{logo_path}", width: 3.2cm, fit: "contain")]'
        else:
            cover_top = (
                f'#align(left)[#text(font: "{heading_font}", weight: "bold", size: 13pt, '
                f'tracking: 2pt, fill: {_rgb(accent)})[#upper("{_esc(spec.author)}")]]'
            )

        secondary = t.get("secondary", "#B8960C")

        # Build cover panel block — parameterised or empty spacer
        if spec.cover_panel:
            panel_cells = "\n    ".join(
                f"""[
      #text(fill: {_rgb(secondary)}, weight: "bold", size: 22pt)[{_esc(v)}]
      #v(3pt)
      #text(fill: rgb("#c0d0c0"), size: 8pt, tracking: 0.08em)[{_esc(k)}]
    ]"""
                for k, v in list(spec.cover_panel.items())[:6]
            )
            n_cols = min(len(spec.cover_panel), 4)
            col_spec = "(1fr, " * n_cols + ")"
            cover_panel_block = f"""#block(
  width: 100%,
  inset: (x: 22pt, y: 18pt),
  fill: {_rgb(accent)},
  radius: 4pt,
)[
  #text(fill: white, weight: "bold", size: 7.5pt, tracking: 2pt)[HIGHLIGHTS]
  #v(14pt)
  #grid(
    columns: {col_spec},
    gutter: 6pt,
    {panel_cells}
  )
]

#v(1.2cm)"""
        else:
            cover_panel_block = "#v(1.2cm)"

        return f"""// Cover page — top-logo / title / highlights panel / bottom-metadata
#set page(header: none, footer: none, margin: (top: 2.5cm, bottom: 2.0cm, left: 2.5cm, right: 2.5cm))

#v(0.2cm)
{cover_top}
#v(0.4cm)
#line(length: 100%, stroke: 1pt + {_rgb(accent)})
#v(1.4cm)

#align(left)[
  #text(font: "{heading_font}", weight: "bold", size: 32pt, fill: {_rgb(accent)})[
    #upper("{_esc(spec.title)}")
  ]
  #v(0.6cm)
  #text(size: 16pt, fill: {_rgb(muted)})[{_esc(spec.subtitle)}]
]

#v(1.2cm)

{cover_panel_block}

#v(1fr)

{info_table}

#v(0.6cm)
#line(length: 100%, stroke: 0.5pt + {_rgb(t.get("border", "#cccccc"))})
#v(0.2cm)
#align(center, text(size: 9pt, fill: {_rgb(muted)})[{_esc(conf)}])

#pagebreak()"""

    # -- TOC ---------------------------------------------------------------

    def _toc_page(self, spec: DocumentSpec | None = None) -> str:
        t = self.t
        accent = t.get("accent", "#1a3a5c")
        heading_font = t.get("heading_font", "Inter")
        muted = t.get("muted", "#6B7280")
        border = t.get("border", "#D1D5DB")
        conf = t.get("confidentiality", "")

        toc_panel = spec.toc_panel if spec is not None else None
        light_bg2 = t.get("light_bg", "#f0f4f8")
        secondary = t.get("secondary", "#B8960C")

        toc_base = f"""// Table of Contents
#set page(header: auto, footer: auto)
#counter(page).update(1)

#text(font: "{heading_font}", weight: "bold", size: 18pt, fill: {_rgb(accent)})[Table of Contents]
#v(16pt)
#[
  #set text(size: 11.5pt)
  #outline(title: none, indent: 1.5em, depth: 2)
]

#v(22pt)"""

        if toc_panel:
            # Parameterised TOC panel
            panel_title = _esc(toc_panel.get("title", ""))
            cards = toc_panel.get("cards", [])
            how_to_read = toc_panel.get("how_to_read")
            conf_notice = toc_panel.get("confidentiality_notice")

            n_cols = max(1, len(cards))
            col_spec = ", ".join(["1fr"] * n_cols)
            card_blocks = "\n    ".join(
                f"""block(
      stroke: (left: 3pt + {_rgb(accent)}),
      inset: (left: 12pt, rest: 10pt),
      fill: {_rgb(light_bg2)},
      radius: (right: 4pt),
      width: 100%,
    )[
      #text(weight: "bold", size: 9pt, fill: {_rgb(accent)})[{_esc(card.get("heading", ""))}]
      #v(4pt)
      #text(size: 8pt, fill: {_rgb(muted)})[{_esc(card.get("body", ""))}]
    ]"""
                for card in cards
            )

            panel_block = f"""#block(
  width: 100%,
  inset: (x: 0pt, y: 0pt),
)[
  #text(weight: "bold", size: 7.5pt, tracking: 2pt, fill: {_rgb(muted)})[{panel_title}]
  #v(10pt)
  #grid(
    columns: ({col_spec}),
    gutter: 10pt,
    {card_blocks}
  )
]"""

            how_block = ""
            if how_to_read:
                how_block = f"""
#v(18pt)
#block(
  width: 100%,
  inset: (left: 14pt, rest: 12pt),
  stroke: (left: 3pt + {_rgb(accent)}),
  fill: {_rgb(light_bg2)},
  radius: (right: 4pt),
)[
  #text(weight: "bold", size: 9pt, fill: {_rgb(accent)})[HOW TO READ THIS DOCUMENT]
  #v(6pt)
  #text(size: 9.5pt)[{_esc(how_to_read)}]
]"""

            conf_text = conf_notice if conf_notice else conf
            conf_block = f"""#v(1fr)

#block(
  width: 100%,
  inset: (x: 16pt, y: 12pt),
  fill: {_rgb(accent)},
  radius: 4pt,
)[
  #text(weight: "bold", size: 9pt, fill: white)[CONFIDENTIALITY NOTICE]
  #v(5pt)
  #text(size: 8.5pt, fill: rgb("#d8e0d8"))[{_esc(conf_text)}]
]"""

            return f"""{toc_base}

{panel_block}{how_block}

{conf_block}

#pagebreak()"""

        else:
            # Minimal TOC page — just outline + confidentiality notice from theme
            conf_block = ""
            if conf:
                conf_block = f"""
#v(1fr)

#block(
  width: 100%,
  inset: (x: 16pt, y: 12pt),
  fill: {_rgb(accent)},
  radius: 4pt,
)[
  #text(weight: "bold", size: 9pt, fill: white)[CONFIDENTIALITY NOTICE]
  #v(5pt)
  #text(size: 8.5pt, fill: rgb("#d8e0d8"))[{_esc(conf)}]
]"""

            return f"""{toc_base}
{conf_block}

#pagebreak()"""

    # -- Section divider page ----------------------------------------------

    def _section_divider_page(self, section_number: int, heading: str) -> str:
        """Render a full-bleed accent-coloured section divider page."""
        t = self.t
        accent = t.get("accent", "#1a3a5c")
        heading_font = t.get("heading_font", "Inter")
        return f"""// Section divider — {heading}
#page(
  fill: {_rgb(accent)},
  margin: (top: 0pt, bottom: 0pt, left: 0pt, right: 0pt),
  header: none,
  footer: none,
)[
  #align(center + horizon)[
    #v(1fr)
    #text(
      font: "{heading_font}",
      size: 11pt,
      weight: "bold",
      fill: white,
      tracking: 0.15em,
    )[#upper("Section {section_number}")]
    #v(0.6cm)
    #text(
      font: "{heading_font}",
      size: 36pt,
      weight: "bold",
      fill: white,
    )[{_esc(heading)}]
    #v(1fr)
  ]
]"""

    # -- Section rendering -------------------------------------------------

    def _render_section(self, section: dict) -> str:
        """Render a document section.

        Section dict keys:
        - heading: str — section heading text
        - level: int — heading level (1, 2, 3)
        - content: str — body text (Typst markup)
        - exhibits: list[dict] — optional exhibits; each dict has:
            type: "figure" | "table"
            content: str — Typst content expression
            caption: str (optional)
            source: str (optional)
        - pagebreak: bool — add pagebreak after section
        """
        level = section.get("level", 1)
        heading = section.get("heading", "")
        content = section.get("content", "")
        exhibits = section.get("exhibits", [])
        pb = section.get("pagebreak", False)

        heading_prefix = "=" * level
        parts = [f"{heading_prefix} {heading}"]
        if content:
            parts.append(content)

        for exhibit in exhibits:
            ex_type = exhibit.get("type", "figure")
            ex_content = exhibit.get("content", "")
            caption = exhibit.get("caption")
            source = exhibit.get("source")

            caption_arg = f', caption: "{_esc(caption)}"' if caption else ""
            source_arg = f', source: "{_esc(source)}"' if source else ""

            if ex_type == "table":
                parts.append(f"#tbl({ex_content}{caption_arg}{source_arg})")
            else:
                parts.append(f"#fig({ex_content}{caption_arg}{source_arg})")

        if pb:
            parts.append("#pagebreak()")

        return "\n\n".join(parts)

    # -- Markdown to Typst conversion (basic) ------------------------------

    def _markdown_to_typst(self, md: str) -> str:
        """Convert basic Markdown to Typst markup.

        Handles: headings, bold, italic, bullet lists, numbered lists,
        horizontal rules, and basic tables.
        """
        lines = md.split("\n")
        output = []
        in_table = False
        table_rows: list[list[str]] = []
        in_code = False
        code_buffer: list[str] = []
        code_lang = ""

        for line in lines:
            stripped = line.strip()

            # Fenced code blocks (```lang ... ```)
            if stripped.startswith("```"):
                if in_code:
                    # Closing fence — emit raw block.
                    # Pass raw() as a positional arg to block() to avoid
                    # Typst's content-mode [...] parsing the string contents
                    # (which would treat @, # etc. as syntax inside the body).
                    code_text = "\n".join(code_buffer)
                    escaped = (
                        code_text
                        .replace("\\", "\\\\")
                        .replace("\"", "\\\"")
                        .replace("\n", "\\n")
                    )
                    if code_lang:
                        raw_call = f'raw(lang: "{code_lang}", block: true, "{escaped}")'
                    else:
                        raw_call = f'raw(block: true, "{escaped}")'
                    output.append(
                        f'#block(fill: rgb("#F5F5F5"), inset: 8pt, radius: 3pt, '
                        f'width: 100%, {raw_call})'
                    )
                    code_buffer = []
                    code_lang = ""
                    in_code = False
                else:
                    # Opening fence
                    code_lang = stripped[3:].strip()
                    in_code = True
                continue

            if in_code:
                code_buffer.append(line)
                continue

            # Flush table if we leave table context
            if in_table and not stripped.startswith("|"):
                output.append(self._flush_table(table_rows))
                table_rows = []
                in_table = False

            # Headings — any number of # followed by space
            heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if heading_match:
                level = len(heading_match.group(1))
                text = self._inline_format(heading_match.group(2))
                output.append(f'{"=" * level} {text}')
                continue

            # Horizontal rule
            if stripped in ("---", "***", "___"):
                output.append("#line(length: 100%)")
                continue

            # Table rows
            if stripped.startswith("|"):
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                if all(set(c) <= set("-: ") for c in cells):
                    continue  # Skip separator row
                table_rows.append(cells)
                in_table = True
                continue

            # Bullet lists
            if stripped.startswith("- ") or stripped.startswith("* "):
                text = stripped[2:]
                text = self._inline_format(text)
                output.append(f"- {text}")
                continue

            # Numbered lists
            match = re.match(r"^(\d+)\.\s+(.*)", stripped)
            if match:
                text = self._inline_format(match.group(2))
                output.append(f"+ {text}")
                continue

            # Regular paragraph
            output.append(self._inline_format(stripped))

        # Flush remaining table
        if in_table:
            output.append(self._flush_table(table_rows))

        return "\n".join(output)

    def _inline_format(self, text: str) -> str:
        """Convert inline Markdown formatting to Typst."""
        # First escape Typst-special characters that aren't markdown syntax:
        #   $ → math mode
        #   @ → label reference
        #   < → label declaration (e.g. <2 seconds is parsed as unclosed label)
        #   > → end of label / heading marker in some contexts
        # Done BEFORE markdown processing so they survive to output.
        text = text.replace("$", "\\$")
        text = text.replace("@", "\\@")
        text = text.replace("<", "\\<")
        text = text.replace(">", "\\>")
        # Don't escape # here because we want #raw() etc. to work in headers
        # Bold — replace with placeholder first to prevent italic regex grabbing *text*
        _BOLD_OPEN = "\x00BO\x00"
        _BOLD_CLOSE = "\x00BC\x00"
        text = re.sub(r"\*\*(.+?)\*\*", lambda m: f"{_BOLD_OPEN}{m.group(1)}{_BOLD_CLOSE}", text)
        text = re.sub(r"__(.+?)__", lambda m: f"{_BOLD_OPEN}{m.group(1)}{_BOLD_CLOSE}", text)
        # Italic (single * or _ — now safe since ** has been replaced with placeholders)
        text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"_\1_", text)
        text = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"_\1_", text)
        # Restore bold placeholders as Typst strong (*text*)
        text = text.replace(_BOLD_OPEN, "*").replace(_BOLD_CLOSE, "*")
        # Inline code
        text = re.sub(r"`(.+?)`", r'#raw("\1")', text)
        return text

    def _flush_table(self, rows: list[list[str]]) -> str:
        """Convert accumulated table rows to a Typst table."""
        if not rows:
            return ""
        t = self.t
        n_cols = max(len(r) for r in rows)
        accent = t.get("accent", "#1a3a5c")
        border = t.get("border", "#D1D5DB")
        bg = t.get("surface", "#F4F6F8")

        def _safe_header(cell: str) -> str:
            formatted = self._inline_format(cell)
            if not formatted or not formatted.strip():
                formatted = " "
            return f'table.cell(fill: {_rgb(accent)})[#text(fill: white, weight: "bold", size: 9pt)[{formatted}]]'

        header_cells = ",\n    ".join(_safe_header(cell) for cell in rows[0])

        data_cells = []
        for row in rows[1:]:
            for cell in row:
                formatted = self._inline_format(_force_breakable(cell))
                if not formatted or not formatted.strip():
                    formatted = " "
                data_cells.append(f"[{formatted}]")
        data_str = ", ".join(data_cells)

        # Calculate content-proportional column widths based on average cell length
        col_lens = [0.0] * n_cols
        for row in rows:
            for j, cell in enumerate(row):
                if j < n_cols:
                    col_lens[j] += len(cell)
        total = sum(col_lens) or 1
        # Normalise to fr units with a floor of 0.6fr so narrow columns don't vanish
        col_frs = [max(0.6, round(n_cols * (l / total), 2)) for l in col_lens]
        widths = ", ".join(f"{fr}fr" for fr in col_frs)

        return f"""#block(width: 100%)[
  #set par(justify: false)
  #table(
    columns: ({widths}),
    inset: 6pt,
    stroke: 0.5pt + {_rgb(border)},
    fill: (_, y) => if y == 0 {{ {_rgb(accent)} }} else if calc.odd(y) {{ white }} else {{ {_rgb(bg)} }},
    {header_cells},
    {data_str},
  )
]"""


def _esc(text: str) -> str:
    """Escape special Typst characters."""
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
