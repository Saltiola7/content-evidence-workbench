import marimo

__generated_with = "0.23.15"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo

    from evidence_workbench import (
        MAX_UPLOAD_BYTES,
        ChunkConfig,
        DocumentValidationError,
        EvidenceSession,
        Judgments,
        LatentConfig,
        ReviewDecision,
        ReviewLedger,
        apply_review,
        build_entity_graph,
        chunk_documents,
        evaluate_retrieval,
        export_evidence,
        generate_corpus,
        parse_upload,
        retrieve_latent,
        retrieve_lexical,
    )

    mo.md(
        """
        # Content Evidence Workbench

        Compare deterministic lexical and latent retrieval over a clean-room
        synthetic corpus or one bounded visitor file. Every result retains its
        exact source text, character offsets, and SHA-256 citation.

        **Privacy:** visitor files remain only in the active notebook runtime.
        The workbench does not fetch source URLs, call providers, or persist
        uploaded content. Use the WASM build when browser-only execution is
        required.
        """
    )
    return (
        MAX_UPLOAD_BYTES,
        ChunkConfig,
        DocumentValidationError,
        EvidenceSession,
        Judgments,
        LatentConfig,
        ReviewDecision,
        ReviewLedger,
        apply_review,
        build_entity_graph,
        chunk_documents,
        evaluate_retrieval,
        export_evidence,
        generate_corpus,
        mo,
        parse_upload,
        retrieve_latent,
        retrieve_lexical,
    )


@app.cell
def _(MAX_UPLOAD_BYTES, mo):
    source_mode = mo.ui.radio(
        options={"Synthetic corpus": "synthetic", "Visitor file": "upload"},
        value="Synthetic corpus",
        inline=True,
        label="Corpus source",
    )
    visitor_file = mo.ui.file(
        filetypes=[".txt", ".md", ".markdown", ".csv", ".json"],
        kind="area",
        max_size=MAX_UPLOAD_BYTES,
        label="Upload one UTF-8 text, Markdown, CSV, or JSON file (maximum 5 MB)",
    )
    map_document_id = mo.ui.text(value="document_id", label="Document ID column")
    map_title = mo.ui.text(value="title", label="Title column")
    map_text = mo.ui.text(value="text", label="Text column")
    map_source_url = mo.ui.text(value="source_url", label="Source URL column (optional)")
    map_published_on = mo.ui.text(
        value="published_on",
        label="Published date column (optional)",
    )
    map_entities = mo.ui.text(value="entities", label="Entities column (optional)")
    mo.vstack(
        [
            source_mode,
            mo.md(
                "Structured files need explicit field mapping. Optional mappings "
                "may be cleared when the column is absent."
            ),
            visitor_file,
            mo.hstack(
                [map_document_id, map_title, map_text],
                widths="equal",
                wrap=True,
            ),
            mo.hstack(
                [map_source_url, map_published_on, map_entities],
                widths="equal",
                wrap=True,
            ),
        ]
    )
    return (
        map_document_id,
        map_entities,
        map_published_on,
        map_source_url,
        map_text,
        map_title,
        source_mode,
        visitor_file,
    )


