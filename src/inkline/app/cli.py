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
import sys
import webbrowser
from pathlib import Path

from inkline.app.llm_backends import available_backend_names, resolve_backend


def _check_backend(backend_name: str) -> None:
    backend = resolve_backend(backend_name)
    if backend.available():
        return
    available = ", ".join(available_backend_names()) or "none"
    if backend.name == "claude":
        print(
            "WARNING: 'claude' CLI not found on PATH.\n"
            "Install Claude Code and authenticate:\n"
            "  npm install -g @anthropic-ai/claude-code\n"
            "  claude /login\n",
            file=sys.stderr,
        )
        return
    print(
        f"WARNING: '{backend.executable}' CLI not found on PATH.\n"
        "Install and authenticate the Gemini CLI, or choose a different backend.\n"
        f"Available backends on this machine: {available}\n",
        file=sys.stderr,
    )


def cmd_serve(args: argparse.Namespace) -> None:
    """Start the bridge and open the WebUI in the default browser."""
    _check_backend(getattr(args, "backend", "auto"))
    print(f"Starting Inkline on http://localhost:{args.port}/")
    if not args.no_browser:
        # Delay browser open slightly so the server has time to bind
        import threading
        def _open():
            import time; time.sleep(1.5)
            webbrowser.open(f"http://localhost:{args.port}/")
        threading.Thread(target=_open, daemon=True).start()

    from inkline.app.claude_bridge import main as bridge_main
    bridge_main(port=args.port, backend_name=getattr(args, "backend", "auto"))


def cmd_bridge(args: argparse.Namespace) -> None:
    """Start the bridge server only (no browser)."""
    _check_backend(getattr(args, "backend", "auto"))
    print(f"Starting Inkline bridge on http://localhost:{args.port}/")
    from inkline.app.claude_bridge import main as bridge_main
    bridge_main(port=args.port, backend_name=getattr(args, "backend", "auto"))


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


def cmd_render(args: argparse.Namespace) -> None:
    """Render a markdown file to PDF (and optionally other formats).

    This is the non-agentic path: preprocessor → DesignAdvisor → exporter.
    It does NOT route through Claude agentic mode — suitable for CI and
    the live-preview editor.
    """
    import json as _json
    from pathlib import Path as _Path

    md_path = _Path(args.file)
    if not md_path.exists():
        print(f"ERROR: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)

    try:
        from inkline.authoring.preprocessor import preprocess
        from inkline.intelligence import DesignAdvisor
        from inkline.typst import export_typst_slides
        from inkline.intelligence import audit_deck, format_report
    except ImportError as exc:
        print(f"ERROR: {exc}\nInstall Inkline with: pip install inkline[all]", file=sys.stderr)
        sys.exit(1)

    md_text = md_path.read_text(encoding="utf-8")
    print(f"[inkline render] Preprocessing {md_path.name}...")

    deck_meta, sections = preprocess(
        md_text,
        strict_directives=args.strict_directives,
        source_path=str(md_path),
    )

    # CLI flags override front-matter
    brand    = args.brand    or deck_meta.get("brand", "minimal")
    template = args.template or deck_meta.get("template", "consulting")
    mode     = deck_meta.get("mode", "rules")  # default rules for non-agentic

    print(f"[inkline render] Designing deck (brand={brand}, template={template}, mode={mode})...")

    advisor = DesignAdvisor(brand=brand, template=template, mode=mode)
    slides = advisor.design_deck(
        title=deck_meta.get("title", md_path.stem),
        subtitle=deck_meta.get("subtitle", ""),
        date=deck_meta.get("date", ""),
        sections=sections,
        audience=deck_meta.get("audience", ""),
        goal=deck_meta.get("goal", ""),
    )

    # Determine output path
    output_dir = _Path("~/.local/share/inkline/output").expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    out_stem = md_path.stem
    pdf_path = output_dir / f"{out_stem}.pdf"

    print(f"[inkline render] Exporting to {pdf_path}...")
    export_typst_slides(
        slides=slides,
        output_path=str(pdf_path),
        brand=brand,
        template=template,
    )

    # Write notes file
    try:
        from inkline.authoring.notes_writer import write_notes
        notes_path = write_notes(pdf_path, slides, sections)
        print(f"[inkline render] Notes → {notes_path}")
    except Exception as exc:
        print(f"[inkline render] WARNING: notes writer failed: {exc}", file=sys.stderr)

    # Structural audit
    audit_level = deck_meta.get("audit", "structural")
    if audit_level != "off":
        warnings = audit_deck(slides)
        if warnings:
            print(format_report(warnings))

    print(f"PDF ready: {pdf_path}")

    if args.watch:
        print(f"[inkline render] Watch mode — monitoring {md_path} for changes...")
        _run_watch(md_path, args)


def _run_watch(md_path: "Path", args: "argparse.Namespace") -> None:
    """File-watch loop for --watch flag (synchronous polling fallback)."""
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        print("ERROR: watchdog is required for --watch. Install with: pip install watchdog",
              file=sys.stderr)
        sys.exit(1)

    import time
    from pathlib import Path

    _last_render = [0.0]
    _DEBOUNCE = 0.25

    class _Handler(FileSystemEventHandler):
        def on_modified(self, event):
            if event.src_path == str(md_path.resolve()):
                now = time.time()
                if now - _last_render[0] < _DEBOUNCE:
                    return
                _last_render[0] = now
                print(f"\n[inkline watch] Change detected — re-rendering...")
                try:
                    cmd_render(args)
                except Exception as exc:
                    print(f"[inkline watch] Render error: {exc}", file=sys.stderr)

    observer = Observer()
    observer.schedule(_Handler(), str(md_path.parent), recursive=False)
    observer.start()
    print(f"[inkline watch] Watching {md_path} — Ctrl+C to stop")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def cmd_backend_coverage(_args: argparse.Namespace) -> None:
    """Print the slide-type × backend coverage matrix."""
    try:
        from inkline.authoring.backend_coverage import print_coverage_table
        print(print_coverage_table())
    except ImportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_knowledge(args: argparse.Namespace) -> None:
    """Browse the Inkline design knowledge base from the command line."""
    from inkline.app.mcp_resources import list_resources, read_resource, ResourceNotFoundError

    sub = getattr(args, "knowledge_cmd", None)

    if sub == "list" or sub is None:
        resources = list_resources()
        print(f"Inkline knowledge base — {len(resources)} resources\n")
        for r in resources:
            print(f"  {r['uri']}")
            if r.get("description"):
                print(f"      {r['description']}")
        print()

    elif sub == "get":
        uri = args.uri
        if not uri.startswith("inkline://"):
            # Allow short form: layouts/three_card → inkline://layouts/three_card
            uri = f"inkline://{uri}"
        try:
            content = read_resource(uri)
            print(content)
        except ResourceNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)

    elif sub == "search":
        query = args.query.lower()
        resources = list_resources()
        matches = [
            r for r in resources
            if query in r["uri"].lower() or query in r.get("description", "").lower()
        ]
        if not matches:
            print(f"No resources matched {args.query!r}")
        else:
            print(f"Matches for {args.query!r}:\n")
            for r in matches:
                print(f"  {r['uri']}")
                if r.get("description"):
                    print(f"      {r['description']}")

    else:
        print(f"Unknown knowledge subcommand: {sub!r}. Use: list, get <uri>, search <query>")
        sys.exit(1)


