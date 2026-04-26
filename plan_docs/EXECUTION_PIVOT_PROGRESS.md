# Execution Engine + Knowledge Base Pivot — Progress

| Phase | Commit | Tests | Status | Notes |
|---|---|---|---|---|
| Phase 1 — Documentation + default-mode flip | 7e06c27 | 400 passed (+15 new) | COMPLETE | audit: post-render directive; _mode defaults to exact when _layout specified; /health modes object; CLAUDE.md + README.md restructured |
| Phase 2 — freeform slide_type + image strategy | a979992 | 453 passed (+53 new) | COMPLETE | image_strategy.py (3 strategies, loud failures); freeform.py (8 shape types); Typst + PPTX renderers; backend_coverage updated |
| Phase 3 — Knowledge base as MCP resources | 00325c5 | 522 passed (+69 new) | COMPLETE | mcp_resources.py (13 URI dispatch); 9 playbooks front-matter migrated; MCP tools (render_spec, validate_spec, critique_pdf, get_capacity, list_brands); /knowledge/* HTTP proxies; /critique endpoint; CLI (knowledge, validate, critique, draft) |
| Phase 4 — Vishwakarma as post-render critique | d59e516 | 540 passed (+18 new) | COMPLETE | critique_pdf() + CritiqueResult + SlideCritique dataclasses; 3 rubrics; mocked vision_fn for tests; /critique endpoint wired to new function; inkline_critique_pdf MCP tool |
| Phase 5 — Examples, migration docs, draft-mode labelling | 3606184 | 540 passed (+0 new) | COMPLETE | 3 example decks (typed_layout, freeform_hero, hybrid); MIGRATION.md; Draft Mode docstrings on design_advisor/plan_auditor/visual_direction; CLAUDE.md execute-mode at line 33 |
