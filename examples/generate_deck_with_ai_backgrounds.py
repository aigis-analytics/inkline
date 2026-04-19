#!/usr/bin/env python3
"""
Example: Generate a slide deck with AI-generated backgrounds via n8n + Gemini.

This demonstrates the complete integration:
1. Define slide sections
2. Call n8n to generate backgrounds
3. Use backgrounds in Inkline slides
4. Export PDF with Archon audit

Usage:
  python3 examples/generate_deck_with_ai_backgrounds.py
"""

import json
from pathlib import Path

from inkline.intelligence import DesignAdvisor
from inkline.generative_assets import generate_background_image
from inkline.typst import export_typst_slides


def main():
    # Configuration
    N8N_WEBHOOK = "http://localhost:5678/webhook/inkblot-icon"
    OUTPUT_DIR = Path("~/.local/share/inkline/output").expanduser()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 0: Generate AI backgrounds
    # ─────────────────────────────────────────────────────────────────────────

    print("\n[GENERATION] Phase: generate_ai_backgrounds")

    backgrounds = {}
    background_prompts = {
        "hero": (
            "16:9 landscape background for a tech pitch deck, minimalist geometric style. "
            "Color: dark navy #1F2937 (80%), teal accent #06B6D4 (20% accent lines). "
            "Leave center-right clear for title text. No photographic textures, pure vector."
        ),
        "financials": (
            "16:9 landscape background for financial slides, corporate clean aesthetic. "
            "Color: slate #475569, emerald accent #10B981. "
            "Subtle grid lines in background, one bold accent stripe top-right. "
            "Leave center clear for charts."
        ),
        "closing": (
            "16:9 landscape background for closing slide, minimalist bold style. "
            "Color: deep purple #5B21B6, gold accent #FBBF24. "
            "Organic curved shapes, no text. Bold and memorable."
        ),
    }

    try:
        for slot, prompt in background_prompts.items():
            print(f"  Generating {slot}...", end=" ", flush=True)
            path = generate_background_image(N8N_WEBHOOK, prompt)
            backgrounds[slot] = path
            print(f"✓ {path}")
    except Exception as e:
        print(f"\n  ✗ Background generation failed: {e}")
        print("  Make sure n8n is running at", N8N_WEBHOOK)
        return

    print(f"[GENERATION] generate_ai_backgrounds → OK ({len(backgrounds)} backgrounds)")

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 1: Parse content
    # ─────────────────────────────────────────────────────────────────────────

    print("\n[ARCHON] Phase: parse_content")

    sections = [
        {
            "type": "narrative",
            "title": "Our Vision",
            "narrative": (
                "We're building the future of AI-powered document design. "
                "Inkline combines design intelligence with generative assets to enable "
                "anyone to create institutional-quality decks, reports, and documents."
            ),
            "metrics": {"Founded": "2024", "Customers": "50+"},
        },
        {
            "type": "kpi_dashboard",
            "title": "Traction",
            "metrics": {
                "Growth": "3.2x YoY",
                "NRR": "128%",
                "ARR": "$240K",
            },
        },
        {
            "type": "narrative",
            "title": "How It Works",
            "narrative": (
                "Users describe their deck in natural language. "
                "Inkline's AI engine generates section layouts, pulls in charts, "
                "and generates branded backgrounds via Gemini. "
                "The Archon pipeline audits every slide for quality. "
                "Export to PDF in seconds."
            ),
        },
    ]

    print(f"[ARCHON] parse_content → OK ({len(sections)} sections)")

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 2: Design advisor
    # ─────────────────────────────────────────────────────────────────────────

    print("\n[ARCHON] Phase: design_advisor_llm")

    advisor = DesignAdvisor(brand="minimal", template="consulting", mode="llm")
    slides = advisor.design_deck(
        title="Inkline",
        subtitle="AI-Powered Document Toolkit",
        sections=sections,
        audience="investors",
        goal="Series A fundraise",
    )

    print(f"[ARCHON] design_advisor_llm → OK ({len(slides)} slides)")

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 3: Insert backgrounds into slides
    # ─────────────────────────────────────────────────────────────────────────

    print("\n[ARCHON] Phase: integrate_backgrounds")

    # Title slide gets hero background
    if len(slides) > 0:
        slides[0].setdefault("data", {})["background_image"] = backgrounds.get("hero")

    # Content slide gets financials background
    for i, slide in enumerate(slides):
        if slide.get("slide_type") == "kpi_strip" or "Traction" in str(slide):
            slide.setdefault("data", {})["background_image"] = backgrounds.get("financials")

    # Closing slide gets closing background
    if len(slides) > 0:
        slides[-1].setdefault("data", {})["background_image"] = backgrounds.get("closing")

    print(f"[ARCHON] integrate_backgrounds → OK")

    # ─────────────────────────────────────────────────────────────────────────
    # Phase 4: Export to PDF
    # ─────────────────────────────────────────────────────────────────────────

    print("\n[ARCHON] Phase: export_pdf")

    output_path = OUTPUT_DIR / "inkline_ai_backgrounds_demo.pdf"

    export_typst_slides(
        slides=slides,
        output_path=str(output_path),
        brand="minimal",
        template="consulting",
        title="Inkline",
        date="April 2026",
    )

    print(f"[ARCHON] export_pdf → OK")
    print(f"\nPDF ready: {output_path}")
    print(f"\n✓ Deck with AI-generated backgrounds complete!")


if __name__ == "__main__":
    main()
