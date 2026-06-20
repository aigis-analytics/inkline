---
domain: workflow
audience: [institutional, operator]
slide_type_relevance: []
brand_affinity: [institutional_finance]
version: 1.0.0
last_updated: 2026-06-20
description: How benchmark PPTX decks are ingested into Inkline reference families.
---

# Reference Deck Ingestion

MVP rules:

- `PPTX` only
- local/private catalog first
- operator curation via `curation_overrides.yaml`
- no confidential previews or manifests in the public repo

CLI:

```bash
inkline ingest-reference benchmark.pptx --family ccc_angola_focus_v1
inkline apply-curation --family ccc_angola_focus_v1
```

Catalog roots:

- packaged: `src/inkline/intelligence/reference_catalog/`
- local/private: `~/.config/inkline/reference_catalog/`
