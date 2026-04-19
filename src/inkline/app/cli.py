"""Inkline CLI — entry point for the standalone app commands.

Usage
-----
    inkline serve              # start bridge + WebUI at http://localhost:8082
    inkline serve --port 9000  # custom port
    inkline bridge             # bridge only (no browser auto-open)
    inkline mcp                # start MCP server (stdio transport)
"""

from __future__ import annotations

import argparse
import shutil
import sys
import webbrowser
from pathlib import Path


def _check_claude() -> None:
    if not shutil.which("claude"):
        print(
            "WARNING: 'claude' CLI not found on PATH.\n"
            "Install Claude Code and authenticate:\n"
            "  npm install -g @anthropic-ai/claude-code\n"
            "  claude /login\n",
            file=sys.stderr,
        )


def cmd_serve(args: argparse.Namespace) -> None:
    """Start the bridge and open the WebUI in the default browser."""
    _check_claude()
    print(f"Starting Inkline on http://localhost:{args.port}/")
    if not args.no_browser:
        # Delay browser open slightly so the server has time to bind
        import threading
        def _open():
            import time; time.sleep(1.5)
            webbrowser.open(f"http://localhost:{args.port}/")
        threading.Thread(target=_open, daemon=True).start()

    from inkline.app.claude_bridge import main as bridge_main
    bridge_main(port=args.port)


def cmd_bridge(args: argparse.Namespace) -> None:
    """Start the bridge server only (no browser)."""
    _check_claude()
    print(f"Starting Inkline bridge on http://localhost:{args.port}/")
    from inkline.app.claude_bridge import main as bridge_main
    bridge_main(port=args.port)


def cmd_mcp(_args: argparse.Namespace) -> None:
    """Start the MCP server (stdio transport for Claude Desktop / Claude.ai)."""
    try:
        from inkline.app.mcp_server import main as mcp_main
        mcp_main()
    except ImportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_learn(args: argparse.Namespace) -> None:
    """Run the feedback aggregator and pattern extractor to update learned patterns."""
    nightly = getattr(args, "nightly", False)
    brand = getattr(args, "brand", None) or None

    # Always run the existing feedback aggregator
    try:
        from inkline.intelligence.aggregator import Aggregator
        agg = Aggregator()
        report = agg.run_full_pass()
        print(report)
    except Exception as exc:
        print(f"WARNING: Aggregator failed: {exc}", file=sys.stderr)

    # Run the new pattern extractor
    try:
        from inkline.learning.extractor import run_nightly_extraction
        ext_report = run_nightly_extraction(brand=brand)
        if nightly:
            print(f"Nightly extraction: {ext_report.summary}")
        else:
            print(f"Pattern extraction: {ext_report.summary}")
    except Exception as exc:
        print(f"WARNING: Pattern extractor failed: {exc}", file=sys.stderr)


