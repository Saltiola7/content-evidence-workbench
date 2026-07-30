"""Deterministic fictional corpus generator."""

from __future__ import annotations

import random
from hashlib import sha256

from .domain import CorpusFixture
from .validation import MAX_DOCUMENTS, validate_documents

_ORGANIZATIONS = (
    "Aster Labs",
    "Orion Clinic",
    "Juniper Transit",
    "Cobalt Library",
    "Lumen Foods",
    "Nimbus Works",
    "Harbor Museum",
    "Cedar Robotics",
)
_PRODUCTS = (
    "Evidence Console",
    "Atlas Registry",
    "Signal Desk",
    "Source Ledger",
    "Review Portal",
    "Citation Kit",
)
_TOPICS = (
    ("retention", "stores audit events for thirty days", "reviews deletion receipts monthly"),
    ("access", "requires quarterly workspace access review", "records every reviewer decision"),
    ("energy", "measures solar output each week", "publishes battery capacity summaries"),
    ("quality", "samples evidence packets before release", "rejects records missing citations"),
    ("continuity", "tests recovery procedures every quarter", "keeps signed restoration reports"),
    ("privacy", "minimizes visitor file collection", "removes runtime files after each session"),
)


def generate_corpus(seed: int = 2026, documents: int = 24) -> CorpusFixture:
    """Generate a stable corpus containing only fictional names and statements."""
    if not 1 <= documents <= MAX_DOCUMENTS:
        raise ValueError(f"documents must be between 1 and {MAX_DOCUMENTS}")
    generator = random.Random(seed)
    records: list[dict[str, object]] = []
    for index in range(documents):
        organization = _ORGANIZATIONS[index % len(_ORGANIZATIONS)]
        product = _PRODUCTS[(index * 3 + generator.randrange(len(_PRODUCTS))) % len(_PRODUCTS)]
        topic, policy, control = _TOPICS[(index + generator.randrange(len(_TOPICS))) % len(_TOPICS)]
        edition = 1 + index // len(_ORGANIZATIONS)
        text = (
            f"{organization} publishes a fictional {topic} handbook for demonstration. "
            f"The handbook says the team {policy}. "
            f"The {product} {control}. "
            "Every evidence packet includes a document identity, exact character offsets, "
            "source text, and a content hash. "
            "These statements describe synthetic organizations and are not factual claims."
        )
        records.append(
            {
                "document_id": f"synthetic-{index + 1:03d}",
                "title": f"{organization} {topic.title()} Handbook - Edition {edition}",
                "text": text,
                "source_url": f"https://example.test/synthetic/{index + 1:03d}",
                "published_on": f"2026-{(index % 12) + 1:02d}-{(index % 27) + 1:02d}",
                "entities": [organization, product],
            }
        )
    corpus = validate_documents(records)
    identity = sha256(
        "\0".join(
            f"{document.document_id}:{sha256(document.text.encode()).hexdigest()}"
            for document in corpus.documents
        ).encode()
    ).hexdigest()
    return CorpusFixture(
        corpus=corpus,
        seed=seed,
        generated_on="2026-07-29",
        fixture_id=f"synthetic-v1-{identity[:16]}",
    )
