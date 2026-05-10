# Graphify Integration

## Goal

Use `graphify` as a lightweight structure map for Inkline so future coding
sessions can navigate the package, tests, examples, and execution-mode docs
without re-exploring the same topology.

Graphify is developer tooling only.

## Recommended Scope

### Include

- `src/inkline/`
- `tests/`
- selected `examples/`
- durable docs/specs relevant to the execution model

### Exclude

- output artefacts
- caches and virtualenvs
- bulky generated audit folders
- large support assets that do not help with code navigation

## Output Contract

Commit lightweight artifacts when available:

- `graphify-out/GRAPH_REPORT.md`
- `graphify-out/graph.json`
- `graphify-out/GRAPH_TREE.html`
- `graphify-out/graph.html` when generated

## Refresh

From the repo root:

```bash
./scripts/graphify_refresh.sh
```
