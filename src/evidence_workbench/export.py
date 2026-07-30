"""Deterministic citation-preserving JSON and formula-safe CSV exports."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from hashlib import sha256
from io import StringIO

from .domain import EvidenceSession, ExportBundle


def _safe_csv(value: object) -> object:
    if not isinstance(value, str):
        return value
    if value.startswith(("\t", "\r", "\n")) or value.lstrip(" ").startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def _csv_text(headers: list[str], rows: list[dict[str, object]]) -> str:
    output = StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=headers, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _safe_csv(row.get(key, "")) for key in headers})
    return output.getvalue()


def _result_payload(session: EvidenceSession) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    for result in session.results:
        results.append(
            {
                "query": result.query,
                "query_id": result.query_id,
                "method": result.method,
                "status": result.status,
                "limit": result.limit,
                "corpus_digest": result.corpus_digest,
                "configuration": dict(result.configuration),
                "items": [
                    {
                        "evidence_id": item.evidence_id,
                        "rank": item.rank,
                        "score": item.score,
                        "score_label": item.score_label,
                        "explanation": item.explanation,
                        "matched_terms": list(item.matched_terms),
                        "related_entities": list(item.related_entities),
                        "review_status": item.review_status,
                        "citation": asdict(item.citation),
                    }
                    for item in result.items
                ],
            }
        )
    return results


def export_evidence(session: EvidenceSession) -> ExportBundle:
    """Export evidence without changing citation identity or source text."""
    results_payload = _result_payload(session)
    review_payload = [
        {
            "sequence": entry.sequence,
            "query_id": entry.query_id,
            "evidence_id": entry.evidence_id,
            "action": entry.action,
            "note": entry.note,
            "prior_rank": entry.prior_rank,
            "resulting_rank": entry.resulting_rank,
            "citation": asdict(entry.citation),
        }
        for entry in session.ledger.entries
    ]
    evaluation_payload = []
    for evaluation in session.evaluations:
        evaluation_payload.append(
            {
                "query_id": evaluation.query_id,
                "available": evaluation.available,
                "reason": evaluation.reason,
                "metrics": asdict(evaluation.metrics) if evaluation.metrics is not None else None,
            }
        )
    payload = {
        "schema_version": "1.0",
        "fixture_id": session.fixture_id,
        "configuration": dict(session.configuration),
        "results": results_payload,
        "review_ledger": review_payload,
        "evaluations": evaluation_payload,
    }
    json_text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"

    evidence_rows: list[dict[str, object]] = []
    for result in session.results:
        for item in result.items:
            citation = item.citation
            evidence_rows.append(
                {
                    "query_id": result.query_id,
                    "query": result.query,
                    "method": result.method,
                    "rank": item.rank,
                    "score": f"{item.score:.12g}",
                    "score_label": item.score_label,
                    "evidence_id": item.evidence_id,
                    "document_id": citation.document_id,
                    "title": citation.title,
                    "source_url": citation.source_url or "",
                    "published_on": citation.published_on or "",
                    "chunk_id": citation.chunk_id,
                    "start_offset": citation.start_offset,
                    "end_offset": citation.end_offset,
                    "content_sha256": citation.content_sha256,
                    "text": citation.text,
                    "matched_terms": "|".join(item.matched_terms),
                    "related_entities": "|".join(item.related_entities),
                }
            )
    evidence_headers = [
        "query_id",
        "query",
        "method",
        "rank",
        "score",
        "score_label",
        "evidence_id",
        "document_id",
        "title",
        "source_url",
        "published_on",
        "chunk_id",
        "start_offset",
        "end_offset",
        "content_sha256",
        "text",
        "matched_terms",
        "related_entities",
    ]
    evidence_csv = _csv_text(evidence_headers, evidence_rows)

    review_rows = [
        {
            "sequence": entry.sequence,
            "query_id": entry.query_id,
            "evidence_id": entry.evidence_id,
            "action": entry.action,
            "note": entry.note or "",
            "prior_rank": entry.prior_rank,
            "resulting_rank": entry.resulting_rank,
            "document_id": entry.citation.document_id,
            "chunk_id": entry.citation.chunk_id,
            "start_offset": entry.citation.start_offset,
            "end_offset": entry.citation.end_offset,
            "content_sha256": entry.citation.content_sha256,
            "text": entry.citation.text,
        }
        for entry in session.ledger.entries
    ]
    review_headers = [
        "sequence",
        "query_id",
        "evidence_id",
        "action",
        "note",
        "prior_rank",
        "resulting_rank",
        "document_id",
        "chunk_id",
        "start_offset",
        "end_offset",
        "content_sha256",
        "text",
    ]
    review_csv = _csv_text(review_headers, review_rows)
    digest = sha256(
        (json_text + "\0" + evidence_csv + "\0" + review_csv).encode("utf-8")
    ).hexdigest()
    return ExportBundle(
        json_text=json_text,
        evidence_csv=evidence_csv,
        review_csv=review_csv,
        bundle_sha256=digest,
    )
