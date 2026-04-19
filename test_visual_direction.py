#!/usr/bin/env python3
"""
Test script: Rebuild Brand Guidelines and Pitch decks with new Visual Direction Layer.

Tests:
1. Brand Guidelines deck with brand_editorial register
2. Pitch deck with investor_pitch register
3. Launchpad deck (backward compat, no DesignContext)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from inkline.intelligence import DesignAdvisor, DesignContext
from inkline.typst import export_typst_slides


def test_brand_guidelines():
    """Brand Guidelines: brand_editorial register, organic_ink style."""
    print("\n" + "="*60)
    print("TEST 1: Brand Guidelines Deck")
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
        {
            "type": "content",
            "title": "What is Inkline?",
            "narrative": "Inkline is a presentation design framework that makes decks visually compelling through systematic visual direction. Every slide follows the same palette, typography, and accent rules, creating cohesion.",
        },
        {
            "type": "content",
            "title": "Visual Philosophy",
            "narrative": "Visual coherence comes from consistent decisions: one accent color per slide, one template, one image treatment style. This creates the sense that every slide was designed together.",
        },
        {
            "type": "content",
            "title": "Palette System",
            "narrative": "The color palette includes dominant background, secondary structural color, accent for emphasis, and text colors. All other colors are derived from these 5 hex values.",
        },
    ]

    try:
        slides = advisor.design_deck(
            title="Inkline Brand Guidelines",
            sections=sections,
            design_context=design_context,
            date="April 2026",
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

        print(f"✓ Generated: {output}")
        print(f"  Slides: {len(slides)}")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_pitch_deck():
    """Pitch Deck: investor_pitch register, abstract_geometric style."""
    print("\n" + "="*60)
    print("TEST 2: Pitch Deck")
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
        {
            "type": "content",
            "title": "The Problem",
            "narrative": "Teams spend 40% of presentation time fighting design tools instead of focusing on the message. Design consistency is hard. Visual direction is a solved problem in print but broken in digital.",
        },
        {
            "type": "content",
            "title": "Our Solution",
            "narrative": "Inkline generates visually coherent decks automatically. Users describe the content; Inkline picks layouts, colors, and typography. One decision per deck (visual direction), not one per slide.",
        },
        {
            "type": "content",
            "title": "Market",
            "narrative": "5M knowledge workers create presentations annually. Current tools (PowerPoint, Google Slides) are 20+ years old, commodity pricing. Design-first tools (Canva, Gamma) lack automation.",
        },
        {
            "type": "content",
            "title": "Traction",
            "narrative": "100 beta users across venture studios and management consulting. NPS 67. Churn 0. Monthly active: growing 15% MoM.",
        },
    ]

    try:
        slides = advisor.design_deck(
            title="Inkline: AI Design Automation",
            sections=sections,
            design_context=design_context,
            date="April 2026",
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

        print(f"✓ Generated: {output}")
        print(f"  Slides: {len(slides)}")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
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

        print(f"✓ Generated: {output}")
        print(f"  Slides: {len(slides)}")
        print("  (No DesignContext — system inferred from audience/goal)")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
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
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")

    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)
