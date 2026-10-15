"""Scheme repository contract, strictly validated Mongo adapter, and dev-only mock."""

from __future__ import annotations

import logging
import re
from typing import Protocol

from pydantic import ValidationError

from .config import SCHEME_CATEGORIES
from .errors import SchemaMismatchError
from .schemas import SchemeFilters, SchemeRecord

logger = logging.getLogger(__name__)
CATEGORY_LABELS = {
    "farmers": "Farmers",
    "women": "Women",
    "students": "Students",
    "health": "Health",
    "housing": "Housing",
    "pensions": "Pensions",
    "employment": "Employment",
}
CONTRACT_TEXT_FIELDS = (
    "title",
    "summary",
    "benefits",
    "eligibility",
    "documents",
    "how_to_apply",
    "categories",
)


class SchemeRepository(Protocol):
    """Shared query interface; document storage and Mongo details stay behind it."""

    def search(
        self,
        query: str = "",
        filters: SchemeFilters | None = None,
        *,
        limit: int = 5,
    ) -> list[SchemeRecord]:
        """Search by text and apply canonical eligibility filters."""

    def get(self, scheme_id: str) -> SchemeRecord | None:
        """Return one scheme by its stable public ID."""


def _normalized(value: str) -> str:
    return value.strip().casefold()


def _matches(record: SchemeRecord, filters: SchemeFilters) -> bool:
    if filters.age is not None:
        if record.eligible_age_min is not None and filters.age < record.eligible_age_min:
            return False
        if record.eligible_age_max is not None and filters.age > record.eligible_age_max:
            return False
    if filters.income is not None:
        if record.income_min is not None and filters.income < record.income_min:
            return False
        if record.income_max is not None and filters.income > record.income_max:
            return False
    checks = (
        (filters.state, record.eligible_states),
        (filters.gender, record.genders),
        (filters.occupation, record.occupations),
    )
    for requested, allowed in checks:
        if requested and allowed and not any(_normalized(requested) == _normalized(item) for item in allowed):
            return False
    if filters.category and not any(
        _normalized(filters.category) == _normalized(item) for item in record.categories
    ):
        return False
    return True


def _score(record: SchemeRecord, query: str) -> int:
    tokens = {token.casefold() for token in re.findall(r"\w+", query) if len(token) > 1}
    if not tokens:
        return 0
    searchable = " ".join(
        [record.title, record.summary, *record.benefits, *record.eligibility,
         *record.documents, *record.how_to_apply, *record.categories]
    ).casefold()
    return sum(searchable.count(token) for token in tokens)


def _sample(
    scheme_id: str,
    title: str,
    category: str,
    summary: str,
    *,
    occupation: str | None = None,
    gender: str | None = None,
) -> SchemeRecord:
    disclaimer = "Development sample only. Not an official government scheme; replace with verified MongoDB records."
    return SchemeRecord(
        scheme_id=scheme_id,
        title=f"DEVELOPMENT SAMPLE — {title}",
        summary=f"{disclaimer} {summary}",
        benefits=["Sample benefit text; no amount or entitlement is asserted."],
        eligibility=["Sample eligibility text; confirm all criteria against an official source."],
        documents=["Sample document list; confirm required documents with the scheme owner."],
        how_to_apply=["Sample application step; replace with the verified official process."],
        categories=[category],
        eligible_states=[],
        genders=[gender] if gender else [],
        occupations=[occupation] if occupation else [],
        development_sample=True,
    )


DEVELOPMENT_SCHEMES = (
    _sample("dev-farmer-input", "Farmer Input Support", "farmers", "Illustrates a crop-input support listing.", occupation="farmer"),
    _sample("dev-farm-equipment", "Small Farm Equipment Assistance", "farmers", "Illustrates equipment assistance.", occupation="farmer"),
    _sample("dev-women-enterprise", "Women Enterprise Starter Support", "women", "Illustrates a small-enterprise listing.", gender="woman"),
    _sample("dev-student-scholarship", "Student Learning Scholarship", "students", "Illustrates an education support listing."),
    _sample("dev-student-hostel", "Student Hostel Support", "students", "Illustrates an accommodation support listing."),
    _sample("dev-health-access", "Community Health Access Support", "health", "Illustrates a health-services listing."),
    _sample("dev-housing-repair", "Rural Housing Repair Support", "housing", "Illustrates a housing support listing."),
    _sample("dev-senior-pension", "Senior Citizen Pension Listing", "pensions", "Illustrates a pension listing."),
    _sample("dev-disability-pension", "Disability Pension Listing", "pensions", "Illustrates a disability support listing."),
    _sample("dev-employment-skills", "Local Skills and Employment Support", "employment", "Illustrates a skills and employment listing."),
)