@app.cell
def _(
    DocumentValidationError,
    generate_corpus,
    map_document_id,
    map_entities,
    map_published_on,
    map_source_url,
    map_text,
    map_title,
    parse_upload,
    source_mode,
    visitor_file,
):
    synthetic_fixture = generate_corpus(seed=2026, documents=24)
    active_corpus = synthetic_fixture.corpus
    active_fixture_id = synthetic_fixture.fixture_id
    corpus_ready = True
    corpus_message = (
        f"Loaded {len(active_corpus.documents)} deterministic synthetic documents "
        f"from seed {synthetic_fixture.seed}."
    )
    corpus_message_kind = "success"

    if source_mode.value == "upload":
        active_fixture_id = "visitor-runtime"
        if not visitor_file.value:
            corpus_ready = False
            corpus_message = "Choose a supported visitor file to start an in-memory session."
            corpus_message_kind = "warn"
        else:
            _uploaded = visitor_file.value[0]
            _mapping_values = {
                "document_id": map_document_id.value.strip(),
                "title": map_title.value.strip(),
                "text": map_text.value.strip(),
                "source_url": map_source_url.value.strip(),
                "published_on": map_published_on.value.strip(),
                "entities": map_entities.value.strip(),
            }
            _mapping = {key: value for key, value in _mapping_values.items() if value}
            try:
                active_corpus = parse_upload(
                    _uploaded.name,
                    _uploaded.contents,
                    mapping=_mapping,
                )
                active_fixture_id = "visitor-runtime"
                corpus_message = (
                    f"Validated {len(active_corpus.documents)} visitor documents "
                    "for this runtime-only session."
                )
            except DocumentValidationError as _error:
                corpus_ready = False
                corpus_message = f"Validation stopped ({_error.code}): {_error}"
                corpus_message_kind = "danger"

    return (
        active_corpus,
        active_fixture_id,
        corpus_message,
        corpus_message_kind,
        corpus_ready,
        synthetic_fixture,
    )


@app.cell
def _(corpus_message, corpus_message_kind, mo):
    mo.callout(corpus_message, kind=corpus_message_kind)
    return


@app.cell
def _(ChunkConfig, active_corpus, build_entity_graph, chunk_documents, corpus_ready):
    active_chunks = (
        chunk_documents(
            active_corpus,
            ChunkConfig(max_chars=480, overlap_chars=80),
        )
        if corpus_ready
        else None
    )
    entity_graph = build_entity_graph(active_chunks) if active_chunks is not None else None
    return active_chunks, entity_graph


@app.cell
def _(mo):
    query_control = mo.ui.text(
        value="citation retention policy",
        placeholder="Describe the evidence you need",
        label="Evidence query",
        full_width=True,
    )
    limit_control = mo.ui.slider(
        start=1,
        stop=12,
        step=1,
        value=5,
        show_value=True,
        include_input=True,
        label="Top results per method",
    )
    latent_dimensions = mo.ui.slider(
        start=1,
        stop=16,
        step=1,
        value=8,
        show_value=True,
        include_input=True,
        label="Latent dimensions",
    )
    mo.hstack(
        [query_control, limit_control, latent_dimensions],
        widths=[3, 1, 1],
        align="end",
        wrap=True,
    )
    return latent_dimensions, limit_control, query_control


@app.cell
def _(
    Judgments,
    LatentConfig,
    active_chunks,
    corpus_ready,
    evaluate_retrieval,
    latent_dimensions,
    limit_control,
    query_control,
    retrieve_latent,
    retrieve_lexical,
):
    if corpus_ready and active_chunks is not None:
        lexical_result = retrieve_lexical(
            active_chunks,
            query_control.value,
            limit=int(limit_control.value),
        )
        latent_result = retrieve_latent(
            active_chunks,
            query_control.value,
            LatentConfig(
                dimensions=int(latent_dimensions.value),
                seed=2026,
                limit=int(limit_control.value),
            ),
        )
        unjudged = Judgments(by_query={})
        lexical_evaluation = evaluate_retrieval(lexical_result, unjudged)
        latent_evaluation = evaluate_retrieval(latent_result, unjudged)
    else:
        lexical_result = None
        latent_result = None
        lexical_evaluation = None
        latent_evaluation = None
    return (
        latent_evaluation,
        latent_result,
        lexical_evaluation,
        lexical_result,
    )


