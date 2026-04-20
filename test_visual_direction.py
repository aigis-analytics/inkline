#!/usr/bin/env python3
"""
Test script: Rebuild Brand Guidelines and Pitch decks with new Visual Direction Layer.

Tests:
1. Brand Guidelines deck with brand_editorial register
2. Pitch deck with investor_pitch register
3. Launchpad deck (backward compat, no DesignContext)

Section specs use structured exhibit types (kpi_dashboard, process_flow,
feature_grid, three_card, icon_stat, before_after) instead of plain
``type: content`` narrative blobs — this forces DesignAdvisor to pick
exhibit-driven slide types (metrics, diagrams, cards) rather than defaulting
to bullet-wall content slides.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from inkline.intelligence import DesignAdvisor, DesignContext
from inkline.typst import export_typst_slides


N8N_ENDPOINT = "http://localhost:5678/webhook/inkblot-icon"


def test_brand_guidelines():
    """Brand Guidelines: brand_editorial register, organic_ink style.

    Audience: design community. Focus: inspire.
    Uses structured section types so DesignAdvisor produces a feature grid,
    three-card philosophy, icon-stat palette, process-flow typography scale,
    and a before/after do-vs-don't — not prose bullets.
    """
    print("\n" + "="*60)
    print("TEST 1: Brand Guidelines Deck (with n8n background generation)")
    print("="*60)

    advisor = DesignAdvisor(brand="minimal", template="editorial")
    design_context = DesignContext(
        audience="design community",
        tone="visionary",
        focus="inspire",
        industry="design",
        deck_purpose="Inkline brand identity and design system guidelines"
    )

    sections = [
        # Cover — DesignAdvisor always synthesises a title slide
        {
            "type": "executive_summary",
            "title": "Inkline Brand Guidelines",
            "narrative": (
                "Inkline is a presentation design framework that produces "
                "visually coherent decks through systematic visual direction. "
                "These guidelines define what 'Inkline' looks and feels like."
            ),
        },
        # What is Inkline — 6-up feature grid
        {
            "type": "feature_grid",
            "title": "What is Inkline?",
            "features": [
                {"title": "Visual Direction", "body": "One brief drives palette, type, accents across every slide."},
                {"title": "Template System", "body": "11 slide templates × 7 brand identities."},
                {"title": "Archon Audit", "body": "LLM vision reviews every slide before ship."},
                {"title": "AI Backgrounds", "body": "Gemini-generated covers and dividers via n8n."},
                {"title": "Multi-brand", "body": "Private brand plugin system keeps IP out of the public repo."},
                {"title": "API-first", "body": "One Python call renders a full deck from structured data."},
            ],
        },
        # Visual Philosophy — three cards
        {
            "type": "comparison",
            "title": "Visual Philosophy",
            "cards": [
                {"title": "One brief, not 100 decisions",
                 "body": "Palette, type, and accent are decided once at deck level — every slide inherits."},
                {"title": "Exhibit over prose",
                 "body": "A chart, diagram, or card beats a bullet list. Prose is a fallback, not a default."},
                {"title": "Audit before ship",
                 "body": "Nothing leaves the pipeline until Archon signs off on every slide."},
            ],
        },
        # Palette System — icon stats with the 5 palette roles
        {
            "type": "kpi_dashboard",
            "title": "Palette System",
            "metrics": {
                "Primary (brand identity)": "#0F2A44",
                "Secondary (structural)": "#3D5A80",
                "Accent (emphasis only)": "#EE6C4D",
                "Text (body + heads)": "#1A1A1A",
                "Surface (page + cards)": "#F7F5F0",
            },
        },
        # Typography — process flow showing the scale hierarchy
        {
            "type": "process_flow",
            "title": "Typography Scale",
            "steps": [
                {"number": "1", "title": "Display 48pt",
                 "desc": "Cover and section dividers only. Used sparingly."},
                {"number": "2", "title": "Heading 28pt",
                 "desc": "Slide titles. Sentence case, action-oriented."},
                {"number": "3", "title": "Body 14pt",
                 "desc": "Card body, narrative, captions. 1.4 line height."},
                {"number": "4", "title": "Caption 10pt",
                 "desc": "Footnotes, sources, axis labels. Never for content."},
            ],
        },
        # Do / Don't — before/after
        {
            "type": "before_after",
            "title": "Do / Don't",
            "left": {
                "label": "DO",
                "items": [
                    "One accent colour per slide",
                    "Action titles (e.g., 'Revenue grew 34% YoY')",
                    "Exhibits first, prose second",
                    "Audit every slide before shipping",
                ],
            },
            "right": {
                "label": "DON'T",
                "items": [
                    "Rainbow palettes across slides",
                    "Topic-only titles (e.g., 'Revenue')",
                    "Walls of bullet points",
                    "Ship without visual review",
                ],
            },
        },
    ]

    try:
        slides = advisor.design_deck(
            title="Inkline Brand Guidelines",
            sections=sections,
            design_context=design_context,
            date="April 2026",
            n8n_endpoint=N8N_ENDPOINT,
        )

        output = Path("./brand_guidelines_v2.pdf")
        export_typst_slides(
            slides,
            output,
            brand="minimal",
            template="editorial",
            title="Inkline Brand Guidelines",
            date="April 2026",
            audit=True,
        )

        print(f"PASS Generated: {output}")
        print(f"  Slides: {len(slides)}")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pitch_deck():
    """Pitch Deck: investor_pitch register, abstract_geometric style.

    Audience: seed investors. Focus: persuade.
    Sections are KPI-first: every non-cover slide carries a concrete metric,
    process, or positioning diagram — no prose narrative stand-alones.
    """
    print("\n" + "="*60)
    print("TEST 2: Pitch Deck (with n8n background generation)")
    print("="*60)

    advisor = DesignAdvisor(brand="minimal", template="pitch")
    design_context = DesignContext(
        audience="seed investors",
        tone="visionary",
        focus="persuade",
        industry="tech",
        deck_purpose="Series A pitch for Inkline design automation platform"
    )

    sections = [
        # Cover
        {
            "type": "executive_summary",
            "title": "Inkline: AI Design Automation",
            "narrative": (
                "Inkline turns structured content into investor-grade decks "
                "in minutes. Visual direction, exhibit-first layouts, and a "
                "closed-loop visual auditor — all in one Python call."
            ),
        },
        # Problem — kpi dashboard with the pain metrics
        {
            "type": "kpi_dashboard",
            "title": "The Problem",
            "metrics": {
                "Time wasted on formatting": "40%",
                "Design tools: unchanged since": "2003",
                "Teams with consistent brand decks": "12%",
            },
        },
        # Solution — process flow showing the 3-step pipeline
        {
            "type": "process_flow",
            "title": "Our Solution",
            "steps": [
                {"number": "1", "title": "Describe content",
                 "desc": "Pass structured sections — metrics, steps, cards."},
                {"number": "2", "title": "Inkline designs every slide",
                 "desc": "Visual direction picks palette, type, layouts."},
                {"number": "3", "title": "Archon audits and delivers",
                 "desc": "LLM vision reviews each slide; ships a clean PDF."},
            ],
        },
        # Market — kpi dashboard with the market sizing numbers
        {
            "type": "kpi_dashboard",
            "title": "Market",
            "metrics": {
                "Market size": "$10B+",
                "Knowledge workers": "500M",
                "AI design penetration": "0%",
            },
        },
        # Traction — kpi dashboard with growth metrics
        {
            "type": "kpi_dashboard",
            "title": "Traction",
            "metrics": {
                "Beta users": "100",
                "NPS": "67",
                "Churn": "0%",
                "MoM growth": "+15%",
            },
        },
        # Close / ask — closing slide synthesised by DesignAdvisor
        {
            "type": "executive_summary",
            "title": "The Ask",
            "narrative": (
                "Raising $2M seed to scale the Inkline platform: hire three "
                "engineers, expand the brand plugin ecosystem, ship the "
                "self-serve web app. Join us."
            ),
        },
    ]

    try:
        slides = advisor.design_deck(
            title="Inkline: AI Design Automation",
            sections=sections,
            design_context=design_context,
            date="April 2026",
            n8n_endpoint=N8N_ENDPOINT,
        )

        output = Path("./pitch_deck_v2.pdf")
        export_typst_slides(
            slides,
            output,
            brand="minimal",
            template="pitch",
            title="Inkline: AI Design Automation",
            date="April 2026",
            audit=True,
        )

        print(f"PASS Generated: {output}")
        print(f"  Slides: {len(slides)}")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backward_compat():
    """Launchpad deck: backward compat test (no DesignContext)."""
    print("\n" + "="*60)
    print("TEST 3: Backward Compat (Launchpad, no DesignContext)")
    print("="*60)

    advisor = DesignAdvisor(brand="minimal", template="consulting")

    sections = [
        {
            "type": "content",
            "title": "Financial Summary",
            "narrative": "Q1 revenues grew 22% YoY to $4.2M. Operating margin improved 180bps through cost optimization.",
        },
        {
            "type": "content",
            "title": "Risk Mitigation",
            "narrative": "Rate risk hedged at 3.5% swap curve. Counterparty concentration reduced to 15% max. Liquidity buffer: 18 months.",
        },
    ]

    try:
        slides = advisor.design_deck(
            title="Launchpad Portfolio Review",
            sections=sections,
            audience="institutional lenders",  # Old style, no DesignContext
            goal="quarterly reporting",
            date="April 2026",
        )

        output = Path("./launchpad_backward_compat.pdf")
        export_typst_slides(
            slides,
            output,
            brand="minimal",
            template="consulting",
            title="Launchpad Portfolio Review",
            date="April 2026",
            audit=True,
        )

        print(f"PASS Generated: {output}")
        print(f"  Slides: {len(slides)}")
        print("  (No DesignContext — system inferred from audience/goal)")
        return True
    except Exception as e:
        print(f"FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    results = {
        "brand_guidelines": test_brand_guidelines(),
        "pitch": test_pitch_deck(),
        "backward_compat": test_backward_compat(),
    }

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)
