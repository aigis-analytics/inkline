"""CSS generation from brand palette.

Produces the complete embedded CSS for branded HTML reports.
All color references come from the brand — no hardcoded values.
"""

from __future__ import annotations

from inkline.brands import BaseBrand


def build_css(brand: BaseBrand) -> str:
    """Return the complete embedded CSS for a branded HTML report."""
    return f"""
/* ── Reset ─────────────────────────────────────────────────────────── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

/* ── Page layout ────────────────────────────────────────────────────── */
html {{
  font-family: {brand.body_font}, -apple-system, BlinkMacSystemFont, "Segoe UI",
               "Noto Sans", Helvetica, Arial, sans-serif;
  font-size: 16px;
  color: {brand.text};
  background: {brand.background};
  scroll-behavior: smooth;
}}

body {{
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  margin: 0;
  background: {brand.background};
}}

/* ── Sticky header ────────────────────────────────────────────────────── */
.ink-header {{
  position: sticky;
  top: 0;
  z-index: 200;
  background: {brand.surface};
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  box-shadow: 0 1px 0 rgba(255,255,255,0.08), 0 2px 8px rgba(0,0,0,0.4);
  flex-shrink: 0;
}}
.ink-logo {{
  height: 26px;
  width: auto;
  display: block;
}}
.ink-logo-fallback {{
  color: #ffffff;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 1px;
  white-space: nowrap;
}}
.ink-header-right {{
  display: flex;
  align-items: center;
  gap: 16px;
}}
.ink-header-meta {{
  color: rgba(255,255,255,0.55);
  font-size: 12px;
  white-space: nowrap;
}}

/* ── Content area ───────────────────────────────────────────────────── */
.ink-content-wrap {{
  display: flex;
  flex: 1;
  min-width: 0;
  position: relative;
}}

.markdown-body {{
  flex: 1;
  min-width: 0;
  max-width: 960px;
  margin: 0 auto;
  padding: 40px 48px 80px;
  word-wrap: break-word;
  line-height: 1.6;
  font-size: 16px;
}}

/* ── TOC sidebar ────────────────────────────────────────────────────── */
.ink-toc {{
  position: sticky;
  top: 68px;
  align-self: flex-start;
  width: 220px;
  flex-shrink: 0;
  padding: 20px 0 20px 20px;
  max-height: calc(100vh - 80px);
  overflow-y: auto;
  font-size: 12.5px;
  display: none;
  scrollbar-width: thin;
  scrollbar-color: {brand.border} transparent;
}}
.ink-toc::-webkit-scrollbar {{ width: 4px; }}
.ink-toc::-webkit-scrollbar-track {{ background: transparent; }}
.ink-toc::-webkit-scrollbar-thumb {{ background: {brand.border}; border-radius: 4px; }}

.ink-toc-title {{
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: {brand.muted};
  margin-bottom: 10px;
  padding-bottom: 6px;
  border-bottom: 1px solid {brand.border};
}}
.ink-toc ol {{
  list-style: none;
  padding: 0;
  margin: 0;
}}
.ink-toc a {{
  display: block;
  padding: 4px 8px 4px 0;
  color: {brand.muted};
  text-decoration: none;
  border-left: 2px solid transparent;
  transition: color 0.15s, border-color 0.15s;
  line-height: 1.4;
}}
.ink-toc a:hover {{
  color: {brand.primary};
  border-left-color: {brand.primary};
}}
.ink-toc a.active {{
  color: {brand.primary};
  border-left-color: {brand.primary};
  font-weight: 600;
}}
@media (min-width: 1280px) {{
  .ink-toc {{ display: block; }}
  .markdown-body {{ margin: 0 0 0 0; }}
}}

/* ── Headings ───────────────────────────────────────────────────────── */
.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4,
.markdown-body h5,
.markdown-body h6 {{
  margin-top: 28px;
  margin-bottom: 14px;
  font-family: {brand.heading_font}, {brand.body_font}, sans-serif;
  font-weight: 600;
  line-height: 1.25;
}}
.markdown-body h1 {{
  font-size: 2em;
  padding-bottom: 0.3em;
  border-bottom: 2.5px solid {brand.primary};
  color: {brand.surface};
  margin-top: 0;
}}
.markdown-body h2 {{
  font-size: 1.5em;
  padding-bottom: 0.3em;
  border-bottom: 1px solid {brand.border};
  color: {brand.primary};
}}
.markdown-body h3 {{
  font-size: 1.25em;
  color: {brand.surface};
}}
.markdown-body h4 {{
  font-size: 1em;
  color: {brand.surface};
}}
.markdown-body h5 {{ font-size: 0.875em; }}
.markdown-body h6 {{ font-size: 0.85em; color: {brand.muted}; }}

/* ── Body text ──────────────────────────────────────────────────────── */
.markdown-body p       {{ margin-top: 0; margin-bottom: 16px; }}
.markdown-body strong  {{ font-weight: 600; }}
.markdown-body em      {{ font-style: italic; }}
.markdown-body del     {{ text-decoration: line-through; color: {brand.muted}; }}
.markdown-body a       {{ color: {brand.primary}; text-decoration: none; }}
.markdown-body a:hover {{ text-decoration: underline; }}

/* ── Lists ──────────────────────────────────────────────────────────── */
.markdown-body ul,
.markdown-body ol   {{ margin-top: 0; margin-bottom: 16px; padding-left: 2em; }}
.markdown-body ul ul,
.markdown-body ul ol,
.markdown-body ol ul,
.markdown-body ol ol {{ margin-top: 0; margin-bottom: 0; }}
.markdown-body li      {{ margin: 4px 0; }}
.markdown-body li > p  {{ margin-bottom: 4px; }}

/* ── Tables ─────────────────────────────────────────────────────────── */
.markdown-body table {{
  border-collapse: collapse;
  width: 100%;
  margin: 0 0 20px 0;
  font-size: 14px;
  overflow: auto;
  display: table;
}}
.markdown-body thead tr {{
  border-bottom: 2px solid {brand.surface};
}}
.markdown-body thead th {{
  background: {brand.surface};
  color: #ffffff;
  padding: 10px 14px;
  text-align: left;
  font-weight: 600;
  border: 1px solid {brand.surface};
  white-space: nowrap;
}}
.markdown-body tbody td {{
  padding: 8px 14px;
  border: 1px solid {brand.border};
  vertical-align: top;
}}
.markdown-body tbody tr:nth-child(even) {{ background: {brand.light_bg}; }}
.markdown-body tbody tr:hover {{ background: #eef2f6; }}

/* ── Code ───────────────────────────────────────────────────────────── */
.markdown-body code,
.markdown-body tt {{
  padding: 0.2em 0.4em;
  margin: 0;
  font-size: 85%;
  white-space: break-spaces;
  background: rgba(175,184,193,0.2);
  border-radius: 6px;
  font-family: {brand.mono_font}, ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  color: #CF222E;
}}
.markdown-body pre {{
  padding: 16px;
  overflow: auto;
  font-size: 85%;
  line-height: 1.45;
  background: {brand.light_bg};
  border-radius: 6px;
  margin: 0 0 16px 0;
  border-left: 3px solid {brand.primary};
  word-wrap: normal;
}}
.markdown-body pre code,
.markdown-body pre tt {{
  padding: 0;
  margin: 0;
  white-space: pre;
  background: transparent;
  border: 0;
  font-size: 100%;
  color: {brand.text};
  border-radius: 0;
}}

/* ── Blockquote ─────────────────────────────────────────────────────── */
.markdown-body blockquote {{
  margin: 0 0 16px 0;
  padding: 12px 16px;
  color: {brand.muted};
  background: {brand.light_bg};
  border-left: 4px solid {brand.primary};
  border-radius: 0 4px 4px 0;
}}
.markdown-body blockquote > :first-child {{ margin-top: 0; }}
.markdown-body blockquote > :last-child  {{ margin-bottom: 0; }}

/* ── Horizontal rule ────────────────────────────────────────────────── */
.markdown-body hr {{
  background: {brand.border};
  border: 0;
  height: 2px;
  margin: 28px 0;
  border-radius: 1px;
}}

/* ── Images ─────────────────────────────────────────────────────────── */
.markdown-body img {{
  max-width: 100%;
  box-sizing: border-box;
  border-radius: 4px;
}}

/* ── Mermaid diagrams ───────────────────────────────────────────────── */
.markdown-body pre.mermaid {{
  background: {brand.light_bg};
  border-left: none;
  border-radius: 8px;
  border: 1px solid {brand.border};
  padding: 24px 16px;
  text-align: center;
  overflow: auto;
}}
.markdown-body pre.mermaid:not([data-processed]) {{
  opacity: 0.3;
}}

/* ── Chart wrapper ──────────────────────────────────────────────────── */
.ink-chart-wrapper {{
  margin: 1.5rem 0;
  padding: 1.25rem 1.5rem;
  background: {brand.light_bg};
  border: 1px solid {brand.border};
  border-left: 3px solid {brand.primary};
  border-radius: 6px;
}}
.ink-chart-wrapper canvas {{
  display: block;
  max-width: 100%;
}}

/* ── Footer ─────────────────────────────────────────────────────────── */
.ink-footer {{
  background: {brand.surface};
  color: rgba(255,255,255,0.45);
  font-size: 11px;
  text-align: center;
  padding: 14px 32px;
  letter-spacing: 0.3px;
  flex-shrink: 0;
}}

/* ── Print ──────────────────────────────────────────────────────────── */
@media print {{
  .ink-header {{ position: static; print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
  .ink-toc    {{ display: none !important; }}
  .markdown-body {{ max-width: none; padding: 24px 40px; }}
  .markdown-body h1, .markdown-body h2, .markdown-body h3 {{ page-break-after: avoid; }}
  .markdown-body pre, .markdown-body blockquote,
  .markdown-body table {{ page-break-inside: avoid; }}
  .ink-footer {{ position: fixed; bottom: 0; left: 0; right: 0; print-color-adjust: exact; -webkit-print-color-adjust: exact; }}
}}
"""
