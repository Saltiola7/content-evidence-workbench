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
- 28 focused tests, strict Marimo validation, and a locked environment

No employer source, SaaS Pegasus code, premium UI assets, client data, or
owner-funded API calls are included. See [CLEAN_ROOM.md](CLEAN_ROOM.md).

## Run locally

```bash
uv sync
uv run pytest -q
uv run marimo edit app.py
```

Visitor uploads remain only in the active notebook runtime. The deterministic
path performs no network calls, source-URL fetches, model calls, or persistence.
Use the future WASM build when browser-only processing is required.

## Validation

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run marimo check --strict app.py
```

Status: reviewed local MVP. GitHub Pages, Molab, accessibility, and browser
release validation remain intentionally pending.

## License

MIT. Public fixture provenance remains separately documented.
