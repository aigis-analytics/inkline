"""Generate Aigis investor deck from markdown via DesignAdvisor.

This script demonstrates the full Inkline pipeline:
1. Parse investor pitch markdown into structured sections
2. Feed to DesignAdvisor for layout decisions
3. Generate Typst slides
4. Compile to PDF

Usage:
    python scripts/gen_aigis_investor_deck.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from inkline.intelligence import DesignAdvisor
from inkline.typst import export_typst_slides

# ---------------------------------------------------------------------------
# Structured content — parsed from aigis-investor-deck-apr2026.md
# Following playbook guidance:
#   - slide_layouts.md: Pyramid Principle (lead with conclusion)
#   - slide_layouts.md: Action titles (not topic titles)
#   - chart_selection.md: Tables for structured comparisons
#   - slide_layouts.md: 3-column cards for triads
#   - slide_layouts.md: KPI strip for 3-5 hero metrics
#   - color_theory.md: Accent for emphasis, muted for supporting
# ---------------------------------------------------------------------------

SECTIONS = [
    # -- PROBLEM (3-card: each pain point gets a card with hero stat) --
    {
        "type": "comparison",
        "section": "The Problem",
        "title": "Upstream DD has a speed, cost and coverage problem",
        "cards": [
            {
                "title": "Compressed bid timelines",
                "body": "4-8 weeks of analyst time per transaction -- compressing bid timelines and stretching teams beyond capacity.",
            },
            {
                "title": "Advisor fees before you've won",
                "body": "USD 200K-2M+ in advisor fees -- before you've won the deal. Capital at risk on every process you enter.",
            },
            {
                "title": "Red flags found post-close",
                "body": "Key red flags buried in VDRs -- found post-close, not pre-sign. The liability was always in the data room.",
            },
        ],
        "footnote": "The bottleneck is human capacity to read, cross-reference, and synthesise under time pressure.",
    },

    # -- WHY NOW (table: market signals with sources) --
    {
        "type": "financial_overview",
        "section": "Why Now",
        "title": "The market inflection point is here",
        "table_data": {
            "headers": ["Signal", "Data Point", "Source"],
            "rows": [
                ["AI adoption in M&A", "86% of leaders now use GenAI", "Deloitte 2025"],
                ["US upstream M&A volume", "USD 65 billion (2025)", "Enverus"],
                ["Cost reduction from GenAI", "~20% average", "McKinsey"],
                ["Investment in AI for M&A", "83% invested USD 1M+", "Deloitte 2025"],
            ],
        },
        "footnote": "AI capability + market readiness + zero competing product = first-mover window.",
    },

    # -- SOLUTION (split: 3-step pipeline left, cost comparison right) --
    {
        "type": "comparison",
        "section": "The Solution",
        "title": "Aigis: upstream DD intelligence built from first principles",
        "cards": [
            {
                "title": "1. Ingest",
                "body": "Reads every PDF, Excel, DOCX, CSV. Classifies against 87-item upstream DD checklist. Identifies data gaps automatically.",
            },
            {
                "title": "2. Analyse",
                "body": "13 sequential AI analysis calls, each focused on a single DD discipline. Every finding cited to source document and page.",
            },
            {
                "title": "3. Deliver",
                "body": "15-section board-level DD report. Deterministically verified. Interactive dashboard. Financial model stress-testing.",
            },
        ],
        "footnote": "Cost per full synthesis: ~USD 50-100 vs USD 200K+ traditional advisory fees.",
    },

    # -- REPORT COVERAGE (table) --
    {
        "type": "financial_overview",
        "section": "Report Coverage",
        "title": "15 sections. Every material DD question answered.",
        "table_data": {
            "headers": ["#", "Section", "Coverage"],
            "rows": [
                ["1", "Executive Summary", "Headline metrics, PROCEED/CAUTION/DNP, bid range"],
                ["2-3", "Transaction + Assets", "Entity structure, per-field WI%, reserves, well inventory"],
                ["4-6", "VDR + Reserves + Production", "Data room rating, 1P/2P/3P, DCA, water cut trends"],
                ["7-8", "Financials + CAPEX", "LTM P&L, cash flow, LOE benchmarking, seller model audit"],
                ["9-10", "Regulatory + SWOT", "Permits, BSEE/BOEM INCs, environmental liability"],
                ["11-13", "Valuation + Decom + People", "NPV10, bid range, P50/P90 ABEX, key person risk"],
                ["14-15", "Actions + Conclusions", "Pre-sign DD checklist, board recommendation"],
            ],
        },
    },

    # -- PROOF POINTS (stat slide: hero metrics) --
    {
        "type": "kpi_dashboard",
        "section": "Live Proof Points",
        "title": "Tested on real transaction VDRs",
        "metrics": {
            "Deals Processed": "7+",
            "MARKO Verified": "93%",
            "End-to-End": "30min",
        },
    },

    # -- TECH DIFFERENTIATORS (4-card) --
    {
        "type": "comparison",
        "section": "Technology",
        "title": "This is not ChatGPT on documents",
        "cards": [
            {
                "title": "MARKO Verification",
                "body": "93% of quantitative claims deterministically verified against the financial model database.",
            },
            {
                "title": "4-Tier Vishwakarma",
                "body": "Regex - Fuzzy - Haiku - Sonnet. Deterministic speed with LLM intelligence. Never fails silently.",
            },
            {
                "title": "Kambr Model Builder",
                "body": "Generates jurisdiction-aware Excel models (6 fiscal regimes). xlwings COM, self-auditing.",
            },
            {
                "title": "Cross-Deal Learning",
                "body": "Archon engine detects patterns across deals. Learns from every pipeline run.",
            },
        ],
    },

    # -- COMPETITIVE LANDSCAPE (split) --
    {
        "type": "positioning",
        "section": "Competitive Landscape",
        "title": "No competitor combines AI-native DD with deep O&G expertise",
        "left": {
            "title": "The Market Today",
            "items": [
                "VDR platforms host docs but don't analyse them",
                "Data providers give reference data, not VDR processing",
                "Generic AI has no domain playbooks or verification",
                "Legal AI covers contracts only, not upstream DD",
                "Advisory firms are deep but manual, slow, USD 200K+",
            ],
        },
        "right": {
            "title": "Aigis Advantage",
            "items": [
                "AI-native + deep domain expertise",
                "VDR to Report to Dashboard to Buyer Case",
                "13 specialist playbooks, not generic prompts",
                "Deterministic verification (MARKO)",
                "USD 50-100 per full synthesis",
            ],
        },
    },

    # -- MARKET OPPORTUNITY (stat: TAM/SAM/SOM) --
    {
        "type": "kpi_dashboard",
        "section": "Market Opportunity",
        "title": "Large addressable market with clear entry point",
        "metrics": {
            "TAM": "USD 12B+",
            "SAM": "USD 3.2B",
            "SOM (Yr 3)": "USD 15-30M",
        },
    },

    # -- BUSINESS MODEL (table) --
    {
        "type": "financial_overview",
        "section": "Business Model",
        "title": "98% gross margin at scale with multiple revenue streams",
        "table_data": {
            "headers": ["Model", "Price", "Margin"],
            "rows": [
                ["Enterprise SaaS (annual)", "GBP 60K-150K per seat", ">95%"],
                ["Transaction fee (per VDR)", "GBP 5K-15K per analysis", ">98%"],
                ["Workstream add-ons", "GBP 2K-5K each", ">95%"],
                ["API cost (full synthesis)", "~GBP 40-80", "--"],
            ],
        },
        "footnote": "At GBP 5K/VDR with ~GBP 80 API cost, gross margin exceeds 98%.",
    },

    # -- TRACTION (table) --
    {
        "type": "financial_overview",
        "section": "Traction",
        "title": "From concept to validated pipeline in 6 months",
        "table_data": {
            "headers": ["Date", "Milestone"],
            "rows": [
                ["Oct 2025", "Concept and architecture design"],
                ["Feb 2026", "MVP -- first VDR processed end-to-end"],
                ["Mar 2026", "MARKO verification engine -- 93% claim verification"],
                ["Mar 2026", "Company incorporated (Aigis Analytics Pty Ltd)"],
                ["Apr 2026", "Kambr corporate model builder -- 6 jurisdictions"],
                ["Apr 2026", "Full synthesis validated (Corsair -- 34/35 sections)"],
            ],
        },
    },

    # -- FINANCIAL PROJECTIONS (table) --
    {
        "type": "financial_overview",
        "section": "Financials",
        "title": "Path to profitability with 5 enterprise customers",
        "table_data": {
            "headers": ["Metric", "Year 1", "Year 2", "Year 3"],
            "rows": [
                ["Customers", "5-10", "25-50", "100+"],
                ["ARR", "GBP 300K-600K", "GBP 1.5M-3M", "GBP 6M-15M"],
                ["Gross Margin", ">95%", ">95%", ">95%"],
                ["Team Size", "3-5", "8-12", "15-25"],
            ],
        },
    },

    # -- THE ASK (split: use of funds + what we offer) --
    {
        "type": "comparison",
        "section": "The Ask",
        "title": "Seeking GBP 150K-250K pre-seed",
        "left": {
            "title": "Use of Funds",
            "items": [
                "Product completion & hardening (40%)",
                "First 3 enterprise customer acquisitions (30%)",
                "Legal, IP, and compliance (15%)",
                "Infrastructure & operations (15%)",
            ],
        },
        "right": {
            "title": "What We Offer",
            "items": [
                "Equity participation (structure TBD)",
                "Board observer seat",
                "Co-authorship of first published case studies",
                "Preferred commercial terms at launch",
            ],
        },
    },
]


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate Aigis investor deck")
    parser.add_argument("--mode", default="llm", choices=["llm", "rules", "advised"],
                        help="Design mode: llm (default), rules (fallback), advised")
    parser.add_argument("--model", default="claude-sonnet-4-20250514",
                        help="Model for LLM mode")
    args = parser.parse_args()

    # Initialize DesignAdvisor — LLM mode is now the default
    advisor = DesignAdvisor(
        brand="aigis",
        template="consulting",
        mode=args.mode,
        model=args.model,
    )

    # Design the deck
    slides = advisor.design_deck(
        title="Aigis Analytics",
        sections=SECTIONS,
        date="April 2026",
        subtitle="AI-Powered Due Diligence for Upstream Oil & Gas M&A",
        audience="PE fund CIOs, energy sector investors, potential design partners",
        goal="Secure GBP 150K-250K pre-seed investment for an AI-powered upstream O&G due diligence platform",
        contact={
            "name": "Aaditya Chintalapati",
            "role": "Founder & CEO, CFA",
            "email": "aaditya@aigis-analytics.com",
            "company": "Aigis Analytics",
            "tagline": "Domain Intelligence, Deal Certainty",
        },
    )

    # Print planned slides
    print(f"DesignAdvisor planned {len(slides)} slides:\n")
    for i, s in enumerate(slides):
        t = s["data"].get("title", s["data"].get("company", ""))
        print(f"  {i+1:2d}. [{s['slide_type']:12s}] {t}")

    # Save the slide specs as JSON (for reuse / debugging)
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "aigis_investor_deck.json"
    json_path.write_text(json.dumps(slides, indent=2, default=str), encoding="utf-8")
    print(f"\nSlide specs saved: {json_path}")

    # Export to PDF
    output_path = output_dir / "aigis_investor_deck.pdf"
    result = export_typst_slides(
        slides=slides,
        output_path=str(output_path),
        brand="aigis",
        template="consulting",
        title="Aigis Analytics",
        date="April 2026",
    )

    print(f"PDF generated: {result} ({output_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
