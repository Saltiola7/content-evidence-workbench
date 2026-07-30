"""Judgment-gated retrieval metrics."""

from __future__ import annotations

from math import log2

from .domain import EvaluationResult, Judgments, RetrievalMetrics, RetrievalResult


def _dcg(grades: list[float]) -> float:
    return sum((2**grade - 1) / log2(rank + 1) for rank, grade in enumerate(grades, start=1))


def evaluate_retrieval(
    result: RetrievalResult,
    judgments: Judgments,
) -> EvaluationResult:
    """Evaluate only when explicit judgments exist for this exact query identity."""
    query_judgments = judgments.by_query.get(result.query_id)
    if query_judgments is None:
        return EvaluationResult(
            query_id=result.query_id,
            available=False,
            reason="judgments_unavailable",
            metrics=None,
        )

    ranked_chunk_ids = [item.citation.chunk_id for item in result.items[: result.limit]]
    grades = [float(query_judgments.get(chunk_id, 0.0)) for chunk_id in ranked_chunk_ids]
    relevant_ids = {chunk_id for chunk_id, grade in query_judgments.items() if grade > 0}
    relevant_retrieved = sum(grade > 0 for grade in grades)
    total_relevant = len(relevant_ids)
    precision = relevant_retrieved / result.limit
    recall = relevant_retrieved / total_relevant if total_relevant else 0.0
    first_relevant = next((rank for rank, grade in enumerate(grades, start=1) if grade > 0), None)
    mrr = 1.0 / first_relevant if first_relevant is not None else 0.0
    ideal_grades = sorted(
        (float(grade) for grade in query_judgments.values() if grade > 0),
        reverse=True,
    )[: result.limit]
    ideal_dcg = _dcg(ideal_grades)
    ndcg = _dcg(grades) / ideal_dcg if ideal_dcg else 0.0
    judged_retrieved = sum(chunk_id in query_judgments for chunk_id in ranked_chunk_ids)
    coverage = judged_retrieved / result.limit
    return EvaluationResult(
        query_id=result.query_id,
        available=True,
        reason=None,
        metrics=RetrievalMetrics(
            k=result.limit,
            relevant_retrieved=relevant_retrieved,
            total_relevant=total_relevant,
            precision_at_k=precision,
            recall_at_k=recall,
            mrr=mrr,
            ndcg_at_k=ndcg,
            judgment_coverage=coverage,
        ),
    )
