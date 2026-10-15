"""Strict source-ID validation and deterministic projection of scheme facts."""

from __future__ import annotations

from .schemas import AnswerResult, GroundedAnswer, SchemeRecord


def ground_answer(
    draft: AnswerResult | None,
    retrieved: list[SchemeRecord],
    *,
    offline: bool = False,
) -> GroundedAnswer:
    """Ignore generated facts and copy answer fields verbatim from retrieved records."""
    if draft is not None:
        allowed = {record.scheme_id for record in retrieved}
        if any(scheme_id not in allowed for scheme_id in draft.source_scheme_ids):
            raise ValueError("LLM referenced a scheme that was not included in retrieval context.")
        selected_ids = set(draft.source_scheme_ids)
        records = (
            [record for record in retrieved if record.scheme_id in selected_ids]
            if selected_ids
            else list(retrieved)
        )
    else:
        records = list(retrieved)
    related = [record for record in retrieved if record not in records]
    missing_fields = [
        field_name
        for field_name in ("benefits", "eligibility", "documents", "how_to_apply")
        if records and not any(getattr(record, field_name) for record in records)
    ]
    return GroundedAnswer(
        summary="\n".join(
            f"{record.title}: {record.summary}" for record in records
        ) if records else "No matching scheme information was found in the available records.",
        benefits=[item for record in records for item in record.benefits],
        eligibility=[item for record in records for item in record.eligibility],
        documents=[item for record in records for item in record.documents],
        how_to_apply=[item for record in records for item in record.how_to_apply],
        source_scheme_ids=[record.scheme_id for record in records + related],
        schemes=records,
        related_schemes=related,
        missing_fields=missing_fields,
        offline=offline,
    )
