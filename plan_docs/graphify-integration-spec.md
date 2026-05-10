# Graphify Integration Spec

## Problem

Inkline has accumulated enough surface area that first-pass repo navigation now
costs real time. New coding sessions have to rediscover the same structure
across:

- `src/inkline/`
- tests
- examples
- brand tooling
- execution-mode / bridge docs

## Goal

Add the same developer-facing `graphify` structure layer already adopted in
Aigis, without affecting the runtime or the public package behaviour.

## Scope

Add:

- `.graphifyignore`
- `scripts/graphify_refresh.sh`
- `docs/architecture/graphify-integration.md`
- committed `graphify-out/` outputs when generation succeeds

## Design

Graphify should focus on:

- `src/inkline/`
- `tests/`
- selected `examples/`
- durable docs/specs that explain the execution model

It should ignore:

- local virtualenvs
- output artefacts
- cache directories
- generated audits
- bulky private/public asset spillover not useful for code navigation

## Non-Goals

- No production dependency.
- No change to package metadata or render behaviour.

## Success Criteria

- Inkline gains a repeatable structural-graph refresh command.
- Graph artifacts are available for future coding sessions.
