#!/usr/bin/env python3
"""Generate Project Corsair Board DD slide deck from the markdown report.

Uses Inkline's DesignAdvisor (LLM mode) with Aigis brand + dmd_stripe template.
Minimal instruction — lets the advisor pick layouts, charts, and visual hierarchy.
"""

import json
import os
import sys
from pathlib import Path

import requests

# Ensure inkline is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("corsair_gen")

from inkline.intelligence import DesignAdvisor
from inkline.typst import export_typst_slides

# ─── LLM Caller: Claude Max bridge → Anthropic API fallback ──────────────────
BRIDGE_URL = "http://localhost:8082"

def bridge_caller(system_prompt: str, user_prompt: str) -> str:
    """LLM caller: tries Claude Max bridge first, falls back to Anthropic API.

    The bridge has a timeout that can't handle the 85K+ system prompt from
    DesignAdvisor (playbooks + design.md catalog). Falls back to API if needed.
    """
    # Try bridge first (prompt mode, 120s timeout — fast for small prompts)
    try:
        log.info("Trying Claude Max bridge (%d sys, %d user chars)...", len(system_prompt), len(user_prompt))
        resp = requests.post(
            f"{BRIDGE_URL}/prompt",
            json={"prompt": user_prompt, "system": system_prompt, "max_tokens": 16000},
            timeout=180,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("response"):
            log.info("Bridge OK: %d chars (source=%s)", len(data["response"]), data.get("source", "?"))
            return data["response"]
    except Exception as e:
        log.warning("Bridge failed (%s), falling back to Anthropic API...", e)

    # Fallback: Anthropic API
    import anthropic
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("No API key and bridge failed — cannot call LLM")
    client = anthropic.Anthropic(api_key=api_key)
    log.info("Calling Anthropic API (claude-sonnet-4-20250514)...")
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=16000,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )
    text = response.content[0].text
    log.info("API response: %d chars", len(text))
    return text


# Load API key as fallback
if not os.environ.get("ANTHROPIC_API_KEY"):
    for env_path in [Path.home() / ".env", Path("/home/k1mini/copilot/.env")]:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                if line.startswith("ANTHROPIC_API_KEY="):
                    os.environ["ANTHROPIC_API_KEY"] = line.split("=", 1)[1].strip()
                    break
            if os.environ.get("ANTHROPIC_API_KEY"):
                break

# ─── Source ───────────────────────────────────────────────────────────────────
SOURCE = Path("/mnt/nullhypothesis/D/aigis-agents-v2/domain_knowledge/Report_examples/Project_Corsair_Board_DD_Report_28Feb2026.md")
OUTPUT = SOURCE.parent / "Project_Corsair_Board_DD_Slides.pdf"

# ─── Content Sections (structured from the DD report, minimal editorial) ─────
# We provide raw facts. The DesignAdvisor decides how to present them.

