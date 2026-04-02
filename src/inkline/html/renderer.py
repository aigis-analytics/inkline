"""Markdown → HTML body rendering.

Supports two backends:
1. pypandoc (preferred — full GFM, smart quotes, emoji)
2. python-markdown (fallback — no external binary needed)
"""

from __future__ import annotations

import re


def pandoc_available() -> bool:
    """Return True when pypandoc is importable."""
    try:
        import pypandoc  # noqa: F401
        return True
    except ImportError:
        return False


def md_to_html_pandoc(md: str) -> str:
    """Convert Markdown to HTML body fragment via pypandoc."""
    import pypandoc
    pypandoc.ensure_pandoc_installed()
    return pypandoc.convert_text(
        md,
        to="html5",
        format="gfm+smart+emoji",
        extra_args=["--syntax-highlighting=none", "--wrap=none"],
    )


def md_to_html_python(md: str) -> str:
    """Convert Markdown to HTML via python-markdown."""
    import markdown as _md

    converter = _md.Markdown(
        extensions=[
            "tables",
            "fenced_code",
            "nl2br",
            "attr_list",
            "def_list",
            "footnotes",
            "toc",
            "sane_lists",
        ]
    )
    return converter.convert(md)


def md_to_html(md: str, force_python: bool = False) -> str:
    """Convert Markdown to HTML body fragment.

    Uses pypandoc when available, falls back to python-markdown.
    """
    if not force_python and pandoc_available():
        return md_to_html_pandoc(md)
    return md_to_html_python(md)


def normalise_mermaid(html: str) -> str:
    """Normalise pandoc's mermaid code block output for mermaid.js rendering."""
    # Pattern 1: <pre class="mermaid"><code>…</code></pre>
    html = re.sub(
        r'<pre\s+class="mermaid"><code>(.*?)</code></pre>',
        r'<pre class="mermaid">\1</pre>',
        html, flags=re.DOTALL,
    )
    # Pattern 2: <pre><code class="language-mermaid">…</code></pre>
    html = re.sub(
        r'<pre><code\s+class="language-mermaid">(.*?)</code></pre>',
        r'<pre class="mermaid">\1</pre>',
        html, flags=re.DOTALL,
    )
    # Pattern 3: sourceCode wrapper from pandoc syntax highlighting
    html = re.sub(
        r'<div\s+class="sourceCode"[^>]*>\s*'
        r'<pre\s+class="sourceCode\s+mermaid"[^>]*><code[^>]*>(.*?)</code></pre>\s*</div>',
        r'<pre class="mermaid">\1</pre>',
        html, flags=re.DOTALL,
    )
    return html
