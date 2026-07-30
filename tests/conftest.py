from __future__ import annotations

import pytest


@pytest.fixture
def document_records() -> list[dict[str, object]]:
    return [
        {
            "document_id": "aster-retention",
            "title": "Aster Labs retention policy",
            "text": (
                "Aster Labs stores audit events for thirty days. "
                "The Retention Console lets operators export signed evidence packets. "
                "Encryption keys rotate every ninety days."
            ),
            "source_url": "https://example.test/aster-retention",
            "published_on": "2026-04-10",
            "entities": ["Aster Labs", "Retention Console"],
        },
        {
            "document_id": "orion-solar",
            "title": "Orion Clinic energy handbook",
            "text": (
                "Orion Clinic powers its west campus with a solar array. "
                "Facilities teams inspect battery capacity each week. "
                "The handbook assigns maintenance to the Energy Desk."
            ),
            "source_url": "https://example.test/orion-solar",
            "published_on": "2026-05-12",
            "entities": ["Orion Clinic", "Energy Desk"],
        },
        {
            "document_id": "aster-access",
            "title": "Aster Labs access review",
            "text": (
                "Aster Labs reviews workspace access monthly. "
                "The Retention Console records reviewer decisions and exact source citations. "
                "Rejected evidence remains visible in the append-only review ledger."
            ),
            "entities": ["Aster Labs", "Retention Console"],
        },
    ]