sections = [
    # ── Executive Summary ────────────────────────────────────────────────
    {
        "type": "executive_summary",
        "title": "Executive Summary — Project Corsair",
        "narrative": (
            "Proposed acquisition of Byron Energy LLC, a Gulf of America "
            "shallow-water oil and gas company operating three producing platforms "
            "(SM71-F, SM58-G, SM69-E) across four lease blocks offshore Louisiana. "
            "Seller: Byron Energy Limited (formerly ASX: BYE). 100% equity in the "
            "US operating entity."
        ),
        "metrics": {
            "Current net daily production": "~1,354 boepd (65% oil)",
            "2025 LTM net revenue": "~$27.9mm",
            "2025 LTM EBITDAX": "~$15mm",
            "PDP Reserves (net)": "1.78 MMboe / NPV10 $51.4mm",
            "2P Reserves (net)": "12.7 MMboe / NPV10 $231.1mm",
            "Total ARO (P50, gross)": "$13.4mm (low; modern infrastructure)",
            "Remaining debt at close": "Nil",
        },
    },

    # ── Bid Recommendation ───────────────────────────────────────────────
    {
        "type": "recommendation",
        "title": "Board Bid Recommendation",
        "narrative": (
            "PDP PV10 = $51.4mm (GoM bid floor). "
            "Recommended headline bid: $130–145mm (2P CPR × 0.60–0.65×) plus a "
            "$15–25mm CVR tied to SM70 Golden Trout delivery. "
            "Walk-away price: $173mm. "
            "Do NOT bid on Management Case NPV ($433mm) — delta is "
            "almost entirely undrilled PR and unvalidated assumptions."
        ),
        "metrics": {
            "Headline bid range": "$130–145mm",
            "CVR (SM70 contingent)": "$15–25mm",
            "Walk-away ceiling": "$173mm",
            "PDP floor bid": "$72–90mm",
        },
    },

    # ── Asset Portfolio ──────────────────────────────────────────────────
    {
        "type": "asset_overview",
        "title": "Asset Portfolio — Three Producing Platforms",
        "items": [
            {
                "name": "SM71 F Platform (50% WI)",
                "status": "Flagship — 3 producing wells, 6-slot platform",
                "production_2025": "789 boepd gross",
                "reserves_2p": "1.642 MMboe / NPV10 $45.5mm",
                "highlight": "Cumulative net cash flow $130mm since 2018 — paid out in 18 months",
            },
            {
                "name": "SM58 G Platform (100% WI)",
                "status": "High-IP oil — 6 wells active, 3 slots available",
                "production_2025": "977 boepd gross",
                "key_opportunity": "G9 Cutthroat North: 1,200–2,400 bopd IP, NPV10 $166mm",
            },
            {
                "name": "SM69 E Platform (53% WI)",
                "status": "W&T-operated satellite — 2 active wells",
                "production_2025": "389 boepd gross",
            },
            {
                "name": "SM70 (100% WI)",
                "status": "Exploration — PRIMARY TERM expires March 2029",
                "prospect": "Golden Trout: 8,005 Mboe net PR, NPV10 $55.7mm, D&C ~$70.9mm",
            },
        ],
    },

    # ── Production Performance ───────────────────────────────────────────
    {
        "type": "production",
        "title": "2025 Production Performance",
        "table_data": {
            "headers": ["Field", "Oil (MBO)", "Gas (MMCF)", "Total kboe", "Avg boepd"],
            "rows": [
                ["SM71 F", "247.3", "243.2", "287.8", "789"],
                ["SM58 G", "246.2", "663.9", "356.9", "977"],
                ["SM69 E", "134.6", "45.4", "142.2", "389"],
                ["GROSS TOTAL", "628.1", "952.5", "786.9", "2,155"],
                ["Approx NET", "~390", "~670", "~503", "~1,378"],
            ],
        },
        "narrative": (
            "92% average annual uptime. Oil-weighted (65%+). "
            "G6 L2 sand new producer from Jan 2025 at >600 bopd. "
            "F1 well consistently 600–900 bopd for 7 years."
        ),
    },

    # ── Reserve Summary ──────────────────────────────────────────────────
    {
        "type": "reserves",
        "title": "Reserve & Resource Summary (Collarini CPR, Jul 2025)",
        "metrics": {
            "PDP": "1.78 MMboe / NPV10 $51.4mm",
            "PD (PDP+PNP)": "3.2 MMboe / NPV10 $80.2mm",
            "1P Total Proved": "8.2 MMboe / NPV10 $103.6mm",
            "2P (Proved + Probable)": "12.7 MMboe / NPV10 $231.1mm",
            "3P": "18.6 MMboe / NPV10 $381.3mm",
            "Prospective Resources": "30.7 MMboe / NPV10 $504mm",
        },
        "narrative": (
            "Reserve life index: 1P = 16.6 years, 2P = 25.7 years (long-lived). "
            "PDP of $51.4mm is the unconditional floor value — no new wells required. "
            "2P/1P ratio = 1.55× — moderate uplift contingent on $78mm+ CAPEX in 2027."
        ),
    },

    # ── Financial Overview ───────────────────────────────────────────────
    {
        "type": "financials",
        "title": "LTM Financial Overview (Sep 2024 – Aug 2025)",
        "metrics": {
            "Net Production": "504,368 boe (~1,381 boed)",
            "Total Revenue": "$27.9mm ($55.31/boe)",
            "Field Opex": "$9.2mm ($18.33/boe)",
            "Net Operating Margin": "$18.7mm ($37.09/boe)",
            "EBITDAX": "~$15mm (after $3.4mm US G&A)",
        },
        "narrative": (
            "Debt-free at close — STUSCO facility repaid Aug 2025. "
            "Balance sheet liabilities: $23.0mm total (ARO $9.2mm, director loan $3.7mm, trade AP). "
            "Vendor rescheduling tail: ~$4.96mm (~$330k/month through Dec 2026)."
        ),
    },

    # ── Five-Year Projections ────────────────────────────────────────────
    {
        "type": "projections",
        "title": "Five-Year Financial Projections (2P Case)",
        "table_data": {
            "headers": ["Metric", "2026E", "2027E", "2028E", "2029E", "2030E"],
            "rows": [
                ["Production (boed)", "1,238", "3,978", "5,088", "4,316", "5,008"],
                ["Revenue ($mm)", "$26.0", "$70.1", "$102.6", "$92.9", "$102.6"],
                ["EBITDAX ($mm)", "$14.4", "$54.0", "$84.2", "$75.5", "$84.2"],
                ["CAPEX ($mm)", "$6.5", "$78.2", "$32.4", "$2.5", "$31.6"],
                ["FCF ($mm)", "$3.8", "($27.6)", "$48.4", "$69.6", "$49.0"],
                ["Cumulative FCF", "$5.7", "($21.9)", "$26.5", "$96.1", "$145.2"],
            ],
        },
        "narrative": (
            "2027 FCF trough of ($27.6mm) is the key funding gap — "
            "buyer must confirm financing plan at completion. "
            "NPV10 (2P Case, Corporate Model) = $189.8mm."
        ),
    },

    # ── Development CAPEX Programme ──────────────────────────────────────
    {
        "type": "capex_programme",
        "title": "Near-Term Drilling Inventory",
        "items": [
            {"well": "SM58 G9 — Cutthroat North", "timing": "Q1 2026", "cost": "$18.3mm", "ip": "1,200–2,400 bopd", "npv10": "$166mm (PR)"},
            {"well": "SM58 G8 — Steelhead", "timing": "Q2 2026", "cost": "$17.5mm", "ip": "1,200 bopd", "npv10": "$74mm (2P)"},
            {"well": "SM71 F5 — Recompletion", "timing": "Q1 2026", "cost": "$1.25mm", "ip": "300 bopd", "npv10": "$7.5mm"},
            {"well": "SM71 F6 — Grits", "timing": "2026–27", "cost": "$8.0mm", "ip": "660 bopd + 15mmcfgpd", "npv10": "$47mm (PR)"},
            {"well": "SM58 G5ST — Apache Trout", "timing": "2027", "cost": "$15.8mm", "ip": "500 bopd", "npv10": "$19mm (2P)"},
        ],
        "narrative": "Total 2P programme CAPEX (2026–2028): ~$116–120mm gross.",
    },

    # ── SWOT (Strengths & Opportunities) ─────────────────────────────────
    {
        "type": "strengths",
        "title": "Key Strengths",
        "items": [
            "80% drilling success on 14 GoA wells — F1 and F3 ranked #1 and #2 GoA Shelf oil producers",
            "Long-lived 2P reserve base: 25-year reserve life index",
            "Low ARO: $13.4mm gross (100% modern infrastructure, installed 2017–2020)",
            "Debt-free at close — clean balance sheet",
            "Oil-weighted production (65%+) — cash-generative from Day 1",
            "Proprietary RTM seismic: 23 GoA blocks, ~$5–10mm replacement value",
        ],
    },
    {
        "type": "opportunities",
        "title": "Key Opportunities",
        "items": [
            {"name": "G9 Cutthroat North", "value": "NPV10 $166mm", "detail": "Q1 2026, drill-ready, 1,200–2,400 bopd IP"},
            {"name": "G8 Steelhead", "value": "NPV10 $74mm", "detail": "Q2 2026, conditioned on G9 success"},
            {"name": "F6 Grits", "value": "NPV10 $47mm", "detail": "Gas exploration, open platform slot"},
            {"name": "SM70 Golden Trout", "value": "NPV10 $56mm (PR)", "detail": "High-risk/high-reward; 8,005 Mboe net; requires $70mm D&C"},
            {"name": "LOE/boe efficiency", "value": "$18 → $10/boe", "detail": "Drops sharply as production scales from 2027"},
        ],
    },

    # ── Key Risks ────────────────────────────────────────────────────────
    {
        "type": "risks",
        "title": "Key Risks & Weaknesses",
        "items": [
            {"risk": "SM70 primary term expires March 2029", "severity": "Critical", "detail": "Requires $70mm D&C; binary outcome"},
            {"risk": "SM71 Otto Energy JOA consent", "severity": "High", "detail": "50% WI; assignment consent + ROFR risk"},
            {"risk": "2027 FCF trough ($27.6mm)", "severity": "High", "detail": "Buyer must fund CAPEX peak; requires bridge financing"},
            {"risk": "G9 dry hole risk", "severity": "High", "detail": "Single well drives $84mm+ of 2P production ramp"},
            {"risk": "Geographic concentration", "severity": "Medium", "detail": "All platforms within ~15km; hurricane event risk"},
            {"risk": "WTI below $52–55/bbl", "severity": "Medium", "detail": "2P programme becomes uneconomic; hedging needed"},
        ],
    },

    # ── Valuation & Deal Multiples ───────────────────────────────────────
    {
        "type": "valuation",
        "title": "Valuation Framework — GoM Shelf Benchmarks",
        "table_data": {
            "headers": ["Basis", "Multiple", "Implied EV ($mm)"],
            "rows": [
                ["PDP PV10 ($51.4mm)", "0.80–1.10×", "$41–57mm"],
                ["PDP-anchor (+ PNP + G9)", "—", "$72–88mm"],
                ["1P PV10 ($103.6mm)", "0.75–0.95×", "$78–98mm"],
                ["2P CPR PV10 ($231.1mm)", "0.55–0.70×", "$127–162mm"],
                ["2P Corp Model ($189.8mm)", "0.60–0.75×", "$114–142mm"],
            ],
        },
        "narrative": (
            "Recommended bid: $130–145mm headline + $15–25mm CVR for SM70. "
            "Exclusivity target: $135–150mm. Walk-away: $173mm."
        ),
    },

    # ── Management Case vs CPR ───────────────────────────────────────────
    {
        "type": "analysis",
        "title": "Management Case vs CPR — $243mm NPV Gap",
        "metrics": {
            "CPR Case NPV10": "$189.8mm",
            "Management Case NPV10": "$433.2mm",
            "Delta": "+$243.4mm (+128%)",
        },
        "items": [
            {"driver": "SM70 Golden Trout (PR → drilled)", "contribution": "+$100–130mm (41–53%)", "risk": "Undrilled prospect, lease expires 2029"},
            {"driver": "G9/G8 earlier timing & higher IP", "contribution": "+$60–75mm (25–31%)", "risk": "IP rates not independently validated"},
            {"driver": "CAPEX phasing / FCF trough elimination", "contribution": "+$15–25mm (6–10%)", "risk": "Requires 2026 drill feasibility"},
        ],
        "narrative": "Do NOT use MGMT case as bid basis — buyer would be paying full PR value with zero risk premium.",
    },

    # ── VDR Quality & Diligence Gaps ─────────────────────────────────────
    {
        "type": "diligence",
        "title": "VDR Assessment & Critical Diligence Actions",
        "narrative": (
            "VDR rating: GOOD — 1,046 files, well-organised. Independent CPR by Collarini "
            "Associates (234pp). Two model versions available. Full daily production history 2020–2025."
        ),
        "items": [
            {"action": "BD-1: Otto Energy JOA — assignment consent & ROFR", "priority": "Critical", "deadline": "7 days"},
            {"action": "BD-2: SM70 lease — HBP extension options before Mar 2029", "priority": "Critical", "deadline": "7 days"},
            {"action": "BD-3: Vendor rescheduling agreements (35 vendors)", "priority": "Critical", "deadline": "7 days"},
            {"action": "BD-4: STUSCO/Shell marketing agreement", "priority": "Critical", "deadline": "7 days"},
            {"action": "BD-5: G9/G8 APD permits confirmation", "priority": "Critical", "deadline": "7 days"},
            {"action": "BD-6: BOEM bonding analysis on COC", "priority": "High", "deadline": "10 days"},
        ],
    },

    # ── Decommissioning ──────────────────────────────────────────────────
    {
        "type": "decommissioning",
        "title": "Decommissioning & Environmental",
        "metrics": {
            "Total Gross ARO (P50)": "$12.4–13.4mm",
            "Byron Net ARO (P50)": "$10.1–11.1mm",
            "Current bonding": "~$3mm cash collateral",
            "Annual bond premium": "~$354k",
        },
        "narrative": (
            "Exceptionally low ARO for a GoM shelf operator — consequence of focused, "
            "minimal-footprint strategy using recently installed platforms (2017 and 2020). "
            "Zero BSEE/BOEM non-compliance incidents. "
            "Gap: No Phase 1 ESA or environmental screening in VDR."
        ),
    },

    # ── Conclusions & Next Steps ─────────────────────────────────────────
    {
        "type": "conclusions",
        "title": "Conclusions & Board Recommendations",
        "items": [
            "Proceed to exclusivity: headline bid $130–145mm + CVR $15–25mm for SM70",
            "Walk-away at $173mm (2P CPR × 0.75×) — above this, risk-adjusted return is marginal",
            "Do NOT bid on MGMT case ($433mm) — unrisked PR + unvalidated IP assumptions",
            "Prioritise BD-1 to BD-5 immediately (Otto JOA, SM70, vendor agreements, STUSCO, G9 permits)",
            "Structure with management retention as condition — 80% drilling success is team-driven",
            "Pre-arrange bridge financing for 2027 FCF trough ($27.6mm)",
            "Insert price protection: hedging programme at ~$65–70/bbl WTI for 2026–2027",
        ],
    },
]

