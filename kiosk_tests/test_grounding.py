import pytest

from kiosk_app.grounding import ground_answer
from kiosk_app.schemas import AnswerResult
from kiosk_tests.helpers import sample_record


def test_grounding_uses_exact_record_fields_not_generated_claims():
    record = sample_record()
    draft = AnswerResult(
        summary="You will receive $50,000 tomorrow.",
        benefits=["Guaranteed payment of $50,000."],
        eligibility=["Everyone qualifies."],
        documents=["No documents needed."],
        how_to_apply=["Apply at invented.example."],
        source_scheme_ids=[record.scheme_id],
    )

    answer = ground_answer(draft, [record])

    assert answer.summary == f"{record.title}: {record.summary}"
    assert answer.benefits == record.benefits
    assert answer.eligibility == record.eligibility
    assert answer.documents == record.documents
    assert answer.how_to_apply == record.how_to_apply
    assert answer.source_scheme_ids == [record.scheme_id]


def test_grounding_rejects_a_scheme_id_outside_retrieval():
    draft = AnswerResult(
        summary="",
        benefits=[],
        eligibility=[],
        documents=[],
        how_to_apply=[],
        source_scheme_ids=["not-retrieved"],
    )
    with pytest.raises(ValueError, match="not included in retrieval"):
        ground_answer(draft, [sample_record()])
