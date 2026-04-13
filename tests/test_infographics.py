"""Test all 16 infographic renderers.

Renders each type to /tmp/inkline_infographics/<type>.png and verifies
the file exists and is > 5 KB (proving a real figure was produced).

Usage:
    python3 tests/test_infographics.py   # standalone
    pytest tests/test_infographics.py    # via pytest
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

OUT_DIR = Path("/tmp/inkline_infographics")

# ---------------------------------------------------------------------------
# Test data for all 16 types
# ---------------------------------------------------------------------------

TEST_CASES: dict[str, dict] = {
    "iceberg": {
        "above": [
            {"label": "Strategy", "desc": "Visible goals and milestones"},
            {"label": "Product", "desc": "Public roadmap features"},
        ],
        "below": [
            {"label": "Technical Debt", "desc": "Accumulated legacy code"},
            {"label": "Team Dynamics", "desc": "Interpersonal friction"},
            {"label": "Process Gaps", "desc": "Unwritten workflows"},
            {"label": "Assumptions", "desc": "Unvalidated beliefs"},
        ],
        "above_label": "What's Visible",
        "below_label": "What's Hidden",
    },
    "funnel_ribbon": {
        "stages": [
            {"label": "Awareness", "value": "10,000"},
            {"label": "Interest", "value": "4,200"},
            {"label": "Consideration", "value": "1,800"},
            {"label": "Intent", "value": "650"},
            {"label": "Purchase", "value": "310"},
        ],
        "title": "Sales Funnel",
    },
    "waffle": {
        "categories": [
            {"label": "Enterprise", "value": 42},
            {"label": "SMB", "value": 33},
            {"label": "Consumer", "value": 25},
        ],
        "rows": 10,
        "columns": 10,
    },
    "dual_donut": {
        "outer": {
            "title": "Revenue",
            "segments": [
                {"label": "APAC", "value": 38},
                {"label": "EMEA", "value": 35},
                {"label": "Americas", "value": 27},
            ],
        },
        "inner": {
            "title": "Costs",
            "segments": [
                {"label": "R&D", "value": 45},
                {"label": "Sales", "value": 30},
                {"label": "Ops", "value": 25},
            ],
        },
    },
    "hexagonal_honeycomb": {
        "cells": [
            {"title": "Innovation", "value": "92%", "subtitle": "YoY growth"},
            {"title": "Quality", "value": "4.8★", "subtitle": "Avg rating"},
            {"title": "Speed", "value": "2.1x", "subtitle": "vs last yr"},
            {"title": "Coverage", "value": "78%", "subtitle": "Market share"},
            {"title": "Retention", "value": "94%", "subtitle": "Annual"},
            {"title": "NPS", "value": "68", "subtitle": "Net promoter"},
        ],
        "columns": 3,
    },
    "radial_pinwheel": {
        "center": {"title": "Platform", "subtitle": "Core value"},
        "items": [
            {"title": "Data Layer", "body": "Real-time ingestion"},
            {"title": "AI Engine", "body": "ML inference"},
            {"title": "API Gateway", "body": "Rate limiting"},
            {"title": "Dashboard", "body": "Self-service BI"},
            {"title": "Security", "body": "Zero-trust model"},
            {"title": "Integrations", "body": "200+ connectors"},
        ],
    },
    "semicircle_taxonomy": {
        "groups": [
            {"name": "Technical", "items": ["Python", "SQL", "APIs", "Cloud"]},
            {"name": "Business", "items": ["Strategy", "Finance", "GTM"]},
            {"name": "Design", "items": ["UX", "Brand"]},
        ],
        "center_label": "Skills",
    },
    "process_curved_arrows": {
        "steps": [
            {"number": 1, "title": "Discovery", "body": "Identify user needs"},
            {"number": 2, "title": "Design", "body": "Prototype solutions"},
            {"number": 3, "title": "Build", "body": "Sprint delivery"},
            {"number": 4, "title": "Test", "body": "QA & validation"},
            {"number": 5, "title": "Launch", "body": "Go to market"},
            {"number": 6, "title": "Iterate", "body": "Continuous improvement"},
        ],
    },
    "pyramid_detailed": {
        "tiers": [
            {"label": "Vision", "detail": "Long-term aspiration"},
            {"label": "Strategy", "detail": "3-year growth plan"},
            {"label": "Goals", "detail": "Annual OKRs"},
            {"label": "Tactics", "detail": "Quarterly initiatives"},
            {"label": "Actions", "detail": "Daily execution"},
        ],
    },
    "ladder": {
        "steps": [
            {"label": "Aware", "body": "Brand recognition"},
            {"label": "Engaged", "body": "Content interaction"},
            {"label": "Qualified", "body": "Need identified"},
            {"label": "Evaluating", "body": "Comparing options"},
            {"label": "Committed", "body": "Decision made"},
        ],
    },
    "petal_teardrop": {
        "center": {"title": "Growth", "subtitle": "Framework"},
        "petals": [
            {"title": "Revenue", "value": "+32%"},
            {"title": "Users", "value": "+18%"},
            {"title": "Market", "value": "+12%"},
            {"title": "Product", "value": "+45%"},
            {"title": "Team", "value": "+22%"},
            {"title": "Brand", "value": "+15%"},
        ],
    },
    "funnel_kpi_strip": {
        "stages": [
            {"label": "Leads", "value": "5,000"},
            {"label": "MQL", "value": "1,200"},
            {"label": "SQL", "value": "480"},
            {"label": "Closed", "value": "96"},
        ],
        "kpis": [
            {"metric": "Win Rate", "value": "20%"},
            {"metric": "Avg Deal", "value": "$42K"},
            {"metric": "Cycle Days", "value": "38"},
            {"metric": "Pipeline", "value": "$8.2M"},
        ],
    },
    "persona_dashboard": {
        "name": "Sarah Chen",
        "role": "VP of Engineering",
        "avatar_initial": "S",
        "attributes": [
            {"label": "Team Size", "value": "45"},
            {"label": "Budget", "value": "$2.1M"},
            {"label": "Tenure", "value": "6 yrs"},
            {"label": "NPS", "value": "72"},
            {"label": "Delivery", "value": "94%"},
            {"label": "Attrition", "value": "8%"},
        ],
    },
    "sidebar_profile": {
        "profile": {
            "name": "Marcus Rivera",
            "role": "Product Manager",
            "avatar_initial": "M",
            "tags": ["SaaS", "B2B", "Agile", "Data"],
        },
        "content": {
            "title": "Key Responsibilities",
            "items": [
                "Own product roadmap and prioritization",
                "Align engineering, design, and GTM teams",
                "Define success metrics for each feature",
                "Conduct regular user research sessions",
                "Report OKR progress to executive team",
            ],
        },
    },
    "metaphor_backdrop": {
        "backdrop": "mountain",
        "items": [
            {"title": "Base Camp", "body": "Foundation metrics established"},
            {"title": "Mid Route", "body": "Growth phase milestones"},
            {"title": "Summit", "body": "Vision and long-term goal"},
        ],
    },
    "chart_row": {
        "charts": [
            {
                "chart_type": "donut",
                "title": "Revenue Mix",
                "data": {
                    "segments": [
                        {"label": "SaaS", "value": 55},
                        {"label": "Services", "value": 30},
                        {"label": "Other", "value": 15},
                    ]
                },
            },
            {
                "chart_type": "gauge",
                "title": "NPS Score",
                "data": {"value": 72, "label": "NPS"},
            },
            {
                "chart_type": "waterfall",
                "title": "Revenue Bridge",
                "data": {
                    "items": [
                        {"label": "FY23", "value": 100, "total": True},
                        {"label": "New", "value": 42},
                        {"label": "Churn", "value": -12},
                        {"label": "FY24", "value": 130, "total": True},
                    ]
                },
            },
        ],
    },
}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all() -> tuple[int, int]:
    """Render all 16 infographic types and return (passed, failed)."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Add src/ to path so we can import inkline directly
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    from inkline.typst.chart_renderer import render_chart  # noqa: PLC0415

    passed = 0
    failed = 0

    for chart_type, test_data in TEST_CASES.items():
        out_path = OUT_DIR / f"{chart_type}.png"
        try:
            render_chart(
                chart_type,
                test_data,
                out_path,
                color_mode="palette",
                width=7.5,
                height=4.2,
                dpi=150,
            )
            if not out_path.exists():
                raise FileNotFoundError(f"Output file not created: {out_path}")
            size = out_path.stat().st_size
            if size < 5_000:
                raise ValueError(f"Output file too small ({size} bytes) — likely blank figure")
            print(f"  ✓ {chart_type} ({size // 1024} KB)")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  ✗ {chart_type}: {exc}")
            failed += 1

    print(f"\n{passed}/{passed + failed} passed")
    return passed, failed


# ---------------------------------------------------------------------------
# Pytest entry point
# ---------------------------------------------------------------------------

def test_all_infographic_types():
    """Pytest-compatible test for all 16 infographic types."""
    passed, failed = run_all()
    assert failed == 0, f"{failed} infographic type(s) failed — see stdout for details"


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print(f"Rendering infographics to {OUT_DIR}/\n")
    _, failed = run_all()
    sys.exit(0 if failed == 0 else 1)
