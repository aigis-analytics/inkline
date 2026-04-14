"""
Project Corsair — Board Investment Memorandum
Inkline deck generation script (aigis brand, consulting template)

Run from the inkline repo root:
    python corsair_board_deck.py
"""
from __future__ import annotations
import logging
import sys
from pathlib import Path

# Make sure we can import from the repo
sys.path.insert(0, str(Path(__file__).parent / "src"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)

OUTPUT_PATH = Path.home() / ".local/share/inkline/output/corsair_board_dd.pdf"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Slide definitions
# ---------------------------------------------------------------------------

slides = [

    # ── 1. Title ──────────────────────────────────────────────────────────
    {
        "slide_type": "title",
        "data": {
            "company":   "Aigis Analytics",
            "title":     "Project Corsair",
            "subtitle":  "Board Investment Memorandum — Byron Energy LLC Acquisition",
            "date":      "April 2026",
            "presenter": "Aigis Due Diligence",
            "confidentiality": "STRICTLY PRIVATE & CONFIDENTIAL",
        },
    },

    # ── 2. Section divider: Executive Summary ─────────────────────────────
    {
        "slide_type": "section_divider",
        "data": {
            "section": "01",
            "title":   "Executive Summary",
            "subtitle": "Deal overview, headline metrics, and board recommendation",
        },
    },

    # ── 3. Deal Snapshot ─────────────────────────────────────────────────
    {
        "slide_type": "three_card",
        "data": {
            "section": "Executive Summary",
            "title": "Project Corsair: Deal at a Glance",
            "cards": [
                {
                    "icon": "🏗️",
                    "headline": "100% Byron Energy LLC",
                    "body": "Delaware entity acquisition (MIPA). Holds 4 GoM shallow-water lease blocks via wholly-owned BOEM-qualified subsidiary. Zero drawn debt at close.",
                },
                {
                    "icon": "🛢️",
                    "headline": "1,354 boepd Net Production",
                    "body": "65% oil-weighted. SM73 salt dome, ~70 mi offshore Louisiana. Three manned platforms. 80% historical drilling success rate (14 wells).",
                },
                {
                    "icon": "📐",
                    "headline": "12.7 MMboe 2P Reserves",
                    "body": "25-year 2P reserve life. Collarini CPR effective Jul 2025. 2P CPR NPV10: $231.1mm. Near-term 2-well programme: G9 + G8 (1Q/2Q 2026).",
                },
            ],
            "footnote": "Source: Byron IM, Collarini CPR Jul-25, Corporate Model vF. All figures net to Byron WI. Seller figures.",
        },
    },

    # ── 4. Headline KPIs ─────────────────────────────────────────────────
    {
        "slide_type": "kpi_strip",
        "data": {
            "section": "Executive Summary",
            "title": "Headline Metrics — Project Corsair",
            "kpis": [
                {"label": "Net Production",      "value": "1,354",  "unit": "boepd", "delta": "65% oil"},
                {"label": "LTM Net Revenue",     "value": "$29mm",  "unit": "LTM Jun-25", "delta": "Seller figure"},
                {"label": "LTM EBITDAX",         "value": "$15mm",  "unit": "~52% margin", "delta": "Seller figure"},
                {"label": "LOE / boe",           "value": "$19.03", "unit": "/boe", "delta": "Above $12–18 bench."},
                {"label": "2P Reserves (Net)",   "value": "12.7",   "unit": "MMboe", "delta": "25-yr RLI"},
                {"label": "2P CPR NPV10",        "value": "$231mm", "unit": "Collarini CPR", "delta": "Jul-25 effective"},
                {"label": "PDP NPV10",           "value": "$51.4mm","unit": "Floor value", "delta": "Proven base"},
                {"label": "Total ARO (Gross)",   "value": "$13.4mm","unit": "P50 estimate", "delta": "Low for GoM shelf"},
            ],
            "footnote": "Source: Byron IM p.5, Collarini CPR Jul-25. All figures net to Byron WI unless stated. Seller figures (a).",
        },
    },

    # ── 5. Board Recommendation ───────────────────────────────────────────
    {
        "slide_type": "comparison",
        "data": {
            "section": "Executive Summary",
            "title": "Board Recommendation: ⚠️ Proceed with Caution",
            "left_label":  "RECOMMENDED BID",
            "right_label": "WALK-AWAY CEILING",
            "left_items": [
                "Headline bid: $130–145mm",
                "Basis: 2P CPR NPV10 $231.1mm × 0.56–0.63×",
                "Includes risked credit for G9 + G8 near-term wells",
                "Excludes SM70 Golden Trout prospective resources",
                "CVR: +$15–25mm contingent on SM70 H1 first production",
                "Implied 3.0–3.3× return vs. management case NPV10 $433mm",
            ],
            "right_items": [
                "Ceiling: $160mm (hard walk-away)",
                "Basis: 2P Corporate Model NPV10 $189.8mm × 0.84×",
                "Beyond $160mm: returns marginal given elevated LOE",
                "Negative FCF in 2027 (peak CAPEX −$27.8mm) — cash call risk",
                "G9 execution risk: ~80% success rate, $18.3mm D&C",
                "JOA gap: Otto Energy ROFR at SM71 unconfirmed",
            ],
            "footnote": "Bid range per Aigis GoM convention methodology. All NPV10 at 10% discount rate, NYMEX strip Jul-25. Seller figures (a); Aigis derivations (c).",
        },
    },

    # ── 6. Section divider: Asset Portfolio ───────────────────────────────
    {
        "slide_type": "section_divider",
        "data": {
            "section": "02",
            "title":   "Asset Portfolio",
            "subtitle": "Four GoM shallow-water blocks, SM73 salt dome structure",
        },
    },

    # ── 7. Asset Portfolio — Four Blocks ─────────────────────────────────
    {
        "slide_type": "four_card",
        "data": {
            "section": "Asset Portfolio",
            "title": "Four Producing Blocks — SM73 Salt Dome Cluster",
            "cards": [
                {
                    "label":   "SM71 (F Platform)",
                    "value":   "50% WI",
                    "detail":  "Byron operator. 6 slots (1 open for F6). 3 active producers (F1, F2, F4). F1 = #1 oil well GoM shelf since 2018. $130mm cumulative net cash flow. Co-owner: Otto Energy (50%). 1P NPV10 $29.4mm | 2P NPV10 $45.5mm",
                },
                {
                    "label":   "SM58 (G Platform)",
                    "value":   "100% WI",
                    "detail":  "Byron operator. 9 slots (3 open). 3 active producers (G1BP1, G4, G6BP1). Primary driver of 2P/management case value. G9 Cutthroat North PR NPV10 $166mm unrisked. 2P NPV10 $55.8mm",
                },
                {
                    "label":   "SM69/58 (E Platform)",
                    "value":   "53–70% WI",
                    "detail":  "W&T Offshore operator (E1). Byron operator (E2, 70% WI). 2 active producers (E1, E2). 2P NPV10 $18.4mm. W&T consent required for change of control at SM69.",
                },
                {
                    "label":   "SM70 (Exploration)",
                    "value":   "100% WI",
                    "detail":  "Byron operator. Primary term — expires March 2029. Golden Trout prospect: PR NPV10 $55.7mm unrisked, D&C $70.9mm gross (facility + pipeline). Must drill or HBP before Mar 2029 or lease expires.",
                },
            ],
            "footnote": "Source: Byron IM p.21–26, Collarini CPR Jul-25. WI = Working Interest. NPV10 figures net to Byron WI. Seller figures (a).",
        },
    },

    # ── 8. Production & Infrastructure ───────────────────────────────────
    {
        "slide_type": "split",
        "data": {
            "section": "Asset Portfolio",
            "title": "Production Base & Infrastructure Strengths",
            "left": {
                "heading": "Current Production (Sep 2025)",
                "items": [
                    "SM71 F Platform: ~314 boepd net (3 active producers)",
                    "SM58 G Platform: ~643 boepd net (G1BP1, G4, G6BP1)",
                    "SM69 E Platform: ~397 boepd net (E1 + E2)",
                    "Total: 1,354 boepd net | 65% oil | 35% gas",
                    "Platform uptime: 92% average annual",
                    "SM58 depth split: Shell 50% WI below 13,639 ft",
                ],
            },
            "right": {
                "heading": "Infrastructure & Clean Entity Advantages",
                "items": [
                    "Entity acquisition: BOEM bonds + qualifications in place ($10mm)",
                    "Shell STUSCO marketing facility: zero drawn principal at close",
                    "Director/SH loan ($3.67mm) + vendor rescheduling ($4.96mm) repaid from proceeds",
                    "Australian parent G&A eliminated end-2025 (~G&A drops $5.1mm→$3.4mm/yr)",
                    "Proprietary RTM seismic coverage across portfolio",
                    "80% historical drilling success rate (14 wells)",
                ],
            },
            "footnote": "Source: Byron IM p.5, p.17–18, p.22. Management Presentation p.17. Seller figures (a); derived figures (c).",
        },
    },

    # ── 9. Section divider: Reserves ─────────────────────────────────────
    {
        "slide_type": "section_divider",
        "data": {
            "section": "03",
            "title":   "Reserves & Resources",
            "subtitle": "Collarini & Associates CPR — effective 1 July 2025",
        },
    },

    # ── 10. Reserves Summary Chart ────────────────────────────────────────
    {
        "slide_type": "chart_caption",
        "data": {
            "section": "Reserves & Resources",
            "title": "Reserves Ladder — CPR Net to Byron WI",
            "image_path": "corsair_reserves_chart.png",
            "chart_request": {
                "chart_type": "grouped_bar",
                "chart_data": {
                    "title": "Net Reserves & Resources (MMboe) — Collarini CPR Jul-25",
                    "x_label": "",
                    "y_label": "MMboe (Net to Byron WI)",
                    "categories": ["PDP", "1P Total", "2P Total", "3P Total", "Prospective (PR)"],
                    "series": [
                        {
                            "name": "Net Reserves / Resources (MMboe)",
                            "values": [1.78, 8.20, 12.70, 18.60, 30.70],
                        }
                    ],
                },
            },
            "caption": "2P reserves of 12.7 MMboe represent a 25-year reserve life index at current production. PDP covers only 14% of 2P — value is heavily weighted to undeveloped and near-term drilling.",
            "footnote": "Source: Collarini CPR effective 1 Jul 2025. Net to Byron WI. Seller figures (a). CPR update to within 6 months of close should be requested.",
        },
    },

    # ── 11. Reserves by Asset ─────────────────────────────────────────────
    {
        "slide_type": "table",
        "data": {
            "section": "Reserves & Resources",
            "title": "Reserve Summary by Category — Collarini CPR (Jul 2025)",
            "headers": ["Category", "Net MMboe", "NPV10 ($mm)", "Notes"],
            "rows": [
                ["PDP",               "1.78",  "$51.4mm",  "Producing wells — low risk baseline"],
                ["PNP / PDBP",        "1.17",  "$28.8mm",  "Behind-pipe; workover required"],
                ["PUD (Proved)",       "5.86",  "$41.2mm",  "Near-term drilling required — G7, G5ST"],
                ["Total 1P",          "8.20",  "$103.6mm", "Proved reserves — CCA certified"],
                ["Probable (2P incr.)","4.50",  "$127.5mm", "G8 Steelhead + SM69 E wells"],
                ["Total 2P",         "12.70",  "$231.1mm", "PRIMARY VALUATION BASIS"],
                ["Possible (3P incr.)","5.90",  "$149.9mm", "Additional upside probability"],
                ["Total 3P",         "18.60",  "$381mm",   ""],
                ["Prospective (PR)", "30.70",  "$504mm",   "Unrisked — G9 Cutthroat North + SM70"],
            ],
            "highlight_rows": [5],  # Highlight 2P row (0-indexed)
            "footnote": "Source: Collarini CPR Jul-25. Net to Byron WI. Gas converted at 6 mcf = 1 boe. ⚠️ CPR effective date 9 months prior to expected close — update to within 6 months should be requested. Seller figures (a); derived (c).",
        },
    },

    # ── 12. Section divider: Financial Analysis ───────────────────────────
    {
        "slide_type": "section_divider",
        "data": {
            "section": "04",
            "title":   "Financial Analysis",
            "subtitle": "2P Case corporate model, FCF profile, and valuation",
        },
    },

    # ── 13. FCF Profile Chart ─────────────────────────────────────────────
    {
        "slide_type": "chart_caption",
        "data": {
            "section": "Financial Analysis",
            "title": "2P Case Free Cash Flow Profile — Net to Byron WI",
            "image_path": "corsair_fcf_chart.png",
            "chart_request": {
                "chart_type": "waterfall",
                "chart_data": {
                    "title": "Annual FCF Pre-Tax ($mm) — 2P Corporate Model vF",
                    "x_label": "Year",
                    "y_label": "FCF ($mm)",
                    "categories": ["2025", "2026", "2027", "2028", "2029", "2030", "2031", "2032", "2033", "2034", "2035"],
                    "values":     [2.6,    3.6,   -27.8,  48.4,   69.6,   49.0,   68.4,   44.4,   40.3,   21.9,   6.2],
                    "cumulative_label": "Cumulative FCF",
                    "cumulative_values": [2.6, 6.2, -21.6, 26.8, 96.4, 145.4, 213.8, 258.2, 298.5, 320.4, 326.6],
                },
            },
            "caption": "2027 peak CAPEX year: −$27.8mm FCF (G9 + G8 drilling). Cumulative FCF turns positive in 2028 at $26.8mm. Total 11-year undiscounted FCF: ~$327mm.",
            "footnote": "Source: Agent 02 DB, Corporate Model vF, 2P Case. Net to Byron WI. Gas deck: $3.19→$4.00/mmbtu. Oil deck not confirmed — request from seller. Seller figures (a).",
        },
    },

    # ── 14. Financial Projections Table ───────────────────────────────────
    {
        "slide_type": "table",
        "data": {
            "section": "Financial Analysis",
            "title": "2P Case — Key Financial Projections (Net to Byron WI)",
            "headers": ["Year", "Revenue ($mm)", "LOE ($mm)", "G&A ($mm)", "FCF Pre-Tax ($mm)", "Cumul. FCF ($mm)"],
            "rows": [
                ["2025", "$8.8",   "$8.9",  "$5.1", "$2.6",    "$2.6"],
                ["2026", "$26.0",  "$9.2",  "$3.4", "$3.6",    "$6.2"],
                ["2027", "$70.1",  "$9.6",  "$3.4", "–$27.8 ⚠️", "–$21.6"],
                ["2028", "$102.6", "$9.8",  "$3.4", "$48.4",   "$26.8"],
                ["2029", "$92.9",  "$9.7",  "$3.4", "$69.6",   "$96.4"],
                ["2030", "$102.6", "$9.8",  "$3.5", "$49.0",   "$145.4"],
                ["2031–35", "Declining", "$9–8", "$3.5", "$181mm total", "$326.6"],
            ],
            "footnote": "⚠️ 2027 negative FCF reflects peak G9/G8 CAPEX (~$35–36mm gross). G&A decline reflects elimination of Australian parent overhead (end-2025). Oil price deck not confirmed — data gap, request from seller. Source: Agent 02 DB, 2P Case. Seller figures (a).",
        },
    },

    # ── 15. Section divider: Valuation ────────────────────────────────────
    {
        "slide_type": "section_divider",
        "data": {
            "section": "05",
            "title":   "Valuation & Bid Strategy",
            "subtitle": "NPV10 waterfall, bid range derivation, and deal metrics",
        },
    },

    # ── 16. Valuation Waterfall / NPV Comparison ──────────────────────────
    {
        "slide_type": "chart_caption",
        "data": {
            "section": "Valuation & Bid Strategy",
            "title": "NPV10 Scenarios vs. Recommended Bid Range",
            "image_path": "corsair_valuation_chart.png",
            "chart_request": {
                "chart_type": "grouped_bar",
                "chart_data": {
                    "title": "NPV10 Scenarios vs. Bid Range ($mm)",
                    "x_label": "",
                    "y_label": "Value ($mm)",
                    "categories": [
                        "PDP NPV10\n(Floor)",
                        "1P NPV10",
                        "2P CPR\nNPV10",
                        "Bid Floor\n$130mm",
                        "Bid Ceiling\n$145mm",
                        "Walk-Away\n$160mm",
                        "2P Corp.\nModel",
                        "Mgmt Case\nNPV10",
                    ],
                    "series": [
                        {
                            "name": "NPV10 / Bid ($mm)",
                            "values": [51.4, 103.6, 231.1, 130, 145, 160, 189.8, 433.2],
                        }
                    ],
                },
            },
            "caption": "Recommended bid of $130–145mm = 56–63% of 2P CPR NPV10 ($231.1mm). Walk-away ceiling of $160mm = 84% of 2P Corporate Model ($189.8mm). Management case ($433mm) includes undrilled prospective resources — not priced into base bid.",
            "footnote": "Source: Collarini CPR Jul-25, Corporate Model vF & vMGMT_CASE. NYMEX strip Jul-25. Aigis bid convention methodology. Seller figures (a); Aigis derivations (c).",
        },
    },

    # ── 17. Bid Range Derivation ───────────────────────────────────────────
    {
        "slide_type": "table",
        "data": {
            "section": "Valuation & Bid Strategy",
            "title": "Bid Range Derivation — GoM Shelf Convention",
            "headers": ["Component", "Basis", "Value ($mm)"],
            "rows": [
                ["PDP NPV10 anchor",          "Collarini CPR, Jul-25",                  "$51.4mm"],
                ["PDP adjustment (×0.80–1.05)", "GoM shelf: low ARO, oil-weighted",     "$41–54mm"],
                ["G9 risked (50% × 50% risk)",  "PR NPV10 $166.3mm × 50% × 50%",       "+$41.6mm"],
                ["G8 risked (50% × 50% risk)",  "PR NPV10 $96.1mm × 50% × 50%",        "+$24.0mm"],
                ["ARO haircut",                  "Net P50 ARO ~$9.9mm @ 10%",           "−$9.9mm"],
                ["Strategic premium",            "Operator + RTM seismic + 3 platforms", "+$10–15mm"],
                ["RECOMMENDED BID",              "Sum of above",                         "$130–145mm"],
                ["CVR — SM70 Golden Trout",      "PR NPV10 $55.7mm × 0.27–0.45× risked","+$15–25mm contingent"],
                ["Walk-away ceiling",            "2P Corp. Model $189.8mm × 0.84×",      "$160mm"],
            ],
            "highlight_rows": [6],
            "footnote": "EV/2P NPV10 implied: 0.56–0.63× (GoM shelf range 0.35–0.55×; upper end justified by low ARO + near-term wells). EV/boed ~$96k–$107k — elevated due to reserve upside; 2P NPV10 is the primary metric. Source: Aigis GoM bid methodology (m).",
        },
    },

    # ── 18. Section divider: Upsides & Drilling ────────────────────────────
    {
        "slide_type": "section_divider",
        "data": {
            "section": "06",
            "title":   "Upsides & Drilling Inventory",
            "subtitle": "Near-term high-impact wells and management case upside",
        },
    },

    # ── 19. Top Upsides / Drilling Inventory ─────────────────────────────
    {
        "slide_type": "three_card",
        "data": {
            "section": "Upsides & Drilling Inventory",
            "title": "Top Upsides — Near-Term Value Catalysts",
            "cards": [
                {
                    "icon": "🟢",
                    "headline": "G9 Cutthroat North (1Q 2026)",
                    "body": "SM58, 100% WI. PR reserves: 6,417 Mboe net. Unrisked NPV10: $166.3mm. D&C cost: $18.33mm. Expected IP: 1,200–2,400 bopd gross. Proprietary RTM seismic coverage. 80% historical success rate. Success re-rates asset significantly.",
                },
                {
                    "icon": "🟢",
                    "headline": "G8 Steelhead + 8-Well Programme",
                    "body": "G8 (2Q 2026): 2P 2,452 Mboe net, D&C $17.5mm. Full 8-well programme (G9, G8, G5ST, F6, G7, E3, F5STBP, SM70 H1) drives Management Case NPV10 $433mm — $243mm premium over 2P model. 3.0–3.3× return on $130–145mm entry.",
                },
                {
                    "icon": "🟢",
                    "headline": "Clean Balance Sheet & Eliminated G&A",
                    "body": "Zero debt at close. All legacy liabilities (director loans $3.67mm + vendor rescheduling $4.96mm) repaid from proceeds. Australian parent G&A eliminated end-2025 (saves ~$1.7mm/yr). BOEM bonds ($10mm) in place — no new bonding cost.",
                },
            ],
            "footnote": "Source: Management Presentation p.33–35, Collarini CPR Jul-25, IM p.17. Seller figures (a). Unrisked NPV10 figures are prospective resources — not priced into base bid.",
        },
    },

    # ── 20. Drilling Inventory Details ────────────────────────────────────
    {
        "slide_type": "table",
        "data": {
            "section": "Upsides & Drilling Inventory",
            "title": "Near-Term Drilling Inventory — 8-Well Programme",
            "headers": ["Well", "Block", "Byron WI", "Category", "Net Reserves (Mboe)", "NPV10 ($mm)", "D&C ($mm gross)", "Timing"],
            "rows": [
                ["G9 Cutthroat North", "SM58", "100%", "PR",   "6,417", "$166.3mm unrisked", "$18.33mm", "1Q 2026"],
                ["G8 Steelhead",       "SM58", "100%", "2P/PR","2,452", "$96.1mm",           "$17.5mm",  "2Q 2026"],
                ["G5ST Apache Trout",  "SM58", "100%", "1P",   "785",   "—",                 "$15.8mm",  "2027"],
                ["G7 Greenback",       "SM58", "100%", "2P",   "2,355", "—",                 "$14.4mm",  "2027–28"],
                ["F6 Grits",           "SM71", "50%",  "PR",   "3,084", "$46.84mm unrisked", "$8.2mm net","2027"],
                ["F5STBP I3 Recomp.",  "SM71", "50%",  "PDBP", "195",   "$7.5mm",            "$1.25mm net","2026"],
                ["E3 workover",        "SM69", "53–70%","2P",  "TBC",   "—",                 "TBC",      "2027"],
                ["SM70 H1 Golden Trout","SM70","100%", "PR",   "TBC",   "$55.7mm unrisked",  "$70.9mm",  "Pre-Mar 2029"],
            ],
            "footnote": "⚠️ SM70 primary term expires March 2029 — well or HBP activity required to hold lease. F6 subject to Otto Energy JOA review (SM71 co-owner). D&C costs are gross; net to Byron WI = WI% × gross. Source: Management Presentation p.33. Seller figures (a).",
        },
    },

    # ── 21. Section divider: Risks ────────────────────────────────────────
    {
        "slide_type": "section_divider",
        "data": {
            "section": "07",
            "title":   "Key Risks & Diligence Gaps",
            "subtitle": "Critical pre-sign items and risk mitigation framework",
        },
    },

    # ── 22. Top Risks ─────────────────────────────────────────────────────
    {
        "slide_type": "three_card",
        "data": {
            "section": "Key Risks & Diligence Gaps",
            "title": "Top Three Risks — Board-Level Attention Required",
            "cards": [
                {
                    "icon": "🔴",
                    "headline": "CRITICAL: JOA Missing — Otto Energy ROFR",
                    "body": "JOAs for SM71/SM58/69/70 absent from VDR. Otto Energy (50% WI, SM71) may hold ROFR triggered by entity-level transfer. If exercised: lose SM71 (1.079 MMboe 1P, $29.4mm NPV10) and F6 Grits prospect ($46.8mm NPV10). Single most critical pre-sign item.",
                },
                {
                    "icon": "🔴",
                    "headline": "CRITICAL: LOE $19.03/boe Above Benchmark; No US Audited Financials",
                    "body": "LOE $19.03/boe exceeds GoM shelf benchmark $12–18/boe. Thin EBITDAX margin at current production (~52%). Byron Energy LLC and Inc. have no standalone audited financials — only consolidated Australian parent. Cannot independently verify LTM unit economics.",
                },
                {
                    "icon": "🟠",
                    "headline": "HIGH: Management Case Relies on Undrilled Resources; SM70 Lease Expiry",
                    "body": "Management Case NPV10 $433mm includes undrilled SM70 ($70.9mm gross D&C) and SM58 prospective wells — these are unrisked and must NOT be priced into base bid. SM70 primary term expires March 2029. If no well drilled, Golden Trout prospect is lost.",
                },
            ],
            "footnote": "Source: VDR Gap Analysis, Byron IM, Collarini CPR Jul-25. See Section 7 of full DD report for complete risk register. Aigis risk assessment (c).",
        },
    },

    # ── 23. Critical Diligence Gaps ───────────────────────────────────────
    {
        "slide_type": "table",
        "data": {
            "section": "Key Risks & Diligence Gaps",
            "title": "Critical Diligence Gaps — Pre-Sign Requirements",
            "headers": ["Gap", "Severity", "Impact if Unresolved", "Action Required"],
            "rows": [
                ["JOAs (SM71/58/69/70)", "🔴 Critical", "Otto/W&T ROFR could remove SM71 (up to −$45.5mm 2P NPV10)", "Obtain all JOAs; confirm no ROFR/CoC triggered by entity transfer"],
                ["MIPA — full R&W review", "🔴 Critical", "Reps, warranties, indemnities, price adjustments unconfirmed", "Request near-final MIPA for full legal review before binding bid"],
                ["US subsidiary standalone financials", "🔴 Critical", "Cannot verify LTM LOE/boe or EBITDAX independently", "Request Byron Energy LLC + Inc. standalone audited accounts"],
                ["Phase I/II environmental assessments", "🔴 Critical", "Standard for US offshore — absence is a red flag", "Require Phase I (and Phase II if warranted) before close"],
                ["ARO balance sheet provision/actuarial", "🟠 High", "Cannot confirm BOEM compliance or adequacy of $9.22mm provision", "Request ARO actuarial report and BOEM decom filing status"],
                ["Oil price deck (Corporate Model)", "🟠 High", "Revenue line unverifiable — 65% oil-weighted production", "Request oil price assumptions from Corporate Model vF"],
                ["Process letter / bid deadline", "🟡 Medium", "Timing and exclusivity terms unknown", "Request from AMP Energy (Ben Colegrave, Paul Connolly)"],
                ["EI183/184 legacy ARO exposure", "🟡 Medium", "Potential ~$1.35mm BOEM demand; no recent notice", "Seek cash escrow / seller indemnity at close"],
            ],
            "footnote": "Source: VDR Gap Analysis (Aigis), IM p.17–18. Contact AMP Energy: Ben Colegrave (bc@amp-energy.co.uk), Paul Connolly (paul@amp-energy.co.uk). All risk classifications per Aigis DD framework (c).",
        },
    },

    # ── 24. Section divider: Transaction ──────────────────────────────────
    {
        "slide_type": "section_divider",
        "data": {
            "section": "08",
            "title":   "Transaction Structure",
            "subtitle": "Entity acquisition mechanics and liability treatment",
        },
    },

    # ── 25. Transaction Structure ──────────────────────────────────────────
    {
        "slide_type": "split",
        "data": {
            "section": "Transaction Structure",
            "title": "Transaction Mechanics — Entity Acquisition (MIPA)",
            "left": {
                "heading": "Structure & Advantages",
                "items": [
                    "100% membership interest in Byron Energy LLC (Delaware)",
                    "Entity acquisition — preserves BOEM bonds, qualifications, vendor MSAs",
                    "Avoids lease assignment approvals (Apache SM58/69 legacy consents)",
                    "Shell STUSCO marketing facility: zero principal outstanding at close",
                    "Shareholder vote: board + associates control ~70% — outcome effectively certain",
                    "BOEM-qualified entity (Byron Energy Inc.) passes to buyer intact",
                ],
            },
            "right": {
                "heading": "Liabilities at Close",
                "items": [
                    "Director/SH loan (~$3.67mm): REPAID from proceeds",
                    "Vendor rescheduling (~$4.96mm, 35 vendors): REPAID from proceeds",
                    "STUSCO marketing fee tail (~$0.98mm): buyer inherits, winds down",
                    "Insurance premium financing ($1.60mm): buyer inherits, normal course",
                    "Trade payables ($6.64mm current): working capital adjustment",
                    "ARO provision ($9.22mm on balance sheet): buyer inherits",
                    "EI183/184 legacy ARO (~$1.35mm): seek escrow/indemnity",
                    "One vendor (NOV) unresolved — maritime lien risk",
                ],
            },
            "footnote": "Source: Byron IM p.15, p.17–18. Management Presentation p.17. Seller figures (a); Aigis risk flags (c). ⚠️ MIPA not fully reviewed — request near-final version from AMP Energy before binding bid.",
        },
    },

    # ── 26. Section divider: Next Steps ───────────────────────────────────
    {
        "slide_type": "section_divider",
        "data": {
            "section": "09",
            "title":   "Next Steps",
            "subtitle": "Pre-bid action plan and board approval pathway",
        },
    },

    # ── 27. Process Timeline ───────────────────────────────────────────────
    {
        "slide_type": "timeline",
        "data": {
            "section": "Next Steps",
            "title": "Pre-Bid Action Plan & Process Timeline",
            "events": [
                {
                    "date":  "Immediate",
                    "title": "Obtain JOAs + MIPA",
                    "body":  "Request all Joint Operating Agreements (SM71/58/69/70) and near-final MIPA from AMP Energy. Confirm Otto Energy ROFR status and change-of-control provisions.",
                },
                {
                    "date":  "Week 1–2",
                    "title": "Legal & Financial Diligence",
                    "body":  "Request US subsidiary standalone financials, oil price deck, Phase I environmental, ARO actuarial. Engage GoM specialist outside counsel for JOA review.",
                },
                {
                    "date":  "Week 2–3",
                    "title": "Technical Verification",
                    "body":  "Independent CPR update request (9 months old — update to within 6 months of close). Verify G9 seismic interpretation with independent geologist. Confirm SM70 lease holding strategy.",
                },
                {
                    "date":  "Week 3–4",
                    "title": "Binding Bid Submission",
                    "body":  "Submit binding bid of $130–145mm headline (plus CVR of +$15–25mm contingent on SM70 H1 first production). Include conditionality on JOA/ROFR confirmation and MIPA sign-off.",
                },
                {
                    "date":  "Post-Bid",
                    "title": "Exclusivity & Close",
                    "body":  "Target BOEM entity-level change notification + shareholder vote. Coordinate G9 rig booking for 1Q 2026 spud. Obtain STUSCO change-of-control consent.",
                },
            ],
            "footnote": "AMP Energy contacts: Ben Colegrave (bc@amp-energy.co.uk), Paul Connolly (paul@amp-energy.co.uk), Max Thenard (max@amp-energy.co.uk), Adil Kurt-Elli (adil@amp-energy.co.uk). Source: Byron Teaser p.4. Seller figures (a).",
        },
    },

    # ── 28. Closing ────────────────────────────────────────────────────────
    {
        "slide_type": "closing",
        "data": {
            "title":    "Project Corsair",
            "subtitle": "Recommendation: Proceed — Binding Bid $130–145mm",
            "message":  (
                "Byron Energy LLC offers a proven oil-weighted production base with 25-year 2P reserve life, "
                "a drill-ready near-term portfolio (G9 + G8 in 2026), and a clean balance sheet delivering "
                "zero debt at close. The recommended bid of $130–145mm represents 56–63% of 2P CPR NPV10 — "
                "appropriate for a GoM shelf operator with above-benchmark LOE and material near-term drilling upside. "
                "Critical pre-conditions: JOA/ROFR confirmation (SM71/Otto Energy) and receipt of US subsidiary "
                "standalone financials before binding bid submission."
            ),
            "contact":  "Aigis Analytics Limited | Private & Confidential | April 2026",
        },
    },
]


# ---------------------------------------------------------------------------
# Generate the deck
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from inkline.typst import export_typst_slides

    print(f"\n{'='*68}")
    print(" INKLINE — Project Corsair Board DD Deck")
    print(f" Slides: {len(slides)} | Brand: aigis | Template: consulting")
    print(f" Output: {OUTPUT_PATH}")
    print(f"{'='*68}\n")

    result = export_typst_slides(
        slides=slides,
        output_path=OUTPUT_PATH,
        brand="aigis",
        template="consulting",
        title="Project Corsair — Board Investment Memorandum",
        subtitle="Byron Energy LLC Acquisition",
        date="April 2026",
        source_narrative=(
            "Project Corsair is the proposed acquisition of 100% of Byron Energy LLC, "
            "a GoM shallow-water E&P company holding 4 lease blocks (SM71 50% WI, SM58 100% WI, "
            "SM69 53-70% WI, SM70 100% WI) on the SM73 salt dome ~70 miles offshore Louisiana. "
            "Current net production: 1,354 boepd (65% oil). 2P reserves: 12.7 MMboe (NPV10 $231mm, Collarini CPR Jul-25). "
            "Recommended bid: $130-145mm. Top risk: JOA missing from VDR — Otto Energy ROFR at SM71 unconfirmed. "
            "Near-term catalyst: G9 Cutthroat North well (1Q 2026), 6,417 Mboe PR, NPV10 $166mm unrisked."
        ),
        audit=True,
        auto_fix=True,
        max_overflow_attempts=6,
        max_visual_attempts=5,
    )

    print(f"\n{'='*68}")
    print(f" PDF ready: {result}")
    print(f"{'='*68}\n")