# ─── Generate ─────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print(f"INKLINE — Project Corsair Board DD Deck Generator")
print(f"{'='*60}")
print(f"  Brand:    aigis")
print(f"  Template: dmd_stripe")
print(f"  Sections: {len(sections)}")
print(f"  Output:   {OUTPUT}")
print(f"{'='*60}\n")

advisor = DesignAdvisor(
    brand="aigis",
    template="dmd_stripe",
    mode="llm",
    llm_caller=bridge_caller,
)

print("Calling DesignAdvisor (LLM mode) — this takes ~30-60s...")
slides = advisor.design_deck(
    title="Project Corsair — Board-Level Due Diligence",
    subtitle="Proposed Acquisition of Byron Energy LLC",
    date="28 February 2026",
    sections=sections,
    audience="Board of Directors / Investment Committee",
    goal="Secure board approval for exclusivity and headline bid of $130–145mm",
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
    title = s.get("data", {}).get("title", s.get("data", {}).get("company", ""))
    print(f"  [{i+1:2d}] {stype:20s} — {title[:60]}")

# Debug: dump slides to JSON for inspection
debug_json = OUTPUT.with_suffix(".slides.json")
with open(debug_json, "w") as f:
    json.dump(slides, f, indent=2, default=str)
print(f"Slides JSON saved to: {debug_json}")

print(f"\nRendering to Typst PDF...")
try:
    pdf_path = export_typst_slides(
        slides=slides,
        output_path=str(OUTPUT),
        brand="aigis",
        template="dmd_stripe",
        title="Project Corsair — Board-Level Due Diligence",
        date="28 February 2026",
        subtitle="Proposed Acquisition of Byron Energy LLC",
    )
    print(f"\n{'='*60}")
    print(f"DONE — PDF: {pdf_path}")
    print(f"{'='*60}")
except Exception as e:
    # Dump the Typst source for debugging
    from inkline.brands import get_brand
    from inkline.typst.theme_registry import brand_to_typst_theme
    from inkline.typst.slide_renderer import TypstSlideRenderer, DeckSpec, SlideSpec

    brand_obj = get_brand("aigis")
    theme = brand_to_typst_theme(brand_obj, "dmd_stripe")
    deck_spec = DeckSpec(
        slides=[SlideSpec(slide_type=s["slide_type"], data=s.get("data", {})) for s in slides],
        title="Project Corsair — Board-Level Due Diligence",
        date="28 February 2026",
        subtitle="Proposed Acquisition of Byron Energy LLC",
    )
    renderer = TypstSlideRenderer(theme)
    source = renderer.render_deck(deck_spec)
    debug_typ = OUTPUT.with_suffix(".debug.typ")
    debug_typ.write_text(source, encoding="utf-8")
    print(f"\nERROR: {e}")
    print(f"Typst source saved to: {debug_typ}")
    raise
