"""Inkline preprocessor — markdown → (deck_meta, sections[]).

Pipeline:
    raw markdown
      ├─► 1. extract front-matter            → deck_meta_yaml
      ├─► 2. walk markdown-it-py AST         → blocks
      ├─► 3. classify scope per block        → global / local / spot directives + content
      ├─► 4. apply headingDivider            → split into section list
      ├─► 5. parse asset shorthand           → infer _layout where omitted
      ├─► 6. apply spot/local cascades       → resolved per-section directives
      ├─► 7. run plugin directive callbacks  → merged directive dicts
      └─► 8. emit (deck_meta, sections[])

Output shape — each section dict is compatible with DesignAdvisor.design_deck():

    {
      "type": "narrative",         # legacy field
      "title": "Three problems",
      "narrative": "...",
      # NEW from directives:
      "slide_type": "three_card",  # from _layout
      "slide_mode": "guided",      # implied by _layout when fields incomplete
      "directives": {              # everything else: class, accent, bg, notes, …
          "class": "lead",
          "accent": "#0a8f5c",
          "notes": "Emphasise the 80% number.",
      },
      "source_line_start": 12,     # 1-based line number of the heading
      "source_line_end": 24,       # 1-based line number of the last content line
    }
"""

from __future__ import annotations

import logging
import re
import warnings
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Lazy imports (avoid hard-dep at module load if not installed)
# ---------------------------------------------------------------------------

def _get_md():
    """Return a configured markdown-it instance with front_matter plugin."""
    try:
        from markdown_it import MarkdownIt
        from mdit_py_plugins.front_matter import front_matter_plugin
    except ImportError as exc:
        raise ImportError(
            "markdown-it-py and mdit-py-plugins are required for the authoring "
            "preprocessor. Install them with: "
            "pip install markdown-it-py mdit-py-plugins"
        ) from exc

    md = MarkdownIt().use(front_matter_plugin)
    return md


# ---------------------------------------------------------------------------
# YAML parsing (stdlib-safe fallback: PyYAML if available, else simple parser)
# ---------------------------------------------------------------------------

def _parse_yaml(text: str) -> dict:
    try:
        import yaml  # type: ignore[import]
        return yaml.safe_load(text) or {}
    except ImportError:
        pass
    # Minimal YAML-like parser for simple key: value (no nested blocks)
    result: dict = {}
    for line in text.splitlines():
        if ":" in line and not line.startswith(" "):
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1]
            elif v.startswith("'") and v.endswith("'"):
                v = v[1:-1]
            result[k] = v
    return result


# ---------------------------------------------------------------------------
# HTML-comment directive extraction
# ---------------------------------------------------------------------------

_COMMENT_RE = re.compile(r"<!--(.*?)-->", re.DOTALL)


def _extract_directives_from_comment(comment_body: str) -> dict:
    """Parse YAML content from an HTML comment body.

    Returns a dict (empty if no valid YAML found).
    """
    text = comment_body.strip()
    if not text:
        return {}
    parsed = _parse_yaml(text)
    if isinstance(parsed, dict):
        return parsed
    return {}


# ---------------------------------------------------------------------------
# Core preprocessor
# ---------------------------------------------------------------------------

