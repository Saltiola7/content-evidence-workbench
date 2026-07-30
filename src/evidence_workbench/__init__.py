"""Public API for Content Evidence Workbench."""

from .chunking import MAX_CHUNKS, chunk_documents
from .domain import (
    Chunk,
    ChunkConfig,
    ChunkCorpus,
    Citation,
    CorpusFixture,
    Document,
    DocumentCorpus,
    EntityEdge,
    EntityGraph,
    EvaluationResult,
    EvidenceItem,
    EvidenceSession,
    ExportBundle,
    Judgments,
    LatentConfig,
    RetrievalMethod,
    RetrievalMetrics,
    RetrievalResult,
    RetrievalStatus,
    ReviewDecision,
    ReviewEntry,
    ReviewLedger,
)
from .entities import build_entity_graph
from .evaluation import evaluate_retrieval
from .export import export_evidence
from .retrieval import retrieve_latent, retrieve_lexical
from .review import apply_review
from .synthetic import generate_corpus
from .validation import (
    MAX_DOCUMENTS,
    MAX_ENTITIES_PER_DOCUMENT,
    MAX_UPLOAD_BYTES,
    DocumentValidationError,
    parse_upload,
    validate_documents,
)

__all__ = [
    "MAX_CHUNKS",
    "MAX_DOCUMENTS",
    "MAX_ENTITIES_PER_DOCUMENT",
    "MAX_UPLOAD_BYTES",
    "Chunk",
    "ChunkConfig",
    "ChunkCorpus",
    "Citation",
    "CorpusFixture",
    "Document",
    "DocumentCorpus",
    "DocumentValidationError",
    "EntityEdge",
    "EntityGraph",
    "EvaluationResult",
    "EvidenceItem",
    "EvidenceSession",
    "ExportBundle",
    "Judgments",
    "LatentConfig",
    "RetrievalMethod",
    "RetrievalMetrics",
    "RetrievalResult",
    "RetrievalStatus",
    "ReviewDecision",
    "ReviewEntry",
    "ReviewLedger",
    "apply_review",
    "build_entity_graph",
    "chunk_documents",
    "evaluate_retrieval",
    "export_evidence",
    "generate_corpus",
    "parse_upload",
    "retrieve_latent",
    "retrieve_lexical",
    "validate_documents",
]