def cmd_validate(args: argparse.Namespace) -> None:
    """Pre-render validation: image paths, capacity, schema."""
    from pathlib import Path as _Path

    spec_path = _Path(args.spec)
    if not spec_path.exists():
        print(f"ERROR: File not found: {args.spec}", file=sys.stderr)
        sys.exit(1)

    try:
        from inkline.authoring.preprocessor import preprocess
        from inkline.authoring.image_strategy import validate_image_directives_in_sections
    except ImportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    md_text = spec_path.read_text(encoding="utf-8")
    deck_meta, sections = preprocess(
        md_text,
        strict_directives=args.strict,
        source_path=str(spec_path),
    )

    print(f"[inkline validate] {spec_path.name}")
    print(f"  Brand:    {deck_meta.get('brand', 'minimal')}")
    print(f"  Sections: {len(sections)}")
    print(f"  Audit:    {deck_meta.get('audit', 'structural')}")

    # Validate image directives
    issues = []
    try:
        warnings = validate_image_directives_in_sections(
            sections, base_dir=spec_path.parent, dry_run=True
        )
        issues.extend(warnings)
    except FileNotFoundError as exc:
        print(f"\n[FAIL] Image path error: {exc}", file=sys.stderr)
        sys.exit(1)

    if issues:
        print(f"\n{len(issues)} issue(s) found:")
        for issue in issues:
            print(f"  [{issue['severity'].upper()}] Slide {issue['slide_index']}: {issue['issue']}")
        sys.exit(1)
    else:
        print("\n[OK] Spec is valid.")