def preprocess(
    markdown_text: str,
    *,
    strict_directives: bool = False,
    source_path: str | None = None,
) -> tuple[dict, list[dict]]:
    """Parse markdown text into (deck_meta, sections[]).

    Parameters
    ----------
    markdown_text : str
        Full markdown source.
    strict_directives : bool
        If True, unknown or invalid directives raise DirectiveError.
    source_path : str | None
        Path to the source file (used for import resolution and error messages).

    Returns
    -------
    tuple[dict, list[dict]]
        ``(deck_meta, sections)`` where:
        - ``deck_meta`` contains global directives (brand, template, title, …)
        - ``sections`` is a list of section dicts ready for DesignAdvisor
    """
    from inkline.authoring.directives import resolve_directive

    md = _get_md()

    # ── Step 1: expand imports ──────────────────────────────────────────────
    if source_path:
        markdown_text = _expand_imports(markdown_text, source_path, strict=strict_directives)

    # ── Step 2: parse tokens ─────────────────────────────────────────────────
    tokens = md.parse(markdown_text)

    # ── Step 3: extract front-matter ─────────────────────────────────────────
    deck_meta: dict[str, Any] = {}
    fm_end_line = 0

    for tok in tokens:
        if tok.type == "front_matter":
            raw_fm = tok.content.strip()
            parsed = _parse_yaml(raw_fm)
            if isinstance(parsed, dict):
                for k, v in parsed.items():
                    canon_name, canon_val = resolve_directive(
                        k, v, deck_meta, strict=strict_directives
                    )
                    deck_meta[canon_name] = canon_val
            fm_end_line = tok.map[1] if tok.map else 0
            break

    # Apply defaults for missing global directives
    from inkline.authoring.directives import _GLOBAL_DIRECTIVES
    for k, schema in _GLOBAL_DIRECTIVES.items():
        if k not in deck_meta and "default" in schema:
            deck_meta[k] = schema["default"]

    heading_level = int(deck_meta.get("headingDivider", 2))

    # ── Step 4: walk tokens, split into raw sections ──────────────────────────
    raw_sections = _split_into_sections(tokens, heading_level, fm_end_line)

    # ── Step 5: resolve directives per section ────────────────────────────────
    sections: list[dict] = []
    local_cascade: dict = {}  # directives that cascade from a "local" comment

    for raw in raw_sections:
        section = _resolve_section(
            raw, deck_meta, local_cascade, strict=strict_directives
        )
        # Update local cascade from any non-spot directives in this section
        new_locals = {
            k: v for k, v in section.get("directives", {}).items()
            if not k.startswith("_")
        }
        local_cascade.update(new_locals)
        sections.append(section)

    return deck_meta, sections


# ---------------------------------------------------------------------------
# Token walker
# ---------------------------------------------------------------------------

def _split_into_sections(
    tokens: list,
    heading_level: int,
    skip_before_line: int,
) -> list[dict]:
    """Walk markdown-it tokens and split at ``## `` headings (or configured level).

    Returns a list of "raw section" dicts:
        {
          "title": str,
          "title_line": int,       # 1-based
          "content_tokens": [...], # tokens between this heading and the next
          "pre_heading_comments": [dict, ...],  # HTML comments before heading
          "inline_comments": [dict, ...],       # HTML comments in body
        }
    """
    # Heading marker: ``#`` repeated heading_level times
    heading_marker = "#" * heading_level

    sections: list[dict] = []
    current: dict | None = None
    pre_heading_comments: list[dict] = []  # comments before first heading
    global_comments: list[dict] = []       # same thing, kept separately for deck_meta

    i = 0
    while i < len(tokens):
        tok = tokens[i]

        # Skip front-matter token
        if tok.type == "front_matter":
            i += 1
            continue

        line_no = (tok.map[0] + 1) if tok.map else 0  # 1-based

        # Detect HTML comments (directive blocks)
        if tok.type == "html_block":
            for m in _COMMENT_RE.finditer(tok.content):
                directives = _extract_directives_from_comment(m.group(1))
                if directives:
                    comment_info = {"directives": directives, "line": line_no}
                    if current is None:
                        pre_heading_comments.append(comment_info)
                        global_comments.append(comment_info)
                    else:
                        current["inline_comments"].append(comment_info)
            i += 1
            continue

        # Detect headings at the configured level
        if tok.type == "heading_open":
            level_str = tok.tag  # e.g. "h2"
            level = int(level_str[1]) if level_str and level_str[0] == "h" else 0

            if level == heading_level:
                # Close previous section
                if current is not None:
                    current["end_line"] = line_no - 1
                    sections.append(current)

                # Read heading inline content
                title = ""
                if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                    title = tokens[i + 1].content
                    i += 2  # skip inline + heading_close

                current = {
                    "title": title,
                    "title_line": line_no,
                    "end_line": line_no,
                    "content_tokens": [],
                    "pre_heading_comments": pre_heading_comments[:],
                    "inline_comments": [],
                    "global_comments": global_comments[:],
                }
                pre_heading_comments = []
                continue

        # Accumulate content into current section
        if current is not None:
            current["content_tokens"].append(tok)
            if tok.map:
                current["end_line"] = tok.map[1]

        i += 1

    # Close final section
    if current is not None:
        sections.append(current)

    return sections


