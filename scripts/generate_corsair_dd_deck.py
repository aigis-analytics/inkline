#!/usr/bin/env python3
"""Generate Project Corsair Board DD slide deck from the markdown report.

Minimal-direction approach: the raw markdown is parsed into sections by H2
heading and fed to DesignAdvisor. The LLM decides which data points matter,
which slide types to use, and what visual treatment works best.

Brand: aigis / template: dmd_stripe
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("corsair_gen")

from inkline.intelligence import DesignAdvisor
from inkline.typst import export_typst_slides

# ─── Paths ───────────────────────────────���────────────────────────────────────
SOURCE = Path("/mnt/d/aigis-agents-v2/domain_knowledge/Report_examples/Project_Corsair_Board_DD_Report_28Feb2026.md")
OUTPUT = SOURCE.parent / "Project_Corsair_Board_DD_Slides.pdf"

# ─── API Key ──────────────────────��────────────────────────────────────────���──
if not os.environ.get("ANTHROPIC_API_KEY"):
    for env_path in [
        Path("/mnt/d/aigis-agents-v2/.env"),
        Path.home() / ".env",
        Path("/mnt/d/copilot/.env"),
    ]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    os.environ["ANTHROPIC_API_KEY"] = line.split("=", 1)[1].strip()
                    break
            if os.environ.get("ANTHROPIC_API_KEY"):
                break


# ─── Parse markdown into raw sections ─────────────────────────────────────────
def parse_md_sections(md_text: str) -> list[dict]:
    """Split markdown on H2 headings; return minimal section dicts.

    Each section gets only: title + narrative (raw markdown body).
    The DesignAdvisor LLM decides what to extract and how to present it.
    """
    parts = re.split(r'^(## .+)$', md_text, flags=re.MULTILINE)
    # parts[0] = preamble (before first H2), then alternating heading/body
    sections = []
    i = 1
    while i + 1 < len(parts):
        heading = parts[i].lstrip("# ").strip()
        body = parts[i + 1].strip()
        if body:
            sections.append({
                "title": heading,
                "narrative": body,
            })
        i += 2
    return sections


md_text = SOURCE.read_text(encoding="utf-8")
raw_sections = parse_md_sections(md_text)

# ─── Run ──────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"INKLINE — Project Corsair Board DD Deck")
print(f"{'='*60}")
print(f"  Brand:    aigis / dmd_stripe")
print(f"  Sections: {len(raw_sections)} (raw markdown — no editorial)")
for i, s in enumerate(raw_sections):
    print(f"    [{i+1:2d}] {s['title'][:65]}")
print(f"  Output:   {OUTPUT}")
print(f"{'='*60}\n")

advisor = DesignAdvisor(
    brand="aigis",
    template="dmd_stripe",
    mode="llm",
    # No llm_caller needed — DesignAdvisor tries bridge first, then API
)

log.info("Calling DesignAdvisor (LLM mode)...")
slides = advisor.design_deck(
    title="Project Corsair — Board-Level Due Diligence",
    subtitle="Proposed Acquisition of Byron Energy LLC",
    date="28 February 2026",
    sections=raw_sections,
    audience="Board of Directors / Investment Committee",
    goal=(
        "Secure board approval for exclusivity bid of $130–145mm. "
        "Present the key financials, reserve position, upside opportunities, "
        "risks, and bid recommendation clearly and with impact."
    ),
    contact={
        "company": "Aigis Analytics",
        "name": "Aigis Analytics",
        "role": "Domain Intelligence, Deal Certainty",
        "email": "info@aigisanalytics.com",
        "tagline": "Strictly Confidential — Board Distribution Only",
    },
)

print(f"\nDesignAdvisor produced {len(slides)} slides:")
for i, s in enumerate(slides):
    stype = s.get("slide_type", "?")
    title = s.get("data", {}).get("title") or s.get("data", {}).get("company", "")
    print(f"  [{i+1:2d}] {stype:22s} — {str(title)[:55]}")

# Inject per-slide source sections for precise narrative fidelity audit.
# Match each slide to the section it was generated from by title word overlap.
# title/closing/section_divider slides are exempt (no narrative to check).
_EXEMPT_TYPES = {"title", "closing", "section_divider"}
for slide in slides:
    if slide.get("slide_type") in _EXEMPT_TYPES:
        continue
    slide_title_words = set(
        (slide.get("data", {}).get("title") or "").lower().split()
    ) - {"the", "a", "an", "of", "and", "for", "in", "to", "with"}
    if not slide_title_words:
        continue
    best_score, best_narrative = 0, ""
    for sec in raw_sections:
        sec_words = set(sec.get("title", "").lower().split())
        score = len(slide_title_words & sec_words)
        if score > best_score:
            best_score = score
            best_narrative = sec.get("narrative", "")
    if best_narrative:
        slide.setdefault("data", {})["source_section"] = best_narrative[:2000]

# Save debug JSON
debug_json = OUTPUT.with_suffix(".slides.json")
debug_json.write_text(json.dumps(slides, indent=2, default=str), encoding="utf-8")
log.info("Slides JSON: %s", debug_json)

print(f"\nRendering PDF...")
try:
    pdf_path = export_typst_slides(
        slides=slides,
        output_path=str(OUTPUT),
        brand="aigis",
        template="dmd_stripe",
        title="Project Corsair — Board-Level Due Diligence",
        date="28 February 2026",
        subtitle="Proposed Acquisition of Byron Energy LLC",
        source_narrative=md_text,  # Pass full report for narrative fidelity audit
        audit=True,
        auto_fix=True,
    )
    print(f"\n{'='*60}")
    print(f"DONE  →  {pdf_path}")
    print(f"{'='*60}")
except Exception as e:
    # Dump Typst source for debugging
    from inkline.brands import get_brand
    from inkline.typst.theme_registry import brand_to_typst_theme
    from inkline.typst.slide_renderer import TypstSlideRenderer, DeckSpec, SlideSpec

    brand_obj = get_brand("aigis")
    theme = brand_to_typst_theme(brand_obj, "dmd_stripe")
    deck = DeckSpec(
        slides=[SlideSpec(slide_type=s["slide_type"], data=s.get("data", {})) for s in slides],
        title="Project Corsair — Board-Level Due Diligence",
        date="28 February 2026",
        subtitle="Proposed Acquisition of Byron Energy LLC",
    )
    renderer = TypstSlideRenderer(theme, image_root=str(OUTPUT.parent))
    source = renderer.render_deck(deck)
    debug_typ = OUTPUT.with_suffix(".debug.typ")
    debug_typ.write_text(source, encoding="utf-8")
    print(f"\nERROR: {e}")
    print(f"Typst source: {debug_typ}")
    raise
