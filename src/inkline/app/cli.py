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
import json
import os
import sys
import webbrowser
from pathlib import Path

from inkline.app.llm_backends import available_backend_names, resolve_backend


KNOWN_EXECUTION_MODES = {"draft", "explicit_spec"}


def _resolve_execution_contract(args: argparse.Namespace, deck_meta: dict | None = None) -> dict[str, object]:
    deck_meta = deck_meta or {}
    execution_mode = str(
        getattr(args, "execution_mode", "") or deck_meta.get("execution_mode", "") or "explicit_spec"
    ).strip()
    if execution_mode not in KNOWN_EXECUTION_MODES:
        allowed = ", ".join(sorted(KNOWN_EXECUTION_MODES))
        raise ValueError(f"Unknown execution_mode '{execution_mode}'. Allowed values: {allowed}")
    design_locked = getattr(args, "design_locked", None)
    if design_locked is None:
        design_locked = deck_meta.get("design_locked")
    if design_locked is None:
        design_locked = execution_mode == "explicit_spec"
    use_design_advisor = getattr(args, "use_design_advisor", None)
    if use_design_advisor is None:
        use_design_advisor = deck_meta.get("use_design_advisor")
    if use_design_advisor is None:
        use_design_advisor = execution_mode == "draft"
    authoring_mode = str(
        getattr(args, "authoring_mode", "") or deck_meta.get("authoring_mode", "")
        or ("external_llm" if execution_mode == "explicit_spec" else "inkline_draft")
    ).strip()
    return {
        "execution_mode": execution_mode,
        "design_locked": bool(design_locked),
        "use_design_advisor": bool(use_design_advisor),
        "authoring_mode": authoring_mode,
    }