# ---------------------------------------------------------------------------
# Section resolver
# ---------------------------------------------------------------------------

def _resolve_section(
    raw: dict,
    deck_meta: dict,
    local_cascade: dict,
    strict: bool = False,
) -> dict:
    """Convert a raw section dict into the canonical section dict.

    Applies directive cascading (global → local cascade → spot).
    """
    from inkline.authoring.directives import resolve_directive
    from inkline.authoring.asset_shorthand import parse_asset_shorthand, infer_layout_from_assets

    title = raw["title"]
    title_line = raw.get("title_line", 0)
    end_line = raw.get("end_line", title_line)

    # ── Collect directives ────────────────────────────────────────────────────
    # Start with local cascade (carries forward from previous slides)
    resolved: dict = dict(local_cascade)
    spot_overrides: dict = {}

    # Apply pre-heading comments (global/local scope)
    for comment in raw.get("pre_heading_comments", []):
        for k, v in comment["directives"].items():
            is_spot = k.startswith("_")
            canon_k, canon_v = resolve_directive(k, v, deck_meta, strict=strict)
            if is_spot:
                spot_overrides[canon_k] = canon_v
            else:
                resolved[canon_k] = canon_v

    # Apply inline comments
    for comment in raw.get("inline_comments", []):
        for k, v in comment["directives"].items():
            is_spot = k.startswith("_")
            canon_k, canon_v = resolve_directive(k, v, deck_meta, strict=strict)
            if is_spot:
                spot_overrides[canon_k] = canon_v
            else:
                resolved[canon_k] = canon_v

    # Merge spot overrides on top
    resolved.update(spot_overrides)

    # ── Extract narrative text ────────────────────────────────────────────────
    narrative = _tokens_to_text(raw.get("content_tokens", []))

    # ── Handle asset shorthand ────────────────────────────────────────────────
    bg_assets = _extract_bg_images(raw.get("content_tokens", []))
    inferred_layout: dict = {}
    if bg_assets:
        inferred = infer_layout_from_assets(bg_assets)
        for k, v in inferred.items():
            if k == "slide_type":
                # Store separately — will apply below after directive-based layout
                inferred_layout["slide_type"] = v
            elif k in ("multi_layout", "image_paths", "image_path", "_bg_side", "_bg_width", "_bg_fill"):
                inferred_layout[k] = v
            elif k not in resolved:  # don't override explicit directives
                resolved[k] = v

    # ── Build section dict ────────────────────────────────────────────────────
    section: dict = {
        "type": "narrative",
        "title": title,
        "narrative": narrative,
        "source_line_start": title_line,
        "source_line_end": end_line,
    }

    # Map ``layout`` directive → slide_type + slide_mode
    layout = resolved.pop("layout", None) or resolved.pop("_layout", None)
    if layout:
        section["slide_type"] = layout
        slide_mode = resolved.pop("_mode", resolved.pop("mode", "guided"))
        section["slide_mode"] = slide_mode
    elif inferred_layout.get("slide_type"):
        # From asset shorthand — apply inferred layout
        section["slide_type"] = inferred_layout["slide_type"]
        section["slide_mode"] = "guided"
        # Merge other inferred fields (image_path, etc.) into section or directives
        for k, v in inferred_layout.items():
            if k != "slide_type" and k not in section:
                resolved[k] = v

    # Map ``_mode`` spot override to slide_mode (when no layout directive)
    elif "_mode" in resolved:
        section["slide_mode"] = resolved.pop("_mode")

    # ── Notes → directives ───────────────────────────────────────────────────
    notes = resolved.pop("_notes", resolved.pop("notes", None))
    if notes:
        resolved["notes"] = notes

    # ── Store remaining directives ────────────────────────────────────────────
    # Strip spot-prefix keys that weren't layout/mode/notes (pass through)
    cleaned: dict = {}
    for k, v in resolved.items():
        if k.startswith("_") and k not in ("_bg", "_class", "_header", "_footer", "_accent", "_paginate"):
            # Unknown spot directive — strip underscore and store
            cleaned[k[1:]] = v
        else:
            cleaned[k] = v

    if cleaned:
        section["directives"] = cleaned

    return section


