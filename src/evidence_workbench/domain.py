"""Immutable domain values for deterministic evidence retrieval."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal

RetrievalMethod = Literal["lexical", "latent"]
RetrievalStatus = Literal["ok", "empty_query", "no_match"]
ReviewAction = Literal["accept", "reject", "annotate", "defer", "reorder"]


@dataclass(frozen=True, slots=True)
class Document:
    document_id: str
    title: str
    text: str
    source_url: str | None = None
    published_on: str | None = None
    entities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DocumentCorpus:
    documents: tuple[Document, ...]

    @property
    def byte_size(self) -> int:
        return sum(len(document.text.encode("utf-8")) for document in self.documents)


@dataclass(frozen=True, slots=True)
class CorpusFixture:
    corpus: DocumentCorpus
    seed: int
    generated_on: str
    fixture_id: str
    generator_version: str = "1.0"
    license: str = "CC0-1.0"


@dataclass(frozen=True, slots=True)
class ChunkConfig:
    max_chars: int = 480
    overlap_chars: int = 80
    min_break_fraction: float = 0.55

    def __post_init__(self) -> None:
        if self.max_chars < 32:
            raise ValueError("max_chars must be at least 32")
        if not 0 <= self.overlap_chars < self.max_chars:
            raise ValueError("overlap_chars must be smaller than max_chars")
        if not 0.25 <= self.min_break_fraction <= 1.0:
            raise ValueError("min_break_fraction must be between 0.25 and 1.0")


@dataclass(frozen=True, slots=True)
class Chunk:
    chunk_id: str
    document_id: str
    title: str
    source_url: str | None
    published_on: str | None
    start_offset: int
    end_offset: int
    text: str
    normalized_text: str
    content_sha256: str
    entities: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ChunkCorpus:
    chunks: tuple[Chunk, ...]
    corpus_digest: str
    config: ChunkConfig


@dataclass(frozen=True, slots=True)
class LatentConfig:
    dimensions: int = 8
    seed: int = 2026
    limit: int = 8

    def __post_init__(self) -> None:
        if self.dimensions < 1:
            raise ValueError("dimensions must be positive")
        if self.limit < 1:
            raise ValueError("limit must be positive")


@dataclass(frozen=True, slots=True)
class Citation:
    document_id: str
    title: str
    source_url: str | None
    published_on: str | None
    chunk_id: str
    start_offset: int
    end_offset: int
    content_sha256: str
    text: str


@dataclass(frozen=True, slots=True)
class EvidenceItem:
    evidence_id: str
    rank: int
    score: float
    score_label: str
    explanation: str
    citation: Citation
    matched_terms: tuple[str, ...] = ()
    related_entities: tuple[str, ...] = ()
    review_status: str = "unreviewed"


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    query: str
    query_id: str
    method: RetrievalMethod
    status: RetrievalStatus
    limit: int
    corpus_digest: str
    configuration: tuple[tuple[str, str | int | float], ...]
    items: tuple[EvidenceItem, ...] = ()


@dataclass(frozen=True, slots=True)
class EntityEdge:
    source: str
    target: str
    weight: int
    chunk_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EntityGraph:
    nodes: tuple[str, ...]
    edges: tuple[EntityEdge, ...]
    chunk_entities: tuple[tuple[str, tuple[str, ...]], ...]


@dataclass(frozen=True, slots=True)
class Judgments:
    """Explicit graded judgments keyed by query identity then chunk identity."""

    by_query: Mapping[str, Mapping[str, float]]

    def __post_init__(self) -> None:
        normalized: dict[str, Mapping[str, float]] = {}
        for query_id, chunk_scores in self.by_query.items():
            if not isinstance(query_id, str) or not query_id:
                raise ValueError("judgment query identities must be nonempty strings")
            clean_scores: dict[str, float] = {}
            for chunk_id, score in chunk_scores.items():
                numeric_score = float(score)
                if not isinstance(chunk_id, str) or not chunk_id:
                    raise ValueError("judgment chunk identities must be nonempty strings")
                if numeric_score < 0:
                    raise ValueError("judgment scores must be nonnegative")
                clean_scores[chunk_id] = numeric_score
            normalized[query_id] = MappingProxyType(clean_scores)
        object.__setattr__(self, "by_query", MappingProxyType(normalized))


@dataclass(frozen=True, slots=True)
class RetrievalMetrics:
    k: int
    relevant_retrieved: int
    total_relevant: int
    precision_at_k: float
    recall_at_k: float
    mrr: float
    ndcg_at_k: float
    judgment_coverage: float


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    query_id: str
    available: bool
    reason: str | None
    metrics: RetrievalMetrics | None


@dataclass(frozen=True, slots=True)
class ReviewDecision:
    query_id: str
    evidence_id: str
    action: ReviewAction
    note: str | None = None
    resulting_rank: int | None = None


@dataclass(frozen=True, slots=True)
class ReviewEntry:
    sequence: int
    query_id: str
    evidence_id: str
    action: ReviewAction
    note: str | None
    prior_rank: int
    resulting_rank: int
    citation: Citation


@dataclass(frozen=True, slots=True)
class ReviewLedger:
    entries: tuple[ReviewEntry, ...] = ()


@dataclass(frozen=True, slots=True)
class EvidenceSession:
    results: tuple[RetrievalResult, ...]
    ledger: ReviewLedger = field(default_factory=ReviewLedger)
    evaluations: tuple[EvaluationResult, ...] = ()
    configuration: Mapping[str, str | int | float | bool] = field(default_factory=dict)
    fixture_id: str = "runtime"

    def __post_init__(self) -> None:
        object.__setattr__(self, "configuration", MappingProxyType(dict(self.configuration)))


@dataclass(frozen=True, slots=True)
class ExportBundle:
    json_text: str
    evidence_csv: str
    review_csv: str
    bundle_sha256: str
