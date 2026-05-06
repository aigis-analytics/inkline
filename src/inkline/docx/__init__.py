"""Inkline DOCX exporter — Markdown to branded Word documents.

This backend targets editable, structurally faithful Word output rather than
pixel-identical reproduction of Typst/PDF layouts.
"""

from __future__ import annotations

import re
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

from docx import Document
from docx.document import Document as DocumentType
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from inkline.brands import BaseBrand, get_brand


def _set_cell_text(cell, text: str) -> None:
    cell.text = ""
    paragraph = cell.paragraphs[0]
    run = paragraph.add_run(text)
    run.font.name = "Aptos"
    run.font.size = Pt(10.5)


def _set_run_code(run) -> None:
    run.font.name = "Consolas"
    run.font.size = Pt(10)


def _shade_paragraph(paragraph, fill: str = "F3F4F6") -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    p_pr.append(shd)


class _DocxHTMLRenderer(HTMLParser):
    """Translate a constrained HTML subset into a python-docx document."""

    def __init__(self, document: DocumentType):
        super().__init__(convert_charrefs=True)
        self.document = document
        self.current_paragraph = None
        self.list_stack: list[str] = []
        self.blockquote_depth = 0
        self.inline_bold = 0
        self.inline_italic = 0
        self.inline_code = 0
        self.in_pre = False
        self.pre_chunks: list[str] = []
        self.in_table = False
        self.table_rows: list[list[str]] = []
        self.current_row: list[str] | None = None
        self.current_cell: list[str] | None = None
        self.current_link_href: str | None = None

    def _new_paragraph(self, style: str = "Normal"):
        paragraph = self.document.add_paragraph(style=style)
        if self.blockquote_depth and style == "Normal":
            paragraph.style = "Quote"
        if self.list_stack:
            paragraph.paragraph_format.left_indent = Inches(0.25 * max(0, len(self.list_stack) - 1))
        self.current_paragraph = paragraph
        return paragraph

    def _write_text(self, text: str) -> None:
        if not text:
            return
        if self.current_cell is not None:
            self.current_cell.append(text)
            return
        if self.in_pre:
            self.pre_chunks.append(text)
            return
        if self.current_paragraph is None:
            self._new_paragraph()
        if not self.inline_code:
            text = re.sub(r"\s+", " ", text)
        if not text:
            return
        run = self.current_paragraph.add_run(text)
        run.bold = self.inline_bold > 0
        run.italic = self.inline_italic > 0
        if self.inline_code:
            _set_run_code(run)

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "p":
            self._new_paragraph()
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            level = min(int(tag[1]), 4)
            style = "Title" if level == 1 else f"Heading {min(level - 1, 3)}"
            self._new_paragraph(style=style)
        elif tag in {"ul", "ol"}:
            self.list_stack.append(tag)
        elif tag == "li":
            style = "List Number" if self.list_stack and self.list_stack[-1] == "ol" else "List Bullet"
            self._new_paragraph(style=style)
        elif tag in {"strong", "b"}:
            self.inline_bold += 1
        elif tag in {"em", "i"}:
            self.inline_italic += 1
        elif tag == "code" and not self.in_pre:
            self.inline_code += 1
        elif tag == "pre":
            self.in_pre = True
            self.pre_chunks = []
        elif tag == "blockquote":
            self.blockquote_depth += 1
        elif tag == "br":
            if self.current_paragraph is None:
                self._new_paragraph()
            self.current_paragraph.add_run().add_break()
        elif tag == "hr":
            paragraph = self.document.add_paragraph()
            paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
            paragraph.add_run("----------")
            self.current_paragraph = None
        elif tag == "table":
            self.in_table = True
            self.table_rows = []
        elif tag == "tr":
            self.current_row = []
        elif tag in {"td", "th"}:
            self.current_cell = []
        elif tag == "a":
            self.current_link_href = attrs_dict.get("href")

    def handle_endtag(self, tag):
        if tag in {"p", "li", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.current_paragraph = None
        elif tag in {"ul", "ol"}:
            if self.list_stack:
                self.list_stack.pop()
        elif tag in {"strong", "b"}:
            self.inline_bold = max(0, self.inline_bold - 1)
        elif tag in {"em", "i"}:
            self.inline_italic = max(0, self.inline_italic - 1)
        elif tag == "code" and not self.in_pre:
            self.inline_code = max(0, self.inline_code - 1)
        elif tag == "pre":
            paragraph = self.document.add_paragraph(style="No Spacing" if "No Spacing" in self.document.styles else "Normal")
            run = paragraph.add_run("".join(self.pre_chunks).strip("\n"))
            _set_run_code(run)
            _shade_paragraph(paragraph)
            self.in_pre = False
            self.pre_chunks = []
            self.current_paragraph = None
        elif tag == "blockquote":
            self.blockquote_depth = max(0, self.blockquote_depth - 1)
        elif tag in {"td", "th"}:
            if self.current_row is not None and self.current_cell is not None:
                self.current_row.append("".join(self.current_cell).strip())
            self.current_cell = None
        elif tag == "tr":
            if self.current_row is not None:
                self.table_rows.append(self.current_row)
            self.current_row = None
        elif tag == "table":
            rows = [row for row in self.table_rows if row]
            if rows:
                cols = max(len(row) for row in rows)
                table = self.document.add_table(rows=len(rows), cols=cols)
                table.style = "Table Grid"
                for r_idx, row in enumerate(rows):
                    for c_idx in range(cols):
                        _set_cell_text(table.cell(r_idx, c_idx), row[c_idx] if c_idx < len(row) else "")
            self.in_table = False
            self.table_rows = []
            self.current_paragraph = None
        elif tag == "a":
            if self.current_link_href and self.current_paragraph is not None:
                self.current_paragraph.add_run(f" ({self.current_link_href})")
            self.current_link_href = None

    def handle_data(self, data):
        self._write_text(data)


def _extract_title(markdown: str) -> str:
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""


def _markdown_to_html(markdown: str) -> str:
    import markdown as _markdown

    return _markdown.markdown(
        markdown,
        extensions=[
            "tables",
            "fenced_code",
            "sane_lists",
            "nl2br",
        ],
        output_format="html5",
    )


def export_docx(
    markdown: str,
    output_path: str | Path,
    *,
    brand: str | BaseBrand = "minimal",
    title: str = "",
    confidentiality: str | None = None,
    date: Optional[datetime] = None,
) -> Path:
    """Convert Markdown to a branded DOCX document."""
    brand_obj = get_brand(brand)
    if date is None:
        date = datetime.now()
    if confidentiality is None:
        confidentiality = brand_obj.confidentiality
    if not title:
        title = _extract_title(markdown)

    document = Document()
    section = document.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.85)
    section.right_margin = Inches(0.85)

    normal = document.styles["Normal"]
    normal.font.name = "Aptos"
    normal.font.size = Pt(11)

    for style_name, size in [("Title", 22), ("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 11)]:
        if style_name in document.styles:
            document.styles[style_name].font.name = "Aptos"
            document.styles[style_name].font.size = Pt(size)

    document.core_properties.title = title or brand_obj.display_name
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_run = footer.add_run(
        " · ".join(part for part in [brand_obj.display_name, confidentiality, date.strftime("%B %Y")] if part)
    )
    footer_run.font.name = "Aptos"
    footer_run.font.size = Pt(9)

    renderer = _DocxHTMLRenderer(document)
    renderer.feed(_markdown_to_html(markdown))
    renderer.close()

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    document.save(out)
    return out.resolve()


def _cli() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        prog="inkline-docx",
        description="Convert a Markdown file to a branded DOCX document.",
    )
    parser.add_argument("input", help="Path to the Markdown (.md) file")
    parser.add_argument("--out", "-o", default=None, help="Output DOCX path")
    parser.add_argument("--brand", "-b", default="minimal", help="Brand name (default: minimal)")
    parser.add_argument("--title", "-t", default="", help="Document title")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        parser.error(f"File not found: {src}")

    out = Path(args.out) if args.out else src.with_suffix(".docx")
    md = src.read_text(encoding="utf-8")
    docx_path = export_docx(
        markdown=md,
        output_path=out,
        brand=args.brand,
        title=args.title,
    )
    print(f"  Brand  : {args.brand}")
    print(f"  Output : {docx_path}")


if __name__ == "__main__":
    _cli()