def cmd_critique(args: argparse.Namespace) -> None:
    """Post-render visual audit of a PDF using Vishwakarma vision model."""
    from pathlib import Path as _Path

    pdf_path = _Path(args.pdf)
    if not pdf_path.exists():
        print(f"ERROR: File not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)

    try:
        from inkline.intelligence.vishwakarma import critique_pdf
    except ImportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"[inkline critique] Auditing {pdf_path.name} with rubric '{args.rubric}'...")
    try:
        result = critique_pdf(
            pdf_path=str(pdf_path),
            rubric=args.rubric,
            brand=args.brand,
        )
        import json as _json
        print(_json.dumps(result.to_dict(), indent=2))
    except Exception as exc:
        print(f"ERROR: critique failed: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_draft(args: argparse.Namespace) -> None:
    """Start Draft Mode — the agentic /prompt path.

    This is an explicit alias for 'inkline serve' that makes the opt-in
    agentic path discoverable. Opens the bridge WebUI with a note that
    Draft Mode is active.
    """
    _check_backend(getattr(args, "backend", "auto"))
    print(
        "Starting Inkline in Draft Mode "
        f"(agentic path — backend={getattr(args, 'backend', 'auto')})"
    )
    print("Navigate to http://localhost:{}/  to use the conversational interface.".format(
        getattr(args, "port", 8082)
    ))
    from inkline.app.claude_bridge import main as bridge_main
    bridge_main(
        port=getattr(args, "port", 8082),
        backend_name=getattr(args, "backend", "auto"),
    )


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
    serve_p.add_argument("--backend", default="auto", choices=["auto", "claude", "gemini"],
                         help="LLM backend for Draft Mode and critique routes (default: auto)")
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
    bridge_p.add_argument("--backend", default="auto", choices=["auto", "claude", "gemini"],
                          help="LLM backend for agentic routes (default: auto)")
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

    # inkline render
    render_p = sub.add_parser(
        "render",
        help="Render a .md file to PDF (non-agentic; no Claude call)",
    )
    render_p.add_argument("file", metavar="FILE.md", help="Markdown source file")
    render_p.add_argument("--output", default="pdf", metavar="FORMATS",
                          help="Comma-separated output formats: pdf,pptx (default: pdf)")
    render_p.add_argument("--brand", default="", metavar="BRAND",
                          help="Override brand from front-matter")
    render_p.add_argument("--template", default="", metavar="TEMPLATE",
                          help="Override template from front-matter")
    render_p.add_argument("--watch", action="store_true",
                          help="Watch for file changes and re-render")
    render_p.add_argument("--serve", action="store_true",
                          help="Open the bridge WebUI after rendering (requires inkline serve)")
    render_p.add_argument("--strict-directives", action="store_true",
                          help="Treat unknown/invalid directives as errors")
    render_p.set_defaults(func=cmd_render)

    # inkline watch (alias for render --watch --serve)
    watch_p = sub.add_parser(
        "watch",
        help="Alias for 'render --watch --serve' — live reload on edit",
    )
    watch_p.add_argument("file", metavar="FILE.md", help="Markdown source file")
    watch_p.add_argument("--brand", default="", metavar="BRAND")
    watch_p.add_argument("--template", default="", metavar="TEMPLATE")
    watch_p.add_argument("--strict-directives", action="store_true")
    watch_p.set_defaults(func=lambda a: cmd_render(
        type("_Args", (), {**vars(a), "watch": True, "serve": True, "output": "pdf"})()
    ))

    # inkline backend-coverage
    bc_p = sub.add_parser(
        "backend-coverage",
        help="Print slide-type × backend coverage matrix",
    )
    bc_p.set_defaults(func=cmd_backend_coverage)

    # inkline knowledge
    knowledge_p = sub.add_parser(
        "knowledge",
        help="Browse the Inkline design knowledge base (execute-mode primary resource)",
    )
    knowledge_sub = knowledge_p.add_subparsers(dest="knowledge_cmd", metavar="SUBCMD")

    knowledge_sub.add_parser("list", help="List all knowledge resources")

    kget_p = knowledge_sub.add_parser("get", help="Print a resource by URI")
    kget_p.add_argument("uri", metavar="URI",
                        help="Resource URI (e.g. inkline://layouts/three_card or layouts/three_card)")

    ksearch_p = knowledge_sub.add_parser("search", help="Search knowledge by keyword")
    ksearch_p.add_argument("query", metavar="QUERY", help="Search query")

    knowledge_p.set_defaults(func=cmd_knowledge)

    # inkline validate
    validate_p = sub.add_parser(
        "validate",
        help="Pre-render validation: check image paths, capacity, directives (execute-mode)",
    )
    validate_p.add_argument("spec", metavar="SPEC.md", help="Spec file to validate")
    validate_p.add_argument("--strict", action="store_true",
                            help="Treat unknown directives as errors")
    validate_p.set_defaults(func=cmd_validate)

    # inkline critique
    critique_p = sub.add_parser(
        "critique",
        help="Post-render visual audit of a PDF (Vishwakarma vision model)",
    )
    critique_p.add_argument("pdf", metavar="PDF", help="Path to the rendered PDF")
    critique_p.add_argument("--rubric", default="institutional",
                            choices=["institutional", "tech_pitch", "internal_review"],
                            help="Audit rubric to apply (default: institutional)")
    critique_p.add_argument("--brand", default="", metavar="BRAND",
                            help="Brand context for brand-aware critique")
    critique_p.set_defaults(func=cmd_critique)

    # inkline draft
    draft_p = sub.add_parser(
        "draft",
        help="Opt-in: start Draft Mode (agentic /prompt path via Claude or Gemini)",
    )
    draft_p.add_argument("--port", type=int, default=8082, metavar="PORT")
    draft_p.add_argument("--backend", default="auto", choices=["auto", "claude", "gemini"])
    draft_p.set_defaults(func=cmd_draft)

    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