@app.cell
def _(latent_result, lexical_result, mo):
    def _rows(result):
        if result is None:
            return []
        return [
            {
                "method": result.method,
                "rank": item.rank,
                "score": round(item.score, 6),
                "score_label": item.score_label,
                "title": item.citation.title,
                "document_id": item.citation.document_id,
                "offsets": f"{item.citation.start_offset}:{item.citation.end_offset}",
                "content_sha256": item.citation.content_sha256,
                "matched_terms": ", ".join(item.matched_terms),
                "entities": ", ".join(item.related_entities),
                "exact_source_text": item.citation.text,
            }
            for item in result.items
        ]

    lexical_rows = _rows(lexical_result)
    latent_rows = _rows(latent_result)
    lexical_status = lexical_result.status if lexical_result is not None else "waiting_for_corpus"
    latent_status = latent_result.status if latent_result is not None else "waiting_for_corpus"

    def _evidence_table(rows, label):
        if not rows:
            return mo.md("*No evidence is available for this method and query.*")
        return mo.ui.table(
            rows,
            selection="single",
            page_size=6,
            wrapped_columns=["exact_source_text"],
            show_download=False,
            label=label,
        )

    mo.vstack(
        [
            mo.md(
                "## Ranked evidence\n\n"
                "Scores are method-specific and are not directly comparable across columns."
            ),
            mo.hstack(
                [
                    mo.vstack(
                        [
                            mo.md(f"### Lexical · `{lexical_status}`"),
                            _evidence_table(
                                lexical_rows,
                                "Lexical evidence with exact citations",
                            ),
                        ]
                    ),
                    mo.vstack(
                        [
                            mo.md(f"### Latent semantic · `{latent_status}`"),
                            _evidence_table(
                                latent_rows,
                                "Latent evidence with exact citations",
                            ),
                        ]
                    ),
                ],
                widths="equal",
                align="start",
                wrap=True,
            ),
        ]
    )
    return latent_rows, lexical_rows


@app.cell
def _(ReviewLedger, mo):
    ledger_state, set_ledger = mo.state(ReviewLedger())
    return ledger_state, set_ledger


@app.cell
def _(
    ReviewDecision,
    apply_review,
    latent_result,
    ledger_state,
    lexical_result,
    mo,
    set_ledger,
):
    _results = {
        result.method: result for result in (lexical_result, latent_result) if result is not None
    }
    _evidence_options = {
        f"{result.method.title()} #{item.rank} · {item.citation.title}": (
            f"{result.method}|{item.evidence_id}"
        )
        for result in _results.values()
        for item in result.items
    }
    if not _evidence_options:
        _evidence_options = {"No evidence available": ""}

    review_evidence = mo.ui.dropdown(
        options=_evidence_options,
        value=next(iter(_evidence_options)),
        label="Evidence",
        full_width=True,
        disabled=not bool(_results),
    )
    review_action = mo.ui.dropdown(
        options={
            "Accept": "accept",
            "Reject": "reject",
            "Annotate": "annotate",
            "Defer": "defer",
            "Reorder": "reorder",
        },
        value="Accept",
        label="Decision",
    )
    review_note = mo.ui.text_area(
        label="Review note",
        placeholder="Why does this evidence support, weaken, or defer the claim?",
        max_length=2000,
        rows=3,
        full_width=True,
    )
    review_rank = mo.ui.number(
        start=1,
        stop=max((len(result.items) for result in _results.values()), default=1),
        step=1,
        value=1,
        label="Resulting rank (used for reorder)",
    )

    def _append_review(_value):
        _selection = review_evidence.value
        if not _selection:
            return ledger_state()
        _method, _evidence_id = _selection.split("|", 1)
        _result = _results[_method]
        _resulting_rank = int(review_rank.value) if review_action.value == "reorder" else None
        _updated = apply_review(
            _result,
            ReviewDecision(
                query_id=_result.query_id,
                evidence_id=_evidence_id,
                action=review_action.value,
                note=review_note.value.strip() or None,
                resulting_rank=_resulting_rank,
            ),
            ledger=ledger_state(),
        )
        set_ledger(_updated)
        return _updated

    append_review_button = mo.ui.button(
        label="Append review decision",
        kind="success",
        disabled=not bool(_results),
        on_click=_append_review,
    )
    mo.vstack(
        [
            mo.md(
                "## Human review ledger\n\n"
                "Each click appends a decision and snapshots the untouched citation."
            ),
            review_evidence,
            mo.hstack([review_action, review_rank], justify="start", wrap=True),
            review_note,
            append_review_button,
        ]
    )
    return (
        append_review_button,
        review_action,
        review_evidence,
        review_note,
        review_rank,
    )


