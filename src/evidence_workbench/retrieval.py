"""Deterministic lexical and latent-semantic retrieval."""

from __future__ import annotations

from collections.abc import Sequence
from math import isfinite

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from .domain import (
    Chunk,
    ChunkCorpus,
    Citation,
    EvidenceItem,
    LatentConfig,
    RetrievalMethod,
    RetrievalResult,
    RetrievalStatus,
)
from .text import normalize_text, stable_hash


def _query_id(chunks: ChunkCorpus, query: str) -> str:
    return stable_hash(chunks.corpus_digest, normalize_text(query))[:20]


def _empty_result(
    chunks: ChunkCorpus,
    query: str,
    method: RetrievalMethod,
    limit: int,
    status: RetrievalStatus,
    configuration: tuple[tuple[str, str | int | float], ...],
) -> RetrievalResult:
    normalized_query = normalize_text(query)
    return RetrievalResult(
        query=query,
        query_id=_query_id(chunks, normalized_query),
        method=method,
        status=status,
        limit=limit,
        corpus_digest=chunks.corpus_digest,
        configuration=configuration,
    )


def _citation(chunk: Chunk) -> Citation:
    return Citation(
        document_id=chunk.document_id,
        title=chunk.title,
        source_url=chunk.source_url,
        published_on=chunk.published_on,
        chunk_id=chunk.chunk_id,
        start_offset=chunk.start_offset,
        end_offset=chunk.end_offset,
        content_sha256=chunk.content_sha256,
        text=chunk.text,
    )


def _rank_items(
    *,
    chunks: ChunkCorpus,
    query: str,
    method: RetrievalMethod,
    scores: Sequence[float],
    limit: int,
    score_label: str,
    explanation: str,
    matched_terms: Sequence[tuple[str, ...]] | None = None,
) -> tuple[EvidenceItem, ...]:
    query_id = _query_id(chunks, query)
    candidates = [
        (index, float(score))
        for index, score in enumerate(scores)
        if isfinite(float(score)) and float(score) > 1e-12
    ]
    ordered = sorted(
        candidates,
        key=lambda pair: (-round(pair[1], 15), chunks.chunks[pair[0]].chunk_id),
    )
    items: list[EvidenceItem] = []
    for rank, (index, score) in enumerate(ordered[:limit], start=1):
        chunk = chunks.chunks[index]
        items.append(
            EvidenceItem(
                evidence_id=stable_hash(method, query_id, chunk.chunk_id)[:24],
                rank=rank,
                score=score,
                score_label=score_label,
                explanation=explanation,
                citation=_citation(chunk),
                matched_terms=matched_terms[index] if matched_terms is not None else (),
                related_entities=chunk.entities,
            )
        )
    return tuple(items)


def retrieve_lexical(chunks: ChunkCorpus, query: str, limit: int) -> RetrievalResult:
    """Rank active chunks by TF-IDF cosine similarity."""
    if limit < 1:
        raise ValueError("limit must be positive")
    configuration: tuple[tuple[str, str | int | float], ...] = (
        ("analyzer", "word"),
        ("ngram_max", 2),
        ("sublinear_tf", 1),
    )
    normalized_query = normalize_text(query)
    if not normalized_query:
        return _empty_result(chunks, query, "lexical", limit, "empty_query", configuration)
    if not chunks.chunks:
        return _empty_result(chunks, query, "lexical", limit, "no_match", configuration)

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    try:
        document_matrix = vectorizer.fit_transform(chunk.normalized_text for chunk in chunks.chunks)
    except ValueError:
        return _empty_result(chunks, query, "lexical", limit, "no_match", configuration)
    query_vector = vectorizer.transform([normalized_query])
    if query_vector.nnz == 0:
        return _empty_result(chunks, query, "lexical", limit, "no_match", configuration)
    scores = (document_matrix @ query_vector.T).toarray().ravel()
    analyzer = vectorizer.build_analyzer()
    query_terms = set(analyzer(normalized_query))
    matches = tuple(
        tuple(sorted(query_terms.intersection(analyzer(chunk.normalized_text))))
        for chunk in chunks.chunks
    )
    items = _rank_items(
        chunks=chunks,
        query=query,
        method="lexical",
        scores=scores,
        limit=limit,
        score_label="tfidf_cosine",
        explanation="Cosine similarity in a corpus-fitted TF-IDF word and bigram space.",
        matched_terms=matches,
    )
    return RetrievalResult(
        query=query,
        query_id=_query_id(chunks, normalized_query),
        method="lexical",
        status="ok" if items else "no_match",
        limit=limit,
        corpus_digest=chunks.corpus_digest,
        configuration=configuration,
        items=items,
    )


def retrieve_latent(
    chunks: ChunkCorpus,
    query: str,
    config: LatentConfig,
) -> RetrievalResult:
    """Rank chunks in a deterministic latent semantic analysis space."""
    normalized_query = normalize_text(query)
    base_configuration: tuple[tuple[str, str | int | float], ...] = (
        ("dimensions_requested", config.dimensions),
        ("seed", config.seed),
        ("vectorizer", "tfidf_unigram_bigram"),
    )
    if not normalized_query:
        return _empty_result(
            chunks,
            query,
            "latent",
            config.limit,
            "empty_query",
            base_configuration,
        )
    if not chunks.chunks:
        return _empty_result(chunks, query, "latent", config.limit, "no_match", base_configuration)

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
    try:
        matrix = vectorizer.fit_transform(chunk.normalized_text for chunk in chunks.chunks)
    except ValueError:
        return _empty_result(chunks, query, "latent", config.limit, "no_match", base_configuration)
    query_vector = vectorizer.transform([normalized_query])
    if query_vector.nnz == 0:
        return _empty_result(chunks, query, "latent", config.limit, "no_match", base_configuration)

    components = min(config.dimensions, matrix.shape[0] - 1, matrix.shape[1] - 1)
    if components >= 1:
        model = TruncatedSVD(
            n_components=components,
            algorithm="randomized",
            n_iter=7,
            random_state=config.seed,
        )
        latent_documents = normalize(model.fit_transform(matrix))
        latent_query = normalize(model.transform(query_vector))
        scores = np.asarray(latent_documents @ latent_query.T).ravel()
        explanation = f"Cosine similarity in a {components}-dimensional deterministic LSA space."
    else:
        scores = (matrix @ query_vector.T).toarray().ravel()
        explanation = (
            "Cosine similarity in the normalized term space; corpus rank is too small for SVD."
        )
    configuration = (*base_configuration, ("dimensions_used", max(components, 0)))
    items = _rank_items(
        chunks=chunks,
        query=query,
        method="latent",
        scores=scores,
        limit=config.limit,
        score_label="lsa_cosine",
        explanation=explanation,
    )
    return RetrievalResult(
        query=query,
        query_id=_query_id(chunks, normalized_query),
        method="latent",
        status="ok" if items else "no_match",
        limit=config.limit,
        corpus_digest=chunks.corpus_digest,
        configuration=configuration,
        items=items,
    )