def _enforce_explicit_spec_sections(sections: list[dict], *, source_name: str) -> None:
    offenders: list[str] = []
    for idx, section in enumerate(sections, start=1):
        slide_mode = str(section.get("slide_mode", "") or "").strip() or "auto"
        slide_type = str(section.get("slide_type", "") or "").strip()
        if slide_mode != "exact" or not slide_type:
            title = str(section.get("title", "") or f"Section {idx}")
            offenders.append(f"{idx}:{title} (slide_mode={slide_mode}, slide_type={slide_type or 'missing'})")
    if offenders:
        joined = "; ".join(offenders[:6])
        raise ValueError(
            f"execution_mode=explicit_spec requires every section in {source_name} "
            f"to declare _layout and resolve to slide_mode=exact. Offenders: {joined}"
        )


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

    source_path = _Path(args.file)
    if not source_path.exists():
        print(f"ERROR: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    formats = [fmt.strip() for fmt in str(args.output).split(",") if fmt.strip()]
    if not formats:
        formats = ["pdf"]

    if source_path.suffix.lower() in {".yaml", ".yml", ".json"}:
        from inkline.app.institutional import render_spec_file

        artifacts = render_spec_file(
            source_path,
            formats=formats,
            output_dir=args.output_dir,
            editable_institutional=bool(getattr(args, "editable_institutional", False)),
            brand_override=args.brand,
            template_override=args.template,
            execution_mode=str(getattr(args, "execution_mode", "") or ""),
            design_locked=getattr(args, "design_locked", None),
            use_design_advisor=getattr(args, "use_design_advisor", None),
            authoring_mode=str(getattr(args, "authoring_mode", "") or ""),
        )
        if artifacts.pdf_path:
            print(f"PDF ready: {artifacts.pdf_path}")
        if artifacts.pptx_path:
            print(f"PPTX ready: {artifacts.pptx_path}")
        if artifacts.export_metadata_path:
            print(f"Export metadata: {artifacts.export_metadata_path}")
        if getattr(args, "serve", False):
            webbrowser.open(_bridge_url())
        if args.watch:
            print(f"[inkline render] Watch mode — monitoring {source_path} for changes...")
            _run_watch(source_path, args)
        return

    try:
        from inkline.authoring.preprocessor import preprocess
        from inkline.intelligence import DesignAdvisor
        from inkline.typst import export_typst_slides
        from inkline.intelligence import audit_deck, format_report
    except ImportError as exc:
        print(
            "ERROR: "
            f"{exc}\nInstall this Inkline project from the Aigis/GitHub repo:\n"
            "  pip install \"inkline[all,mcp] @ git+https://github.com/aigis-analytics/inkline.git\"\n"
            "For local development from a checkout:\n"
            "  pip install -e \".[all,mcp]\"",
            file=sys.stderr,
        )
        sys.exit(1)

    md_text = source_path.read_text(encoding="utf-8")
    print(f"[inkline render] Preprocessing {source_path.name}...")

    deck_meta, sections = preprocess(
        md_text,
        strict_directives=args.strict_directives,
        source_path=str(source_path),
    )
    execution_contract = _resolve_execution_contract(args, deck_meta)

    # CLI flags override front-matter
    brand    = args.brand    or deck_meta.get("brand", "minimal")
    template = args.template or deck_meta.get("template", "consulting")
    mode     = deck_meta.get("mode", "rules")  # default rules for non-agentic
    if execution_contract["execution_mode"] == "explicit_spec":
        _enforce_explicit_spec_sections(sections, source_name=source_path.name)
        mode = "rules"

    print(
        "[inkline render] Designing deck "
        f"(brand={brand}, template={template}, mode={mode}, execution_mode={execution_contract['execution_mode']})..."
    )

    advisor = DesignAdvisor(brand=brand, template=template, mode=mode)
    slides = advisor.design_deck(
        title=deck_meta.get("title", source_path.stem),
        subtitle=deck_meta.get("subtitle", ""),
        date=deck_meta.get("date", ""),
        sections=sections,
        audience=deck_meta.get("audience", ""),
        goal=deck_meta.get("goal", ""),
    )
    from inkline.intelligence.storyboard import resolve_storyboard_spec, write_storyboard_artifacts

    resolved_spec = resolve_storyboard_spec(
        {
            "title": deck_meta.get("title", source_path.stem),
            "audience": deck_meta.get("audience", ""),
            "reference_family": deck_meta.get("reference_family", ""),
            **execution_contract,
            "storyboard": deck_meta.get("storyboard", {}),
            "slides": slides,
        },
        source_name=str(source_path),
    )
    slides = resolved_spec["slides"]

    # Determine output path
    output_dir = _Path("~/.local/share/inkline/output").expanduser()
    if getattr(args, "output_dir", None):
        output_dir = _Path(args.output_dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    out_stem = source_path.stem
    pdf_path = output_dir / f"{out_stem}.pdf"
    pptx_path = output_dir / f"{out_stem}.pptx"
    pptx_meta_path = output_dir / f"{out_stem}.export_metadata.json"
    try:
        if resolved_spec:
            write_storyboard_artifacts(resolved_spec, output_dir=output_dir, stem=out_stem)
    except Exception as exc:
        print(
            f"[inkline render] WARNING: could not write storyboard artifacts: {exc}",
            file=sys.stderr,
        )
        raise

    if "pdf" in formats:
        print(f"[inkline render] Exporting to {pdf_path}...")
        export_typst_slides(
            slides=slides,
            output_path=str(pdf_path),
            brand=brand,
            template=template,
        )

    if "pptx" in formats:
        from inkline.pptx import export_pptx_slides
        from inkline.app.institutional import _portable_sidecar_payload
        print(f"[inkline render] Exporting to {pptx_path}...")
        export_pptx_slides(
            slides=slides,
            output_path=pptx_path,
            brand=brand,
            title=deck_meta.get("title", source_path.stem),
            source_root=source_path.parent,
            metadata_path=pptx_meta_path,
            editable_institutional=bool(getattr(args, "editable_institutional", False)),
            deck_metadata=_portable_sidecar_payload({
                "storyboard": resolved_spec.get("_resolved_storyboard", {}),
                "authoring_trace": resolved_spec.get("_authoring_trace", {}),
            }),
        )

    # Write notes file
    try:
        from inkline.authoring.notes_writer import write_notes
        notes_target = pdf_path if "pdf" in formats else pptx_path
        notes_path = write_notes(notes_target, slides, sections)
        print(f"[inkline render] Notes → {notes_path}")
    except Exception as exc:
        print(f"[inkline render] WARNING: notes writer failed: {exc}", file=sys.stderr)

    # Structural audit
    audit_level = deck_meta.get("audit", "structural")
    if audit_level != "off":
        warnings = audit_deck(slides)
        if warnings:
            print(format_report(warnings))

    if "pdf" in formats:
        print(f"PDF ready: {pdf_path}")
    if "pptx" in formats:
        print(f"PPTX ready: {pptx_path}")
        print(f"Export metadata: {pptx_meta_path}")

    if getattr(args, "serve", False):
        webbrowser.open(_bridge_url())

    if args.watch:
        print(f"[inkline render] Watch mode — monitoring {source_path} for changes...")
        _run_watch(source_path, args)


def cmd_ingest_reference(args: argparse.Namespace) -> None:
    try:
        from inkline.intelligence.reference_ingest import ingest_reference_pptx
    except ImportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    payload = ingest_reference_pptx(
        args.pptx,
        family_id=args.family,
        license_classification=args.license,
        notes=[args.note] if args.note else None,
    )
    print(f"Reference family ingested: {payload['reference_family_id']}")
    print(f"Catalog path: ~/.config/inkline/reference_catalog/{payload['reference_family_id']}")


def cmd_apply_curation(args: argparse.Namespace) -> None:
    try:
        from inkline.intelligence.reference_ingest import apply_curation_overrides
    except ImportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    payload = apply_curation_overrides(args.family)
    print(f"Curation applied: {payload['reference_family_id']}")
    print(f"Override log entries: {len(payload.get('override_log', []))}")


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
                    cmd_render(_args_for_watch_rerender(args))
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


def _bridge_url() -> str:
    return os.environ.get("INKLINE_BRIDGE_URL", "http://localhost:8082").rstrip("/") + "/"


def _args_for_watch_rerender(args: argparse.Namespace) -> argparse.Namespace:
    payload = dict(vars(args))
    payload["watch"] = False
    payload["serve"] = False
    return argparse.Namespace(**payload)


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
        matches = []
        for resource in resources:
            haystacks = [
                resource["uri"].lower(),
                resource.get("description", "").lower(),
            ]
            try:
                haystacks.append(read_resource(resource["uri"]).lower())
            except Exception:
                pass
            if any(query in haystack for haystack in haystacks):
                matches.append(resource)
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
        from inkline.app.institutional import audit_pdf_artifact
    except ImportError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"[inkline critique] Auditing {pdf_path.name} with rubric '{args.rubric}'...")
    try:
        result = audit_pdf_artifact(
            pdf_path=str(pdf_path),
            rubric=args.rubric,
            brand=args.brand,
        )
        import json as _json
        print(_json.dumps(result, indent=2))
    except Exception as exc:
        print(f"ERROR: critique failed: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_inspect_pptx(args: argparse.Namespace) -> None:
    from inkline.app.institutional import dump_json, inspect_pptx

    result = inspect_pptx(args.pptx)
    if args.out:
        dump_json(args.out, result)
    print(json.dumps(result, indent=2))


def cmd_audit_pptx(args: argparse.Namespace) -> None:
    from inkline.app.institutional import audit_pptx

    result = audit_pptx(
        args.pptx,
        rubric=args.rubric,
        brand=args.brand,
        output_path=args.out,
    )
    print(json.dumps(result, indent=2))
    if result.get("error"):
        sys.exit(21)


def cmd_compare_rendered(args: argparse.Namespace) -> None:
    from inkline.app.institutional import compare_rendered_pdfs

    slides = [item.strip() for item in args.slides.split(",") if item.strip()]
    result = compare_rendered_pdfs(
        args.baseline,
        args.pptx_render,
        slide_tokens=slides,
        output_path=args.out,
    )
    print(json.dumps(result, indent=2))


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
    setattr(args, "no_browser", getattr(args, "no_browser", False))
    cmd_serve(args)


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

    ingest_ref_p = sub.add_parser(
        "ingest-reference",
        help="Ingest a benchmark PPTX deck into the local reference-family catalog",
    )
    ingest_ref_p.add_argument("pptx", metavar="PPTX", help="Path to the PPTX file")
    ingest_ref_p.add_argument("--family", required=True, metavar="FAMILY",
                              help="Reference family identifier")
    ingest_ref_p.add_argument("--license", default="private_internal",
                              choices=["public_reusable", "public_reference_only", "private_internal", "client_confidential"],
                              help="License / confidentiality classification")
    ingest_ref_p.add_argument("--note", default="", metavar="TEXT",
                              help="Optional ingest note")
    ingest_ref_p.set_defaults(func=cmd_ingest_reference)

    curate_ref_p = sub.add_parser(
        "apply-curation",
        help="Apply local curation_overrides.yaml to a reference family",
    )
    curate_ref_p.add_argument("--family", required=True, metavar="FAMILY",
                              help="Reference family identifier")
    curate_ref_p.set_defaults(func=cmd_apply_curation)

    # inkline render
    render_p = sub.add_parser(
        "render",
        help="Render a markdown/YAML/JSON spec to PDF/PPTX (non-agentic; no Claude call)",
    )
    render_p.add_argument("file", metavar="FILE", help="Markdown, YAML, or JSON source file")
    render_p.add_argument("--output", default="pdf", metavar="FORMATS",
                          help="Comma-separated output formats: pdf,pptx (default: pdf)")
    render_p.add_argument("--output-dir", default="", metavar="DIR",
                          help="Override output directory")
    render_p.add_argument("--editable-institutional", action="store_true",
                          help="Enable the institutional editable PPTX path for YAML/JSON specs")
    render_p.add_argument("--brand", default="", metavar="BRAND",
                          help="Override brand from front-matter")
    render_p.add_argument("--template", default="", metavar="TEMPLATE",
                          help="Override template from front-matter")
    render_p.add_argument("--execution-mode", default="", choices=["draft", "explicit_spec"],
                          help="Execution contract: explicit_spec executes a locked spec; draft allows Inkline to invent structure")
    render_p.add_argument("--authoring-mode", default="", metavar="MODE",
                          help="Metadata only: upstream authoring source, e.g. external_llm")
    render_p.add_argument("--design-locked", dest="design_locked", action="store_true",
                          help="Metadata/contract: slide design was chosen upstream and must not be reinvented")
    render_p.add_argument("--no-design-locked", dest="design_locked", action="store_false",
                          help="Metadata/contract: slide design is not locked upstream")
    render_p.add_argument("--use-design-advisor", dest="use_design_advisor", action="store_true",
                          help="Allow Inkline authoring intelligence to invent/recommend structure")
    render_p.add_argument("--no-design-advisor", dest="use_design_advisor", action="store_false",
                          help="Disallow autonomous DesignAdvisor invention; execute the supplied structure only")
    render_p.set_defaults(design_locked=None, use_design_advisor=None)
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
    watch_p.add_argument("--execution-mode", default="", choices=["draft", "explicit_spec"])
    watch_p.add_argument("--authoring-mode", default="", metavar="MODE")
    watch_p.add_argument("--design-locked", dest="design_locked", action="store_true")
    watch_p.add_argument("--no-design-locked", dest="design_locked", action="store_false")
    watch_p.add_argument("--use-design-advisor", dest="use_design_advisor", action="store_true")
    watch_p.add_argument("--no-design-advisor", dest="use_design_advisor", action="store_false")
    watch_p.set_defaults(design_locked=None, use_design_advisor=None)
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

    # inkline inspect-pptx
    inspect_p = sub.add_parser(
        "inspect-pptx",
        help="Inspect a PPTX and emit editability / fallback metadata",
    )
    inspect_p.add_argument("pptx", metavar="PPTX", help="Path to the PPTX file")
    inspect_p.add_argument("--out", default="", metavar="JSON",
                           help="Optional JSON output path")
    inspect_p.set_defaults(func=cmd_inspect_pptx)

    # inkline audit-pptx
    audit_pptx_p = sub.add_parser(
        "audit-pptx",
        help="Render a PPTX through soffice and run post-render critique on the result",
    )
    audit_pptx_p.add_argument("pptx", metavar="PPTX", help="Path to the PPTX file")
    audit_pptx_p.add_argument("--rubric", default="institutional",
                              choices=["institutional", "tech_pitch", "internal_review"],
                              help="Audit rubric to apply")
    audit_pptx_p.add_argument("--brand", default="", metavar="BRAND",
                              help="Brand context for brand-aware critique")
    audit_pptx_p.add_argument("--out", default="", metavar="JSON",
                              help="Optional JSON output path")
    audit_pptx_p.set_defaults(func=cmd_audit_pptx)

    # inkline compare-rendered
    compare_p = sub.add_parser(
        "compare-rendered",
        help="Compare a baseline PDF and rendered PPTX PDF for parity",
    )
    compare_p.add_argument("--baseline", required=True, metavar="PDF",
                           help="Baseline PDF path")
    compare_p.add_argument("--pptx-render", required=True, metavar="PDF",
                           help="Rendered PPTX PDF path")
    compare_p.add_argument("--slides", required=True, metavar="SLIDES",
                           help="Comma-separated slide tokens or page numbers")
    compare_p.add_argument("--out", default="", metavar="JSON",
                           help="Optional JSON output path")
    compare_p.set_defaults(func=cmd_compare_rendered)

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
