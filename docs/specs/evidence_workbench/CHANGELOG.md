---
title: Content Evidence Workbench Changelog
---

# Changelog

## 2026-07-29 - Product specification

- Defined deterministic document validation, chunking, retrieval comparison,
  citations, entity context, review, evaluation, and export journeys.
- Required bounded runtime-only visitor data and exact citation preservation.
- Prohibited employer and licensed SaaS source and evidence.
- Deferred BYOK, generated synthesis, persistence, crawling, and production
  adapters.

## 2026-07-29 - Local deterministic MVP

- Added bounded document validation, deterministic chunking, TF-IDF and LSA
  retrieval, exact citations, entity graph, judged metrics, append-only review,
  and evidence exports.
- Added the thin Marimo workbench with synthetic and runtime-only upload paths.
- Bound query identity to corpus identity, bounded entity expansion, required
  phrase-boundary entity matches, and neutralized spreadsheet control prefixes
  after independent review.
- Passed 28 focused tests, curated Ruff checks, strict Marimo validation, and
  executable HTML export.
