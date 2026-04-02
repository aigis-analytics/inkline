"""PDF rendering backends — WeasyPrint, Playwright, or browser headless.

All backends produce A4 PDFs with repeating branded header and footer.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from inkline.brands import BaseBrand

log = logging.getLogger(__name__)


def render_pdf(
    body_html: str,
    output_path: Path,
    brand: BaseBrand,
    logo_uri: str,
    doc_title: str,
    footer_text: str,
) -> None:
    """Render HTML body to branded PDF using best available backend."""

    # 1. WeasyPrint (preferred — excellent quality, repeating headers)
    try:
        _render_weasyprint(body_html, output_path, brand, logo_uri, doc_title, footer_text)
        return
    except (ImportError, OSError):
        pass

    # 2. Playwright / Chromium
    try:
        _render_playwright(body_html, output_path, brand, logo_uri, doc_title, footer_text)
        return
    except ImportError:
        pass

    # 3. System browser headless (Edge/Chrome)
    _render_browser(body_html, output_path, brand, logo_uri, doc_title, footer_text)


def _build_pdf_html(
    body_html: str,
    brand: BaseBrand,
    logo_uri: str,
    doc_title: str,
    footer_text: str,
    *,
    browser_mode: bool = False,
) -> str:
    """Build full HTML page for PDF rendering with branded header/footer."""

    title_block = f'<h1 class="doc-title">{doc_title}</h1>\n' if doc_title else ""
    logo_tag = (
        f'<img src="{logo_uri}" alt="{brand.display_name}" class="hdr-logo"/>'
        if logo_uri
        else (
            f'<span class="hdr-fallback">{brand.display_name.upper()}</span>'
            if brand.display_name else ""
        )
    )

    if browser_mode:
        page_css = "@page { size: A4; margin: 0; }"
        header_pos = "top: 0; left: 0; right: 0;"
        footer_pos = "bottom: 0; left: 0; right: 0;"
        body_padding = "padding: 72px 60px 52px 60px;"
    else:
        page_css = """@page {
  size: A4;
  margin-top: 72px;
  margin-bottom: 52px;
  margin-left: 60px;
  margin-right: 60px;
}"""
        header_pos = "top: -72px; left: -60px; right: -60px;"
        footer_pos = "bottom: -52px; left: -60px; right: -60px;"
        body_padding = ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{doc_title or f'{brand.display_name} Report'}</title>
<style>
{page_css}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

.page-header {{
  position: fixed;
  {header_pos}
  height: 56px;
  background: {brand.surface};
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 0 28px;
}}
.hdr-logo    {{ height: 30px; width: auto; }}
.hdr-fallback {{
  color: #ffffff;
  font-size: 12pt;
  font-weight: 700;
  letter-spacing: 0.8px;
}}

.page-footer {{
  position: fixed;
  {footer_pos}
  height: 40px;
  border-top: 1px solid {brand.border};
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 8pt;
  color: {brand.muted};
  background: #ffffff;
}}

body {{
  font-family: {brand.body_font}, "Helvetica Neue", Helvetica, Arial, sans-serif;
  font-size: 10.5pt;
  line-height: 1.65;
  color: {brand.text};
  background: #ffffff;
  {body_padding}
}}

h1, h2, h3, h4 {{
  page-break-after: avoid;
  font-family: {brand.heading_font}, {brand.body_font}, sans-serif;
}}
h1 {{
  font-size: 18pt; font-weight: 700; color: {brand.surface};
  margin: 24px 0 10px 0; padding-bottom: 6px;
  border-bottom: 2.5px solid {brand.primary};
}}
h1.doc-title {{ margin-top: 10px; }}
h2 {{
  font-size: 13pt; font-weight: 600; color: {brand.primary};
  margin: 20px 0 7px 0;
}}
h3 {{
  font-size: 11pt; font-weight: 600; color: {brand.surface};
  margin: 15px 0 5px 0;
}}
h4 {{
  font-size: 10.5pt; font-weight: 600; color: {brand.text};
  margin: 11px 0 4px 0;
}}

p  {{ margin: 0 0 9px 0; }}
strong {{ font-weight: 600; }}
a  {{ color: {brand.primary}; text-decoration: none; }}

ul, ol {{ margin: 5px 0 10px 0; padding-left: 22px; }}
li {{ margin: 2px 0; }}

table {{
  width: 100%; border-collapse: collapse;
  margin: 10px 0 16px 0; font-size: 9.5pt;
  page-break-inside: auto;
}}
thead tr {{
  background: {brand.surface}; color: #ffffff;
}}
thead th {{
  padding: 8px 10px; text-align: left; font-weight: 600;
  border: 1px solid {brand.surface};
}}
tbody tr {{ page-break-inside: avoid; }}
tbody tr:nth-child(even) {{ background: {brand.light_bg}; }}
tbody td {{
  padding: 7px 10px; border: 1px solid {brand.border};
  vertical-align: top;
}}

code {{
  font-family: {brand.mono_font}, "Courier New", monospace;
  font-size: 8.5pt; background: {brand.light_bg};
  padding: 1px 4px; border-radius: 2px; color: {brand.primary};
}}
pre {{
  background: {brand.light_bg}; border-left: 3px solid {brand.primary};
  padding: 10px 14px; margin: 8px 0 13px 0;
  font-size: 8.5pt; line-height: 1.5;
  white-space: pre-wrap; word-break: break-word;
  page-break-inside: avoid;
}}
pre code {{ background: transparent; padding: 0; color: {brand.text}; }}

blockquote {{
  border-left: 3px solid {brand.primary};
  margin: 8px 0 12px 0; padding: 7px 14px;
  background: {brand.light_bg}; color: #444;
}}

hr {{
  border: none; border-top: 1px solid {brand.border}; margin: 18px 0;
}}
</style>
</head>
<body>

<div class="page-header">
  {logo_tag}
</div>

<div class="page-footer">
  {footer_text}
</div>

{title_block}{body_html}

</body>
</html>"""