def cmd_privacy(args: argparse.Namespace) -> None:
    """Show stored learning data summary and federation status, or toggle federation."""
    try:
        from inkline.learning.federation import (
            get_privacy_summary,
            set_federation_enabled,
        )
        if args.disable:
            set_federation_enabled(False)
            print("Federation disabled. No data will be exported to the community.")
        elif args.enable:
            set_federation_enabled(True)
            print("Federation enabled. Safe structural signals will be shared with the community.")
        else:
            brand = getattr(args, "brand", "") or ""
            print(get_privacy_summary(brand=brand))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_export_patterns(args: argparse.Namespace) -> None:
    """Export anonymised pattern delta for community sharing."""
    try:
        import datetime
        import json as _json
        from inkline.learning.federation import export_pattern_delta, FederationDisabledError

        since_str = getattr(args, "since", None) or ""
        dry_run = getattr(args, "dry_run", False)

        if since_str:
            since = datetime.datetime.fromisoformat(since_str).replace(
                tzinfo=datetime.timezone.utc
            )
        else:
            # Default: last 30 days
            since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)

        delta = export_pattern_delta(
            since=since,
            include_dm_rules=True,
            include_anti_patterns=True,
            dry_run=dry_run,
        )
        print(_json.dumps(delta, indent=2))
        if dry_run:
            print("\n(dry-run: nothing was posted)", file=sys.stderr)

    except Exception as exc:
        # FederationDisabledError is a subclass of RuntimeError
        name = type(exc).__name__
        print(f"ERROR [{name}]: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_ingest(args: argparse.Namespace) -> None:
    """Ingest a reference PDF deck to extract design patterns."""
    try:
        from inkline.intelligence.deck_analyser import DeckAnalyser
        from inkline.intelligence.aggregator import (
            load_decision_matrix, save_decision_matrix, _CONFIG_DIR,
        )
        pdf = Path(args.pdf_path)
        if not pdf.exists():
            print(f"ERROR: File not found: {args.pdf_path}", file=sys.stderr)
            sys.exit(1)

        deck_name = args.deck_name or pdf.stem
        print(f"Analysing {pdf.name} as '{deck_name}'...")

        analyser = DeckAnalyser()
        analysis = analyser.analyse(str(pdf), deck_name=deck_name)

        output_dir = _CONFIG_DIR / "reference_decks" / deck_name
        analysis.save(output_dir)

        # Append candidate rules to decision matrix
        dm = load_decision_matrix()
        existing_pairs = {
            (r["data_structure"], r["message_type"], r["chart_type"])
            for r in dm.get("rules", [])
        }
        added = 0
        for cand in analysis.dm_candidates:
            triple = (cand["data_structure"], cand["message_type"], cand["chart_type"])
            if triple not in existing_pairs:
                cand["id"] = f"DM-I{len(dm.get('rules', [])) + 1:03d}"
                cand["source"] = [deck_name]
                if "rules" not in dm:
                    dm["rules"] = []
                dm["rules"].append(cand)
                existing_pairs.add(triple)
                added += 1
        save_decision_matrix(dm)

        print(f"Done.")
        print(f"  Slides analysed : {analysis.slide_count}")
        print(f"  Charts found    : {analysis.chart_vocabulary}")
        print(f"  Candidate rules : {added} added to decision matrix")
        print(f"  Patterns saved  : {output_dir / 'patterns.md'}")

    except ImportError as exc:
        print(f"ERROR: {exc}\nInstall pymupdf: pip install pymupdf", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="inkline",
        description="Inkline — branded document and presentation toolkit",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    # inkline serve
    serve_p = sub.add_parser(
        "serve",
        help="Start the Inkline WebUI and Claude bridge (http://localhost:8082)",
    )
    serve_p.add_argument("--port", type=int, default=8082, metavar="PORT",
                         help="Port to listen on (default: 8082)")
    serve_p.add_argument("--no-browser", action="store_true",
                         help="Don't auto-open the browser")
    serve_p.set_defaults(func=cmd_serve)

    # inkline bridge
    bridge_p = sub.add_parser(
        "bridge",
        help="Start the Claude bridge server only (no browser auto-open)",
    )
    bridge_p.add_argument("--port", type=int, default=8082, metavar="PORT",
                          help="Port to listen on (default: 8082)")
    bridge_p.set_defaults(func=cmd_bridge)

    # inkline mcp
    mcp_p = sub.add_parser(
        "mcp",
        help="Start the MCP server for Claude Desktop / Claude.ai integration",
    )
    mcp_p.set_defaults(func=cmd_mcp)

    # inkline learn
    learn_p = sub.add_parser(
        "learn",
        help="Process feedback log, update decision matrix, and extract patterns",
    )
    learn_p.add_argument("--nightly", action="store_true",
                         help="Run full nightly extraction pass (suitable for cron)")
    learn_p.add_argument("--brand", default="", metavar="BRAND",
                         help="Limit extraction to a single brand")
    learn_p.set_defaults(func=cmd_learn)

    # inkline privacy
    privacy_p = sub.add_parser(
        "privacy",
        help="Show learning data summary and federation status",
    )
    privacy_p.add_argument("--disable", action="store_true",
                            help="Disable community federation (no data exported)")
    privacy_p.add_argument("--enable", action="store_true",
                            help="Re-enable community federation")
    privacy_p.add_argument("--brand", default="", metavar="BRAND",
                            help="Show stats for a specific brand")
    privacy_p.set_defaults(func=cmd_privacy)

    # inkline export-patterns
    export_p = sub.add_parser(
        "export-patterns",
        help="Export anonymised pattern delta for community sharing",
    )
    export_p.add_argument("--since", default="", metavar="YYYY-MM-DD",
                           help="Only include data since this date (default: last 30 days)")
    export_p.add_argument("--dry-run", action="store_true",
                           help="Preview the export without posting to any endpoint")
    export_p.set_defaults(func=cmd_export_patterns)

    # inkline ingest
    ingest_p = sub.add_parser(
        "ingest",
        help="Ingest a reference PDF deck to extract design patterns",
    )
    ingest_p.add_argument("pdf_path", metavar="PDF", help="Path to the PDF file")
    ingest_p.add_argument("--name", dest="deck_name", default="",
                          help="Deck identifier (default: filename stem)")
    ingest_p.set_defaults(func=cmd_ingest)

    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
