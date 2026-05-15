# Inkline Codex Guide

## Scope

Use this repo for Inkline development: Typst rendering, slides, charts, brand
system, and document-generation tooling.

## Repo Locations

- Main PC repo: `/mnt/d/inkline`
- K1Mini clone: `/home/k1mini/inkline`
- Private brands: `~/.config/inkline/`

## Operating Rules

- This is a public repo. Do not commit proprietary brand data, private assets,
  secrets, or internal-only references.
- For project-context loading, check `graphify-out/GRAPH_REPORT.md` first when
  present. Treat it as the fast structural map before broad source traversal.
- Private brands load from `~/.config/inkline/`; sync that repo separately when
  brand changes are made.
- Typst is the default backend.
- Keep the main PC and `k1mini` clones aligned after changes.
- Prefer Inkline itself for presentation/report output rather than custom
  one-off generation code.

## Visual Audit Rules

- Treat post-render visual audit as a hard gate for investor, board, PE, or
  client-facing decks. A skipped or unavailable vision audit is not a pass.
- Use the live bridge URL explicitly when auditing if the bridge is not on the
  default port, e.g. `INKLINE_BRIDGE_URL=http://localhost:8083`.
- Prefer a resilient backend path: Claude if available, Gemini CLI fallback
  when Claude is rate-limited, and surface the exact provider failure in logs.
- For Gemini vision, images must live in a Gemini-readable workspace such as
  `~/.gemini/tmp/inkline/vision_uploads`; do not assume it can read
  `~/.local/share/inkline/output/vision_uploads`.
- Deck sign-off requires looking at the rendered PDF/PPTX, not only successful
  compilation. Watch for clipped exhibits, excessive whitespace, neutral titles,
  single-chart slides where multi-exhibit layouts are expected, and content
  slides where cards/infographics would carry the message better.
