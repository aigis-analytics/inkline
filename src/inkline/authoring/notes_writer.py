"""Inkline notes writer — emit ``<basename>.notes.txt`` from slide notes.

Format (D2 from the spec):

    ─── Slide 1 — Title slide ───────────────────────────────────────
    (no notes)

    ─── Slide 2 — Three pain points ─────────────────────────────────
    Emphasise the 80% number — this is the wedge.
    Don't dwell on the second card; it's table-stakes.

    ─── Slide 3 — Our solution ──────────────────────────────────────
    ...

The notes file sits alongside the PDF (same directory, same stem + ``.notes.txt``).
"""

from __future__ import annotations

from pathlib import Path


_LINE_WIDTH = 66


def _divider(slide_num: int, title: str) -> str:
    label = f"─── Slide {slide_num} — {title} "
    fill = "─" * max(0, _LINE_WIDTH - len(label))
    return label + fill


def write_notes(
    output_path: str | Path,
    slides: list[dict],
    sections: list[dict] | None = None,
) -> Path:
    """Write a ``<basename>.notes.txt`` file alongside the output PDF.

    Parameters
    ----------
    output_path : str | Path
        Path to the generated PDF (or any file in the output dir).
        Notes will be written to the same directory with the same stem.
    slides : list[dict]
        Slide spec list from DesignAdvisor (after design_deck()).
        Notes are read from ``slide.get("data", {}).get("notes")`` OR
        from the ``directives.notes`` field on the matching section.
    sections : list[dict] | None
        Original sections list from the preprocessor.  If provided,
        ``section["directives"]["notes"]`` is preferred over slide-level notes.

    Returns
    -------
    Path
        Absolute path to the written ``.notes.txt`` file.
    """
    output_path = Path(output_path)
    notes_path = output_path.with_suffix(".notes.txt")
    notes_path = notes_path.parent / (output_path.stem + ".notes.txt")

    lines: list[str] = []

    for i, slide in enumerate(slides, start=1):
        slide_type = slide.get("slide_type", "")
        data = slide.get("data", {})
        title = data.get("title", data.get("company", slide_type or f"Slide {i}"))

        # Prefer notes from the matching section's directives
        notes_text = ""
        if sections and i - 1 < len(sections):
            directives = sections[i - 1].get("directives", {})
            notes_text = directives.get("notes", "")

        # Fall back to slide data
        if not notes_text:
            notes_text = data.get("notes", "")

        lines.append(_divider(i, title))
        if notes_text:
            lines.append(notes_text.strip())
        else:
            lines.append("(no notes)")
        lines.append("")

    notes_path.write_text("\n".join(lines), encoding="utf-8")
    return notes_path


def collect_notes(sections: list[dict]) -> list[str]:
    """Extract notes strings from sections in preprocessor order.

    Returns a list parallel to sections (empty string if no notes).
    """
    result = []
    for sec in sections:
        directives = sec.get("directives", {})
        note = directives.get("notes", "")
        result.append(note)
    return result
