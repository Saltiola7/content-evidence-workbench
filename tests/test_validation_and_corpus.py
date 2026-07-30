from __future__ import annotations

import json
from copy import deepcopy

import pytest

from evidence_workbench import (
    MAX_DOCUMENTS,
    MAX_ENTITIES_PER_DOCUMENT,
    MAX_UPLOAD_BYTES,
    Document,
    DocumentValidationError,
    generate_corpus,
    parse_upload,
    validate_documents,
)


def test_synthetic_corpus_is_deterministic_clean_and_bounded() -> None:
    first = generate_corpus(seed=2026, documents=24)
    second = generate_corpus(seed=2026, documents=24)

    assert first == second
    assert first.seed == 2026
    assert first.generated_on == "2026-07-29"
    assert len(first.corpus.documents) == 24
    assert len({document.document_id for document in first.corpus.documents}) == 24

    serialized = repr(first).casefold()
    for forbidden in ("mgm", "bellagio", "saas pegasus", "flowbite", "@mgmresorts"):
        assert forbidden not in serialized


def test_validate_documents_preserves_input_and_normalizes_types(
    document_records: list[dict[str, object]],
) -> None:
    original = deepcopy(document_records)

    corpus = validate_documents(document_records)

    assert document_records == original
    assert tuple(document.document_id for document in corpus.documents) == (
        "aster-retention",
        "orion-solar",
        "aster-access",
    )
    assert corpus.documents[0].entities == ("Aster Labs", "Retention Console")
    assert corpus.byte_size == sum(
        len(document.text.encode("utf-8")) for document in corpus.documents
    )


def test_validate_documents_revalidates_typed_domain_values() -> None:
    invalid = Document(document_id="typed", title="Typed", text="")

    with pytest.raises(DocumentValidationError) as caught:
        validate_documents([invalid])

    assert caught.value.code == "empty_text"


@pytest.mark.parametrize(
    ("records", "expected_code"),
    [
        (object(), "records_type"),
        ([], "empty_corpus"),
        ([{"document_id": "x", "title": "X", "text": ""}], "empty_text"),
        (
            [
                {"document_id": "x", "title": "X", "text": "one"},
                {"document_id": "x", "title": "X2", "text": "two"},
            ],
            "duplicate_document_id",
        ),
        (
            [
                {
                    "document_id": "x",
                    "title": "X",
                    "text": "safe",
                    "source_url": "file:///private/content",
                }
            ],
            "source_url_scheme",
        ),
        (
            [{"document_id": "x", "title": "X", "text": "\ud800"}],
            "invalid_utf8",
        ),
    ],
)
def test_validation_stops_atomically_with_actionable_codes(
    records: object,
    expected_code: str,
) -> None:
    with pytest.raises(DocumentValidationError) as caught:
        validate_documents(records)

    assert caught.value.code == expected_code
    assert caught.value.partial_corpus is None


def test_validation_enforces_document_and_byte_bounds_without_echoing_content() -> None:
    too_many = [
        {"document_id": f"d-{index}", "title": "Bounded", "text": "safe"}
        for index in range(MAX_DOCUMENTS + 1)
    ]
    with pytest.raises(DocumentValidationError) as document_error:
        validate_documents(too_many)
    assert document_error.value.code == "document_limit"

    secret_marker = "PRIVATE-VISITOR-CONTENT"
    oversized = [
        {
            "document_id": "oversized",
            "title": "Oversized",
            "text": secret_marker + ("x" * MAX_UPLOAD_BYTES),
        }
    ]
    with pytest.raises(DocumentValidationError) as byte_error:
        validate_documents(oversized)
    assert byte_error.value.code == "byte_limit"
    assert secret_marker not in str(byte_error.value)


def test_validation_bounds_entity_cardinality_before_graph_expansion() -> None:
    entities = [f"Entity {index}" for index in range(MAX_ENTITIES_PER_DOCUMENT + 1)]

    with pytest.raises(DocumentValidationError) as caught:
        validate_documents(
            [
                {
                    "document_id": "entity-bound",
                    "title": "Entity bound",
                    "text": "Bounded entity graph.",
                    "entities": entities,
                }
            ]
        )

    assert caught.value.code == "entity_limit"


def test_parse_upload_supports_bounded_text_markdown_csv_and_json() -> None:
    plain = parse_upload("policy.txt", b"Retention is thirty days.")
    markdown = parse_upload("guide.md", b"# Guide\n\nEvidence keeps citations.")
    mapping = {"document_id": "id", "title": "name", "text": "body"}
    csv_corpus = parse_upload(
        "records.csv",
        b"id,name,body\none,First,Exact source text\n",
        mapping=mapping,
    )
    json_corpus = parse_upload(
        "records.json",
        json.dumps([{"id": "two", "name": "Second", "body": "Another source"}]).encode(),
        mapping=mapping,
    )

    assert plain.documents[0].text == "Retention is thirty days."
    assert markdown.documents[0].title == "Guide"
    assert csv_corpus.documents[0].document_id == "one"
    assert json_corpus.documents[0].document_id == "two"


def test_parse_upload_rejects_unsupported_or_ambiguous_inputs() -> None:
    with pytest.raises(DocumentValidationError, match="supported"):
        parse_upload("archive.pdf", b"%PDF")
    with pytest.raises(DocumentValidationError) as missing_mapping:
        parse_upload("records.csv", b"id,name,body\none,First,Text\n")
    assert missing_mapping.value.code == "mapping_required"
    with pytest.raises(DocumentValidationError) as invalid_utf8:
        parse_upload("policy.txt", b"\xff\xfe")
    assert invalid_utf8.value.code == "invalid_utf8"
