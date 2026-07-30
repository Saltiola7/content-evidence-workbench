# Content Evidence Workbench

Interactive clean-room workbench for deterministic content retrieval, exact
citations, entity context, judged evaluation, and human evidence review.

The local MVP includes:

- deterministic fictional corpus and bounded text, Markdown, CSV, or JSON upload
- lexical TF-IDF and latent-semantic retrieval over the same chunk inventory
- exact source text, character offsets, identities, and SHA-256 citations
- declared-entity co-occurrence graph with bounded expansion
- judgment-gated precision at k, recall at k, MRR, nDCG, and coverage
- append-only accept, reject, annotate, defer, and reorder decisions
- citation-preserving JSON plus spreadsheet-safe CSV evidence exports
- 30 focused tests, strict Marimo validation, an executable WASM export, and a
  locked environment

No employer source, SaaS Pegasus code, premium UI assets, client data, or
owner-funded API calls are included. See [CLEAN_ROOM.md](CLEAN_ROOM.md).

## Run locally

```bash
uv sync
uv run pytest -q
uv run marimo edit src/app.py
```

Visitor uploads remain only in the active notebook runtime. The deterministic
path performs no network calls, source-URL fetches, model calls, or persistence.
Use the Pages or Molab WASM build when browser-only processing is required.

## Validation

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run marimo check --strict src/app.py
uv run marimo export html-wasm src/app.py --output /tmp/cew-site --execute
uv run python scripts/validate_wasm_export.py /tmp/cew-site
```

The committed static snapshot contains synthetic output only. CI rebuilds it,
packages the importable local library, exercises query recomputation in
Chromium, scans critical vulnerabilities, emits an SPDX SBOM, and deploys the
same WASM artifact to GitHub Pages.

Status: release candidate. Local browser interaction passes; public GitHub,
Pages, and Molab URLs remain pending until repository publication.

## License

MIT. Public fixture provenance remains separately documented.
