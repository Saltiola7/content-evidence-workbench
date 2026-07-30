from __future__ import annotations

import json
import socket
import urllib.request
from copy import deepcopy

import pytest

from evidence_workbench import (
    ChunkConfig,
    EvidenceSession,
    Judgments,
    ReviewDecision,
    apply_review,
    chunk_documents,
    evaluate_retrieval,
    export_evidence,
    generate_corpus,
    retrieve_lexical,
    validate_documents,
)


def _result(document_records: list[dict[str, object]]):
    chunks = chunk_documents(
        validate_documents(document_records),
        ChunkConfig(max_chars=220, overlap_chars=16),
    )
    return retrieve_lexical(chunks, "retention citations", limit=3)


def test_metrics_are_unavailable_without_explicit_judgments(
    document_records: list[dict[str, object]],
) -> None:
    result = _result(document_records)

    evaluation = evaluate_retrieval(result, Judgments(by_query={}))

    assert evaluation.available is False
    assert evaluation.reason == "judgments_unavailable"
    assert evaluation.metrics is None


def test_metrics_use_explicit_query_and_chunk_identity(
    document_records: list[dict[str, object]],
) -> None:
    result = _result(document_records)
    top = result.items[0].citation.chunk_id
    second = result.items[1].citation.chunk_id
    judgments = Judgments(by_query={result.query_id: {top: 2.0, second: 0.0}})

    evaluation = evaluate_retrieval(result, judgments)

    assert evaluation.available is True
    assert evaluation.metrics is not None
    assert evaluation.metrics.k == 3
    assert evaluation.metrics.relevant_retrieved == 1
    assert evaluation.metrics.precision_at_k == pytest.approx(1 / 3)
    assert evaluation.metrics.recall_at_k == 1.0
    assert evaluation.metrics.mrr == 1.0
    assert evaluation.metrics.ndcg_at_k == 1.0
    assert evaluation.metrics.judgment_coverage == pytest.approx(2 / 3)


def test_review_ledger_is_append_only_and_citation_preserving(
    document_records: list[dict[str, object]],
) -> None:
    result = _result(document_records)
    original = deepcopy(result)
    first_item, second_item = result.items[:2]

    first = apply_review(
        result,
        ReviewDecision(
            query_id=result.query_id,
            evidence_id=first_item.evidence_id,
            action="accept",
            note="Directly supports the retention claim.",
        ),
    )
    second = apply_review(
        result,
        ReviewDecision(
            query_id=result.query_id,
            evidence_id=second_item.evidence_id,
            action="reorder",
            note="Move supporting context first.",
            resulting_rank=1,
        ),
        ledger=first,
    )

    assert result == original
    assert first.entries[0].sequence == 1
    assert second.entries[0] == first.entries[0]
    assert second.entries[1].sequence == 2
    assert second.entries[1].prior_rank == second_item.rank
    assert second.entries[1].resulting_rank == 1
    assert second.entries[0].citation == first_item.citation


def test_safe_exports_preserve_json_citations_and_escape_csv_formulas() -> None:
    records = [
        {
            "document_id": "formula",
            "title": "@Unsafe title",
            "text": '=HYPERLINK("https://attacker.invalid","click") retention evidence',
            "entities": ["Formula Labs"],
        }
    ]
    result = retrieve_lexical(
        chunk_documents(validate_documents(records), ChunkConfig(max_chars=200, overlap_chars=0)),
        "retention evidence",
        limit=1,
    )
    ledger = apply_review(
        result,
        ReviewDecision(
            query_id=result.query_id,
            evidence_id=result.items[0].evidence_id,
            action="annotate",
            note="+SUM(1,1)",
        ),
    )
    session = EvidenceSession(
        results=(result,),
        ledger=ledger,
        evaluations=(),
        configuration={"seed": 2026, "mode": "deterministic"},
        fixture_id="formula-fixture",
    )

    first = export_evidence(session)
    second = export_evidence(session)
    payload = json.loads(first.json_text)

    assert first == second
    assert payload["results"][0]["items"][0]["citation"]["text"].startswith("=HYPERLINK")
    assert "'=HYPERLINK" in first.evidence_csv
    assert "'@Unsafe title" in first.evidence_csv
    assert "'+SUM(1,1)" in first.review_csv
    assert first.bundle_sha256


def test_safe_exports_escape_tab_and_carriage_return_prefixes() -> None:
    records = [
        {
            "document_id": "controls",
            "title": "Control prefixes",
            "text": "\tDDE payload retention evidence",
        }
    ]
    result = retrieve_lexical(
        chunk_documents(validate_documents(records), ChunkConfig()),
        "retention",
        limit=1,
    )
    ledger = apply_review(
        result,
        ReviewDecision(
            query_id=result.query_id,
            evidence_id=result.items[0].evidence_id,
            action="annotate",
            note="\rformula",
        ),
    )

    exported = export_evidence(EvidenceSession(results=(result,), ledger=ledger))

    assert "'\tDDE payload retention evidence" in exported.evidence_csv
    assert "'\rformula" in exported.review_csv


def test_default_workflow_performs_no_network_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def blocked(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network access attempted")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(urllib.request, "urlopen", blocked)

    fixture = generate_corpus(seed=2026, documents=6)
    chunks = chunk_documents(fixture.corpus, ChunkConfig())
    result = retrieve_lexical(chunks, "citation policy", limit=3)
    session = EvidenceSession(
        results=(result,),
        fixture_id=fixture.fixture_id,
        configuration={"seed": fixture.seed},
    )

    assert export_evidence(session).bundle_sha256
