"""HTML page template — wraps rendered body in branded chrome."""

from __future__ import annotations

from inkline.brands import BaseBrand
from inkline.utils import b64_data_uri


# ── TOC JavaScript ───────────────────────────────────────────────────────

_TOC_JS = """
(function () {
  'use strict';
  var headings = Array.from(document.querySelectorAll('.markdown-body h2'));
  if (headings.length < 3) return;

  headings.forEach(function (h, i) {
    if (!h.id) h.id = 'section-' + (i + 1);
  });

  var toc = document.createElement('aside');
  toc.className = 'ink-toc';
  toc.setAttribute('aria-label', 'Table of contents');

  var title = document.createElement('div');
  title.className = 'ink-toc-title';
  title.textContent = 'Contents';
  toc.appendChild(title);

  var ol = document.createElement('ol');
  headings.forEach(function (h) {
    var li = document.createElement('li');
    var a  = document.createElement('a');
    a.href        = '#' + h.id;
    a.textContent = h.textContent.replace(/^[#\\s]+/, '').trim();
    li.appendChild(a);
    ol.appendChild(li);
  });
  toc.appendChild(ol);

  var wrap = document.querySelector('.ink-content-wrap');
  if (wrap) wrap.insertBefore(toc, wrap.firstChild);

  var links   = Array.from(toc.querySelectorAll('a'));
  var current = '';

  function onScroll() {
    var scrollY = window.scrollY + 80;
    var active  = headings[0].id;
    headings.forEach(function (h) {
      if (h.offsetTop <= scrollY) active = h.id;
    });
    if (active !== current) {
      links.forEach(function (a) {
        a.classList.toggle('active', a.getAttribute('href') === '#' + active);
      });
      current = active;
    }
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();
"""


def build_html_page(
    body_html: str,
    css: str,
    brand: BaseBrand,
    doc_title: str,
    confidentiality: str,
    footer_date: str,
    *,
    enable_mermaid: bool = True,
    enable_chartjs: bool = True,
    enable_toc: bool = True,
) -> str:
    """Assemble the full self-contained HTML document."""

    header_style = getattr(brand, "header_style", "bar")
    is_document = header_style == "document"
    display_name = brand.display_name

    # For document style, use light logo (dark/navy on white bg)
    # For bar style, use dark logo (white on dark bg)
    if is_document:
        logo_uri = b64_data_uri(brand.logo_light) if brand.logo_light.exists() else ""
    else:
        logo_uri = b64_data_uri(brand.logo_for_bg(brand.surface))

    logo_tag = (
        f'<img src="{logo_uri}" alt="{display_name}" class="ink-logo"/>'
        if logo_uri
        else (
            f'<span class="ink-logo-fallback">{display_name.upper()}</span>'
            if display_name else ""
        )
    )

    title_attr = doc_title or f"{display_name} Report"
    header_meta = doc_title or ""

    footer_parts = [p for p in [display_name, confidentiality, footer_date] if p]
    footer_line = "\u2002\u00b7\u2002".join(footer_parts)

    # Optional CDN scripts
    chartjs_tag = (
        '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4/dist/chart.umd.min.js"></script>'
        if enable_chartjs else ""
    )

    mermaid_tag = f"""
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'neutral',
      themeVariables: {{
        primaryColor: '{brand.primary}',
        primaryTextColor: '{brand.text}',
        primaryBorderColor: '{brand.border}',
        lineColor: '{brand.muted}',
        background: '{brand.light_bg}',
      }},
      flowchart: {{ htmlLabels: true, curve: 'basis' }},
    }});
  </script>""" if enable_mermaid else ""

    toc_script = f"<script>\n{_TOC_JS}\n</script>" if enable_toc else ""

    # Build header right content based on style
    tagline = getattr(brand, "tagline", "")
    if is_document and tagline:
        header_right = (
            f'<div class="ink-header-right">\n'
            f'      <span class="ink-header-tagline">{tagline}</span>\n'
            f'      <span class="ink-header-meta">{header_meta}</span>\n'
            f'    </div>'
        )
    else:
        header_right = (
            f'<div class="ink-header-right">\n'
            f'      <span class="ink-header-meta">{header_meta}</span>\n'
            f'    </div>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title_attr}</title>
  <style>
{css}
  </style>
</head>
<body>

  <header class="ink-header">
    {logo_tag}
    {header_right}
  </header>

  <div class="ink-content-wrap">
    <main class="markdown-body" id="report-body">
{body_html}
    </main>
  </div>

  <footer class="ink-footer">
    {footer_line}
  </footer>

  {chartjs_tag}
  {mermaid_tag}
  {toc_script}

</body>
</html>"""
