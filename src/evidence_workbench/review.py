"""Append-only human evidence review."""

from __future__ import annotations

from .domain import RetrievalResult, ReviewDecision, ReviewEntry, ReviewLedger

_ACTIONS = {"accept", "reject", "annotate", "defer", "reorder"}
_MAX_NOTE_CHARS = 2_000


def apply_review(
    result: RetrievalResult,
    decision: ReviewDecision,
    ledger: ReviewLedger | None = None,
) -> ReviewLedger:
    """Append one validated decision without mutating retrieval evidence."""
    current = ledger or ReviewLedger()
    if decision.query_id != result.query_id:
        raise ValueError("review query identity does not match retrieval result")
    if decision.action not in _ACTIONS:
        raise ValueError("review action is not supported")
    if decision.note is not None and len(decision.note) > _MAX_NOTE_CHARS:
        raise ValueError("review note exceeds the 2000 character limit")
    item = next((item for item in result.items if item.evidence_id == decision.evidence_id), None)
    if item is None:
        raise ValueError("review evidence identity is not present in the retrieval result")

    resulting_rank = item.rank
    if decision.action == "reorder":
        if decision.resulting_rank is None or not 1 <= decision.resulting_rank <= len(result.items):
            raise ValueError("reorder requires a resulting rank within the result set")
        resulting_rank = decision.resulting_rank
    elif decision.resulting_rank is not None and decision.resulting_rank != item.rank:
        raise ValueError("only reorder decisions may change rank")

    entry = ReviewEntry(
        sequence=len(current.entries) + 1,
        query_id=result.query_id,
        evidence_id=item.evidence_id,
        action=decision.action,
        note=decision.note,
        prior_rank=item.rank,
        resulting_rank=resulting_rank,
        citation=item.citation,
    )
    return ReviewLedger(entries=(*current.entries, entry))
