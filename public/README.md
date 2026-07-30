# Public runtime assets

The public workbench generates its demonstration corpus at runtime with:

- generator: `evidence_workbench.synthetic.generate_corpus`
- seed: `2026`
- document count: `24`
- generated date: `2026-07-29`
- fixture license: `CC0-1.0`

No visitor, employer, client, or external source material is bundled here.
Visitor uploads are bounded, processed in the active session, and excluded from
committed assets. Release builds must record the exact repository commit
identity. The synthetic-only static session is committed beside
`src/app.py`; CI rebuilds and browser-tests the WASM artifact.
