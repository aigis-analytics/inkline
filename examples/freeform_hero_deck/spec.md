---
brand: minimal
template: consulting
title: Technology Architecture Overview
date: April 2026
output: [pdf]
audit: post-render
---

## Platform Overview
<!-- _layout: content -->
Our platform processes 36 months of account history through a temporal AI model
to generate continuous risk scores — not point-in-time snapshots.

Key components:
- Data ingestion layer (real-time + batch)
- Feature engineering pipeline (200+ derived features)
- CNN+BiLSTM temporal model (patent pending)
- Explainability engine (SHAP-based attribution)
- Delivery API (REST + Kafka)

## System Architecture
<!-- _layout: freeform
_shapes_file: shapes/architecture_diagram.json -->

## Data Flow
<!-- _layout: process_flow -->
- title: Ingest
  description: Pull from credit bureau, transaction, macro feeds via secure API
- title: Transform
  description: Normalise, derive 200+ temporal features, handle missing data
- title: Score
  description: Run CNN+BiLSTM inference — 50ms p99 latency
- title: Explain
  description: Generate SHAP attributions and natural language narrative
- title: Deliver
  description: Push to client API or Kafka topic with full audit trail

## Performance Metrics
<!-- _layout: stat -->
- value: 94.99%
  label: Model accuracy (held-out test set)
  delta: +3.2pp vs. logistic regression baseline
- value: 50ms
  label: P99 inference latency
- value: 18 months
  label: Early warning horizon
