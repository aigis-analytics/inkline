# Manual QA Checklist — Institutional Editable PPTX

Fixture:
Reviewer:
Date:

## Core Checks

- [ ] PPTX opens in LibreOffice on `k1mini`
- [ ] Rendered PPTX PDF was generated via `soffice`
- [ ] `audit.json` present
- [ ] `export_metadata.json` present
- [ ] `parity_report.json` present

## Editability Script

- [ ] `cover` edited and reopened without overlap
- [ ] `team_grid` edited and reopened without card breakage
- [ ] `institutional_kpi_cards` edited and reopened without overflow
- [ ] `institutional_timeline` edited and reopened without collisions
- [ ] `appendix_matrix` edited and reopened without clipping

## Evidence

- [ ] Edited proof deck saved as `manual_editability_check.pptx`
- [ ] One screenshot per edited family saved under `manual_qa_screens/`

## Result

- [ ] `engineering_signoff` pass
- [ ] `production_ship_ready` pass

Notes:
