---
title: Content Evidence Workbench Backlog
status: active
last_updated: 2026-07-29
---

# Backlog

| id | title | priority | status | depends_on | owns | reads | parallel_safe | reason | effort | validation |
|---|---|---|---|---|---|---|---|---|---|---|
| CEW-001 | Commit product intent, domain, behavior, contracts, and cycle plan | P0 | completed | - | product specs and policy | approved portfolio Discovery | no | Clean authority precedes code | S | Spec checks pass |
| CEW-002 | Write red domain and security tests | P0 | ready | CEW-001 | `tests/` | product spec | no | Behavior evidence precedes implementation | M | Tests fail for missing package |
| CEW-003 | Implement deterministic domain package and synthetic corpus | P0 | pending | CEW-002 | `src/evidence_workbench/`, `public/` | red tests | no | Core works without APIs | L | Focused pytest and Ruff pass |
| CEW-004 | Build thin Marimo workbench | P0 | pending | CEW-003 | `app.py` | validated package | no | Browser demo exposes core journey | L | Strict Marimo and import smoke pass |
| CEW-005 | Add evidence exports, documentation, and reference provenance | P1 | pending | CEW-004 | docs and reference outputs | validated sessions | yes | Retrieval claims need traceable evidence | M | Export and provenance gates pass |
| CEW-006 | Add CI, WASM export, and browser validation | P0 | pending | CEW-004 | manifests and workflows | validation commands | no | Release needs reproducible authority | M | CI and local export pass |
| CEW-007 | Prepare public repository and deployment release | P0 | pending | CEW-005, CEW-006 | release evidence | exact source SHA | no | External publication follows review | S | Release, Pages, and Molab gates pass |

