from kiosk_app.bhashini import SDKResult
from kiosk_app.observability import StageMetrics
from kiosk_app.pipeline import ChatPipeline
from kiosk_app.repository import MongoSchemeRepository
from kiosk_tests.helpers import FakeBhashini, sample_record, settings
from kiosk_tests.test_repository import MockMongoCollection


class FakeProvider:
    def complete_json(self, _system, _prompt, schema):
        if schema["title"] == "IntentResult":
            return {"intent": "benefits", "filters": {"category": "farmers"}}
        return {
            "summary": "Invented fact, intentionally discarded.",
            "benefits": ["Invented benefit."],
            "eligibility": [],
            "documents": [],
            "how_to_apply": [],
            "source_scheme_ids": ["integration-scheme"],
        }


def test_pipeline_integration_with_mock_bhashini_llm_and_mongo():
    record = sample_record(scheme_id="integration-scheme")
    repository = MongoSchemeRepository.__new__(MongoSchemeRepository)
    repository._collection = MockMongoCollection([record.model_dump()])
    repository._max_scan = 100
    pipeline = ChatPipeline(
        settings(),
        FakeBhashini(),
        repository,
        FakeProvider(),
        StageMetrics(),
    )

    result = pipeline.answer_text("How can I get farmer support?", "en")

    assert result["answer"]["source_scheme_ids"] == ["integration-scheme"]
    assert result["answer"]["benefits"] == record.benefits
    assert "Invented benefit" not in result["reply"]
    assert "Record benefit." in result["reply"]
    assert result["audio_base64"]
