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
- Private brands load from `~/.config/inkline/`; sync that repo separately when
  brand changes are made.
- Typst is the default backend.
- Keep the main PC and `k1mini` clones aligned after changes.
- Prefer Inkline itself for presentation/report output rather than custom
  one-off generation code.