# ---------------------------------------------------------------------------
# Text extraction from tokens
# ---------------------------------------------------------------------------

def _tokens_to_text(tokens: list) -> str:
    """Extract plain text from a list of markdown-it tokens."""
    parts = []
    for tok in tokens:
        if tok.type == "inline":
            parts.append(tok.content)
        elif tok.type in ("bullet_list_open", "ordered_list_open"):
            pass  # handled via inline children
        elif tok.type == "html_block":
            pass  # skip — already processed as directives
    return "\n".join(p for p in parts if p.strip())


def _extract_bg_images(tokens: list) -> list:
    """Find ``![bg ...]`` image shorthand tokens and parse them."""
    from inkline.authoring.asset_shorthand import parse_asset_shorthand
    assets = []
    for tok in tokens:
        if tok.type != "inline":
            continue
        if not tok.children:
            continue
        j = 0
        while j < len(tok.children):
            child = tok.children[j]
            if child.type == "image":
                alt_text = ""
                # Collect alt text from children of the image token
                for grandchild in (child.children or []):
                    if grandchild.type == "text":
                        alt_text += grandchild.content
                src = child.attrGet("src") or ""
                result = parse_asset_shorthand(alt_text, src)
                if result is not None:
                    assets.append(result)
            j += 1
    return assets


# ---------------------------------------------------------------------------
# Import expansion
# ---------------------------------------------------------------------------

def _expand_imports(markdown_text: str, source_path: str, strict: bool = False) -> str:
    """Expand ``import: [...]`` front-matter directives by inlining referenced files."""
    # Quick check — only bother if "import:" appears in first 30 lines
    first_lines = "\n".join(markdown_text.splitlines()[:30])
    if "import:" not in first_lines:
        return markdown_text

    # Parse front-matter to find imports
    fm_match = re.match(r"^---\n(.*?)\n---", markdown_text, re.DOTALL)
    if not fm_match:
        return markdown_text

    fm = _parse_yaml(fm_match.group(1))
    imports = fm.get("import", [])
    if not imports:
        return markdown_text

    if isinstance(imports, str):
        imports = [imports]

    base_dir = Path(source_path).parent
    prepend_blocks: list[str] = []
    for imp in imports:
        imp_path = base_dir / imp
        try:
            prepend_blocks.append(imp_path.read_text(encoding="utf-8"))
        except OSError as exc:
            msg = f"import: cannot read {imp_path}: {exc}"
            if strict:
                from inkline.authoring.directives import DirectiveError
                raise DirectiveError(msg) from exc
            log.warning(msg)

    if prepend_blocks:
        # Prepend imported content after the front-matter block
        fm_end = fm_match.end()
        return (
            markdown_text[: fm_end]
            + "\n\n"
            + "\n\n".join(prepend_blocks)
            + "\n\n"
            + markdown_text[fm_end:]
        )

    return markdown_text


# ---------------------------------------------------------------------------
# Backwards-compatibility shim
# ---------------------------------------------------------------------------

def markdown_to_sections(
    markdown_text: str,
    heading_level: int = 2,
) -> list[dict]:
    """Legacy shim — convert markdown to sections list like the old _text_to_sections.

    Uses the new preprocessor but returns only the sections (no deck_meta).
    Preserves identical output for markdown with no directives.
    """
    _, sections = preprocess(markdown_text)
    return sections
