from kiosk_app.repository import InMemorySchemeRepository, MongoSchemeRepository
from kiosk_app.repository import ResilientSchemeRepository
from kiosk_app.schemas import SchemeFilters
from kiosk_app.errors import SchemaMismatchError
import pytest
from kiosk_tests.helpers import sample_record


class Cursor(list):
    def sort(self, *_args):
        return self

    def limit(self, amount):
        return Cursor(self[:amount])


class MockMongoCollection:
    def __init__(self, documents):
        self.documents = documents

    def find(self, _query, _projection):
        return Cursor(self.documents)

    def find_one(self, query, _projection):
        return next((doc for doc in self.documents if doc["scheme_id"] == query["scheme_id"]), None)


def test_in_memory_search_applies_category_and_keywords():
    repository = InMemorySchemeRepository()
    assert len(repository.search("", SchemeFilters(category="farmers"), limit=10)) == 2
    assert repository.search("scholarship", limit=5)[0].scheme_id == "dev-student-scholarship"


def test_mongo_adapter_uses_canonical_contract_and_text_query():
    record = sample_record()
    repository = MongoSchemeRepository.__new__(MongoSchemeRepository)
    repository._collection = MockMongoCollection([record.model_dump()])
    repository._max_scan = 100
    result = repository.search("support", SchemeFilters(category="farmers"), limit=5)
    assert result == [record]


def test_resilient_repository_searches_cached_records_after_mongo_failure():
    record = sample_record()

    class FlakyRepository:
        available = True

        def search(self, *_args, **_kwargs):
            if not self.available:
                raise ConnectionError("Mongo unavailable")
            return [record]

        def get(self, scheme_id):
            if not self.available:
                raise ConnectionError("Mongo unavailable")
            return record if scheme_id == record.scheme_id else None

    source = FlakyRepository()
    repository = ResilientSchemeRepository(source)
    assert repository.search("support", limit=5) == [record]
    source.available = False
    assert repository.search("support", limit=5) == [record]
    assert repository.degraded is True
    assert repository.get(record.scheme_id) == record


def test_mongo_contract_mismatch_is_explicit():
    with pytest.raises(SchemaMismatchError):
        MongoSchemeRepository._validate_document({"scheme_id": "missing-title"})
