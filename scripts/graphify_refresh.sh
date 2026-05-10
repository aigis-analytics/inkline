#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"

if ! command -v graphify >/dev/null 2>&1; then
  echo "graphify not found. Install with: pipx install graphifyy" >&2
  exit 1
fi

cd "$ROOT"

if [ ! -f ".graphifyignore" ]; then
  echo ".graphifyignore not found in $(pwd)" >&2
  exit 1
fi

echo "Building structural graph..."
graphify update .

if [ ! -f "graphify-out/graph.json" ]; then
  echo "graphify-out/graph.json was not created" >&2
  exit 1
fi

echo "Generating report and HTML views..."
graphify cluster-only .
graphify tree \
  --graph graphify-out/graph.json \
  --output graphify-out/GRAPH_TREE.html \
  --root "$(pwd)" \
  --label "Inkline"

echo
echo "Graphify refresh complete."
echo "Key artifacts:"
echo "  graphify-out/GRAPH_REPORT.md"
echo "  graphify-out/GRAPH_TREE.html"
echo "  graphify-out/graph.json"
if [ -f "graphify-out/graph.html" ]; then
  echo "  graphify-out/graph.html"
fi
