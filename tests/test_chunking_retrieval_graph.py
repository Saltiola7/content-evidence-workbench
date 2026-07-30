from __future__ import annotations

from dataclasses import asdict
from hashlib import sha256

import pytest

from evidence_workbench import (
    MAX_CHUNKS,
    ChunkConfig,
    LatentConfig,
    build_entity_graph,
    chunk_documents,
    retrieve_latent,
    retrieve_lexical,
    validate_documents,
)


def test_chunking_is_deterministic_loss_aware_and_citation_exact(
    document_records: list[dict[str, object]],
) -> None:
    corpus = validate_documents(document_records)
    config = ChunkConfig(max_chars=72, overlap_chars=16)

    first = chunk_documents(corpus, config)
    second = chunk_documents(corpus, config)

    assert first == second
    assert first.corpus_digest == second.corpus_digest
    assert len({chunk.chunk_id for chunk in first.chunks}) == len(first.chunks)

    by_id = {document.document_id: document for document in corpus.documents}
    covered: dict[str, set[int]] = {document.document_id: set() for document in corpus.documents}
    for chunk in first.chunks:
        source = by_id[chunk.document_id]
        assert chunk.text == source.text[chunk.start_offset : chunk.end_offset]
        assert chunk.content_sha256 == sha256(chunk.text.encode("utf-8")).hexdigest()
        assert chunk.chunk_id.startswith(f"{chunk.document_id}:")
        assert 0 <= chunk.start_offset < chunk.end_offset <= len(source.text)
        covered[chunk.document_id].update(range(chunk.start_offset, chunk.end_offset))

    for document in corpus.documents:
        assert covered[document.document_id] == set(range(len(document.text)))


def test_chunking_enforces_public_chunk_bound() -> None:
    corpus = validate_documents(
        [
            {
                "document_id": "bounded",
                "title": "Bounded",
                "text": "x" * ((MAX_CHUNKS + 32) * 32),
            }
        ]
    )

    with pytest.raises(ValueError, match="chunk limit"):
        chunk_documents(corpus, ChunkConfig(max_chars=32, overlap_chars=31))


def test_lexical_and_latent_results_share_inventory_but_label_scores(
    document_records: list[dict[str, object]],
) -> None:
    chunks = chunk_documents(
        validate_documents(document_records),
        ChunkConfig(max_chars=220, overlap_chars=24),
    )

    lexical = retrieve_lexical(chunks, "retention source citations", limit=3)
    latent = retrieve_latent(
        chunks,
        "retention source citations",
        LatentConfig(dimensions=2, seed=2026, limit=3),
    )

    assert lexical.status == "ok"
    assert latent.status == "ok"
    assert lexical.corpus_digest == latent.corpus_digest == chunks.corpus_digest
    assert lexical.method == "lexical"
    assert latent.method == "latent"
    assert lexical.items[0].citation.document_id.startswith("aster-")
    assert latent.items[0].citation.document_id.startswith("aster-")
    assert lexical.items[0].score_label == "tfidf_cosine"
    assert latent.items[0].score_label == "lsa_cosine"
    assert lexical.configuration != latent.configuration

    lexical_citations = [asdict(item.citation) for item in lexical.items]
    repeated = retrieve_lexical(chunks, "retention source citations", limit=3)
    assert repeated == lexical
    assert [asdict(item.citation) for item in repeated.items] == lexical_citations


def test_query_identity_is_bound_to_the_active_corpus() -> None:
    first_chunks = chunk_documents(
        validate_documents(
            [{"document_id": "first", "title": "First", "text": "retention evidence"}]
        ),
        ChunkConfig(),
    )
    second_chunks = chunk_documents(
        validate_documents(
            [{"document_id": "second", "title": "Second", "text": "retention evidence changed"}]
        ),
        ChunkConfig(),
    )

    first = retrieve_lexical(first_chunks, "retention", limit=1)
    second = retrieve_lexical(second_chunks, "retention", limit=1)

    assert first.query_id != second.query_id


def test_empty_and_no_match_states_are_explicit(
    document_records: list[dict[str, object]],
) -> None:
    chunks = chunk_documents(validate_documents(document_records), ChunkConfig())

    empty = retrieve_lexical(chunks, "   ", limit=5)
    no_match = retrieve_latent(
        chunks,
        "quasarxylophone",
        LatentConfig(dimensions=2, seed=2026, limit=5),
    )

    assert empty.status == "empty_query"
    assert empty.items == ()
    assert no_match.status == "no_match"
    assert no_match.items == ()


def test_retrieval_rejects_invalid_limits(
    document_records: list[dict[str, object]],
) -> None:
    chunks = chunk_documents(validate_documents(document_records), ChunkConfig())

    with pytest.raises(ValueError, match="limit"):
        retrieve_lexical(chunks, "retention", limit=0)
    with pytest.raises(ValueError, match="limit"):
        retrieve_latent(chunks, "retention", LatentConfig(limit=0))


def test_entity_graph_uses_declared_entities_and_deterministic_cooccurrence(
    document_records: list[dict[str, object]],
) -> None:
    chunks = chunk_documents(
        validate_documents(document_records),
        ChunkConfig(max_chars=220, overlap_chars=0),
    )

    graph = build_entity_graph(chunks)

    assert graph.nodes == tuple(sorted(graph.nodes))
    assert "Aster Labs" in graph.nodes
    assert "Retention Console" in graph.nodes
    edge = next(
        edge
        for edge in graph.edges
        if {edge.source, edge.target} == {"Aster Labs", "Retention Console"}
    )
    assert edge.weight == 2
    assert len(edge.chunk_ids) == 2
    assert all(
        chunk_id in {chunk.chunk_id for chunk in chunks.chunks} for chunk_id in edge.chunk_ids
    )


def test_entity_matching_uses_phrase_boundaries_not_substrings() -> None:
    chunks = chunk_documents(
        validate_documents(
            [
                {
                    "document_id": "boundary",
                    "title": "Boundary",
                    "text": "The chair remains beside the table.",
                    "entities": ["AI"],
                }
            ]
        ),
        ChunkConfig(),
    )

    graph = build_entity_graph(chunks)

    assert graph.nodes == ()