@app.cell
def _(ledger_state, mo):
    review_rows = [
        {
            "sequence": entry.sequence,
            "action": entry.action,
            "prior_rank": entry.prior_rank,
            "resulting_rank": entry.resulting_rank,
            "title": entry.citation.title,
            "offsets": f"{entry.citation.start_offset}:{entry.citation.end_offset}",
            "content_sha256": entry.citation.content_sha256,
            "note": entry.note or "",
            "exact_source_text": entry.citation.text,
        }
        for entry in ledger_state().entries
    ]
    _review_display = (
        mo.ui.table(
            review_rows,
            selection=None,
            page_size=6,
            wrapped_columns=["note", "exact_source_text"],
            show_download=False,
            label="Append-only review decisions",
        )
        if review_rows
        else mo.md("*No review decisions have been recorded in this session.*")
    )
    mo.vstack([_review_display])
    return (review_rows,)


@app.cell
def _(entity_graph, mo):
    entity_rows = (
        [
            {
                "source": edge.source,
                "target": edge.target,
                "shared_chunks": edge.weight,
                "chunk_ids": ", ".join(edge.chunk_ids),
            }
            for edge in entity_graph.edges
        ]
        if entity_graph is not None
        else []
    )
    mo.vstack(
        [
            mo.md(
                "## Entity context\n\n"
                "Edges are deterministic co-occurrences of declared entity labels."
            ),
            mo.ui.table(
                entity_rows,
                selection=None,
                page_size=8,
                show_download=False,
                label="Entity co-occurrence graph",
            ),
        ]
    )
    return (entity_rows,)


@app.cell
def _(latent_evaluation, lexical_evaluation, mo):
    _evaluations = [
        evaluation
        for evaluation in (lexical_evaluation, latent_evaluation)
        if evaluation is not None
    ]
    metric_rows = [
        {
            "method": method,
            "available": evaluation.available,
            "reason": evaluation.reason or "",
        }
        for method, evaluation in zip(("lexical", "latent"), _evaluations, strict=False)
    ]
    mo.vstack(
        [
            mo.md(
                "## Evaluation\n\n"
                "Metrics remain unavailable until separately supplied judgments identify "
                "the exact query and chunk identities."
            ),
            mo.ui.table(
                metric_rows,
                selection=None,
                show_download=False,
                label="Judgment-gated retrieval metrics",
            ),
        ]
    )
    return (metric_rows,)


@app.cell
def _(
    EvidenceSession,
    active_fixture_id,
    export_evidence,
    latent_evaluation,
    latent_result,
    ledger_state,
    lexical_evaluation,
    lexical_result,
):
    session_results = tuple(
        result for result in (lexical_result, latent_result) if result is not None
    )
    session_evaluations = tuple(
        evaluation
        for evaluation in (lexical_evaluation, latent_evaluation)
        if evaluation is not None
    )
    evidence_session = EvidenceSession(
        results=session_results,
        ledger=ledger_state(),
        evaluations=session_evaluations,
        configuration={
            "synthetic_seed": 2026,
            "network_calls": False,
            "persistence": False,
        },
        fixture_id=active_fixture_id,
    )
    export_bundle = export_evidence(evidence_session)
    return evidence_session, export_bundle


@app.cell
def _(export_bundle, mo):
    mo.vstack(
        [
            mo.md(f"## Safe exports\n\nBundle SHA-256: `{export_bundle.bundle_sha256}`"),
            mo.hstack(
                [
                    mo.download(
                        export_bundle.json_text,
                        filename="evidence-session.json",
                        mimetype="application/json",
                        label="Download JSON evidence packet",
                    ),
                    mo.download(
                        export_bundle.evidence_csv,
                        filename="evidence-results.csv",
                        mimetype="text/csv",
                        label="Download formula-safe evidence CSV",
                    ),
                    mo.download(
                        export_bundle.review_csv,
                        filename="evidence-review-ledger.csv",
                        mimetype="text/csv",
                        label="Download formula-safe review CSV",
                    ),
                ],
                justify="start",
                wrap=True,
            ),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