def _render_weasyprint(
    body_html: str,
    output_path: Path,
    brand: BaseBrand,
    logo_uri: str,
    doc_title: str,
    footer_text: str,
) -> None:
    """Render via WeasyPrint."""
    from weasyprint import HTML as WPhtml

    full_html = _build_pdf_html(
        body_html, brand, logo_uri, doc_title, footer_text,
        browser_mode=False,
    )
    WPhtml(string=full_html).write_pdf(str(output_path))


def _render_playwright(
    body_html: str,
    output_path: Path,
    brand: BaseBrand,
    logo_uri: str,
    doc_title: str,
    footer_text: str,
) -> None:
    """Render via Playwright Chromium."""
    from playwright.sync_api import sync_playwright

    # Playwright needs simpler body HTML — header/footer via templates
    title_block = f'<h1>{doc_title}</h1>\n' if doc_title else ""
    simple_html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
body {{ font-family: {brand.body_font}, sans-serif; font-size: 14px;
       max-width: 900px; margin: 0 auto; padding: 32px 48px; }}
h1 {{ border-bottom: 2px solid {brand.primary}; padding-bottom: 0.3em; }}
h2 {{ color: {brand.primary}; }}
table {{ border-collapse: collapse; width: 100%; margin-bottom: 16px; }}
th {{ background: {brand.surface}; color: #fff; padding: 6px 13px; border: 1px solid {brand.border}; }}
td {{ padding: 6px 13px; border: 1px solid {brand.border}; }}
</style></head><body>{title_block}{body_html}</body></html>"""

    # Header/footer templates
    if logo_uri:
        logo_html = f'<img src="{logo_uri}" style="height:26px;"/>'
    else:
        logo_html = f'<span style="color:#fff;font-size:11px;font-weight:700;">{brand.display_name.upper()}</span>'

    header_t = (
        f'<div style="width:100%;height:52px;background:{brand.surface};'
        f'display:flex;align-items:center;justify-content:flex-end;'
        f'padding:0 24px;">{logo_html}</div>'
    )
    footer_t = (
        f'<div style="width:100%;height:36px;border-top:0.5px solid {brand.border};'
        f'display:flex;align-items:center;justify-content:center;'
        f'font-size:9px;color:{brand.muted};">{footer_text}</div>'
    )

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.set_content(simple_html, wait_until="networkidle")
        page.pdf(
            path=str(output_path),
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template=header_t,
            footer_template=footer_t,
            margin={"top": "62px", "bottom": "46px", "left": "0px", "right": "0px"},
        )
        browser.close()


def _find_browser() -> Optional[str]:
    """Find a Chromium-based browser on the system."""
    candidates = [
        "google-chrome", "chromium-browser", "chromium", "microsoft-edge",
    ]
    # Also check common Windows paths
    win_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    ]
    for name in candidates:
        found = shutil.which(name)
        if found:
            return found
    for p in win_paths:
        if Path(p).exists():
            return p
    return None


def _render_browser(
    body_html: str,
    output_path: Path,
    brand: BaseBrand,
    logo_uri: str,
    doc_title: str,
    footer_text: str,
) -> None:
    """Render via system Edge/Chrome headless."""
    browser = _find_browser()
    if not browser:
        raise RuntimeError(
            "No PDF backend available. Install one of: "
            "weasyprint, playwright, or Google Chrome/Edge."
        )

    full_html = _build_pdf_html(
        body_html, brand, logo_uri, doc_title, footer_text,
        browser_mode=True,
    )

    with tempfile.NamedTemporaryFile(
        suffix=".html", mode="w", encoding="utf-8", delete=False
    ) as fh:
        fh.write(full_html)
        tmp_html = Path(fh.name)

    try:
        cmd = [
            browser,
            "--headless=new", "--disable-gpu", "--no-sandbox",
            f"--print-to-pdf={output_path}",
            "--no-pdf-header-footer",
            f"file:///{tmp_html.as_posix()}",
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=60)
        if not output_path.exists():
            stderr = result.stderr.decode(errors="replace")
            raise RuntimeError(f"Browser did not produce PDF.\nStderr: {stderr}")
    finally:
        tmp_html.unlink(missing_ok=True)