class InMemorySchemeRepository:
    """Ten clearly marked non-official records for local UI and pipeline development."""

    def __init__(self, records: tuple[SchemeRecord, ...] = DEVELOPMENT_SCHEMES) -> None:
        self._records = {record.scheme_id: record for record in records}

    def search(
        self,
        query: str = "",
        filters: SchemeFilters | None = None,
        *,
        limit: int = 5,
    ) -> list[SchemeRecord]:
        active_filters = filters or SchemeFilters()
        ranked = [
            (record, _score(record, query))
            for record in self._records.values()
            if _matches(record, active_filters)
        ]
        if query.strip():
            ranked = [(record, score) for record, score in ranked if score > 0]
            ranked.sort(key=lambda item: item[1], reverse=True)
        return [record for record, _ in ranked[:limit]]

    def get(self, scheme_id: str) -> SchemeRecord | None:
        return self._records.get(scheme_id)


class MongoSchemeRepository:
    """Mongo adapter for the canonical SchemeRecord document contract."""

    def __init__(self, uri: str, database: str, collection: str, *, max_scan: int = 500) -> None:
        try:
            from pymongo import MongoClient
        except ImportError as exc:
            raise RuntimeError("MongoDB mode requires pymongo; install kiosk_requirements.txt.") from exc
        self._client = MongoClient(uri, serverSelectionTimeoutMS=4000, connectTimeoutMS=4000)
        self._collection = self._client[database][collection]
        self._max_scan = max_scan

    @staticmethod
    def _validate_document(document: dict) -> SchemeRecord:
        try:
            return SchemeRecord.model_validate(document)
        except ValidationError as exc:
            issue = exc.errors()[0]
            field_path = ".".join(str(part) for part in issue["loc"])
            logger.error(
                "mongo_schema_mismatch",
                extra={"event": "mongo_schema_mismatch", "fields": {"field_path": field_path}},
            )
            raise SchemaMismatchError(
                f"Mongo scheme document does not match the canonical contract at field '{field_path}'."
            ) from exc

    @staticmethod
    def _mongo_filters(filters: SchemeFilters) -> dict:
        query: dict = {}
        clauses: list[dict] = []
        if filters.age is not None:
            clauses.extend(
                [
                    {"$or": [{"eligible_age_min": None}, {"eligible_age_min": {"$lte": filters.age}}]},
                    {"$or": [{"eligible_age_max": None}, {"eligible_age_max": {"$gte": filters.age}}]},
                ]
            )
        if filters.income is not None:
            clauses.extend(
                [
                    {"$or": [{"income_min": None}, {"income_min": {"$lte": filters.income}}]},
                    {"$or": [{"income_max": None}, {"income_max": {"$gte": filters.income}}]},
                ]
            )
        if filters.state:
            clauses.append({"$or": [{"eligible_states": {"$exists": False}}, {"eligible_states": {"$size": 0}}, {"eligible_states": {"$regex": f"^{re.escape(filters.state)}$", "$options": "i"}}]})
        if filters.gender:
            clauses.append({"$or": [{"genders": {"$exists": False}}, {"genders": {"$size": 0}}, {"genders": {"$regex": f"^{re.escape(filters.gender)}$", "$options": "i"}}]})
        if filters.occupation:
            clauses.append({"$or": [{"occupations": {"$exists": False}}, {"occupations": {"$size": 0}}, {"occupations": {"$regex": f"^{re.escape(filters.occupation)}$", "$options": "i"}}]})
        if filters.category:
            clauses.append({"categories": {"$regex": f"^{re.escape(filters.category)}$", "$options": "i"}})
        if clauses:
            query["$and"] = clauses
        return query

    def search(
        self,
        query: str = "",
        filters: SchemeFilters | None = None,
        *,
        limit: int = 5,
    ) -> list[SchemeRecord]:
        metadata_query = self._mongo_filters(filters or SchemeFilters())
        projection = {"_id": 0}
        if query.strip():
            try:
                documents = list(
                    self._collection.find(
                        {"$and": [metadata_query, {"$text": {"$search": query}}]},
                        {**projection, "score": {"$meta": "textScore"}},
                    )
                    .sort([("score", {"$meta": "textScore"})])
                    .limit(limit)
                )
            except Exception as exc:
                from pymongo.errors import OperationFailure

                if not isinstance(exc, OperationFailure) or (
                    exc.code != 27 and "text index required" not in str(exc).casefold()
                ):
                    raise
                logger.warning(
                    "mongo_text_index_unavailable",
                    extra={"event": "mongo_text_index_unavailable", "fields": {"error_type": type(exc).__name__}},
                )
                documents = list(self._collection.find(metadata_query, projection).limit(self._max_scan))
        else:
            documents = list(self._collection.find(metadata_query, projection).limit(self._max_scan))
        records = []
        for document in documents:
            document.pop("score", None)
            records.append(self._validate_document(document))
        if query.strip():
            records.sort(key=lambda record: _score(record, query), reverse=True)
        return records[:limit]

    def get(self, scheme_id: str) -> SchemeRecord | None:
        document = self._collection.find_one({"scheme_id": scheme_id}, {"_id": 0})
        return self._validate_document(document) if document else None

    def health(self) -> bool:
        return self._client.admin.command("ping").get("ok") == 1.0


class ResilientSchemeRepository:
    """Bounded process-memory copy of previously retrieved scheme records for Mongo outages."""

    def __init__(self, repository: SchemeRepository, *, max_records: int = 1000) -> None:
        self.repository = repository
        self.max_records = max_records
        self._records: dict[str, SchemeRecord] = {}
        self.degraded = False

    def _remember(self, records: list[SchemeRecord]) -> None:
        for record in records:
            self._records.pop(record.scheme_id, None)
            self._records[record.scheme_id] = record
        while len(self._records) > self.max_records:
            oldest = next(iter(self._records))
            self._records.pop(oldest)

    def search(
        self,
        query: str = "",
        filters: SchemeFilters | None = None,
        *,
        limit: int = 5,
    ) -> list[SchemeRecord]:
        try:
            records = self.repository.search(query, filters, limit=limit)
            self._remember(records)
            self.degraded = False
            return records
        except SchemaMismatchError:
            raise
        except Exception as exc:
            self.degraded = True
            logger.warning(
                "mongo_search_fallback_to_memory error_type=%s",
                type(exc).__name__,
            )
            active_filters = filters or SchemeFilters()
            matches = [
                record for record in self._records.values()
                if _matches(record, active_filters)
            ]
            if query.strip():
                matches = [record for record in matches if _score(record, query)]
                matches.sort(key=lambda record: _score(record, query), reverse=True)
            return matches[:limit]

    def get(self, scheme_id: str) -> SchemeRecord | None:
        try:
            record = self.repository.get(scheme_id)
            if record is not None:
                self._remember([record])
            self.degraded = False
            return record
        except SchemaMismatchError:
            raise
        except Exception as exc:
            self.degraded = True
            logger.warning(
                "mongo_detail_fallback_to_memory error_type=%s",
                type(exc).__name__,
            )
            return self._records.get(scheme_id)

    def health(self) -> bool:
        checker = getattr(self.repository, "health", None)
        if checker is None:
            return True
        try:
            return bool(checker())
        except Exception as exc:
            logger.warning("mongo_health_check_failed error_type=%s", type(exc).__name__)
            return False


def category_from_query(text: str) -> str | None:
    """Map common phrases to categories for deterministic offline browsing."""
    terms = {
        "farmers": ("farmer", "farming", "crop", "किसान", "விவசாய", "കർഷ", "ರೈತ", "రైతు", "शेतकरी"),
        "women": ("woman", "women", "महिला", "பெண்", "സ്ത്രീ", "ಮಹಿಳೆ", "మహిళ", "महिला"),
        "students": ("student", "school", "college", "छात्र", "மாணவர்", "വിദ്യാർത്ഥി", "ವಿದ್ಯಾರ್ಥಿ", "విద్యార్థి", "विद्यार्थी"),
        "health": ("health", "hospital", "medicine", "स्वास्थ्य", "மருத்துவ", "ആരോഗ്യ", "ಆರೋಗ್ಯ", "ఆరోగ్య", "आरोग्य"),
        "housing": ("house", "housing", "home", "आवास", "வீடு", "വീട്", "ಮನೆ", "ఇల్లు", "घरकुल"),
        "pensions": ("pension", "senior", "elder", "पेंशन", "ஓய்வூதிய", "പെൻഷൻ", "ಪಿಂಚಣಿ", "పెన్షన్", "निवृत्ती"),
        "employment": ("job", "employment", "work", "skill", "रोजगार", "வேலை", "തൊഴിൽ", "ಉದ್ಯೋಗ", "ఉపాధి", "रोजगार"),
    }
    lowered = text.casefold()
    return next((category for category, keywords in terms.items() if any(word in lowered for word in keywords)), None)
