"""Canonical data-transfer schemas shared with the MongoDB repository contract."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SchemeFilters(BaseModel):
    """Optional eligibility filters extracted from a citizen's request."""

    model_config = ConfigDict(extra="forbid")

    age: int | None = Field(default=None, ge=0, le=120)
    income: float | None = Field(default=None, ge=0)
    state: str | None = None
    category: str | None = None
    gender: str | None = None
    occupation: str | None = None


class IntentResult(BaseModel):
    """Structured intent and filter extraction output."""

    model_config = ConfigDict(extra="forbid")

    intent: Literal["benefits", "eligibility", "documents", "application", "browse", "unknown"]
    filters: SchemeFilters


class SchemeRecord(BaseModel):
    """Canonical MongoDB scheme document; incompatible source fields are rejected."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    scheme_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = ""
    benefits: list[str] = Field(default_factory=list)
    eligibility: list[str] = Field(default_factory=list)
    documents: list[str] = Field(default_factory=list)
    how_to_apply: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    eligible_age_min: int | None = Field(default=None, ge=0, le=120)
    eligible_age_max: int | None = Field(default=None, ge=0, le=120)
    income_min: float | None = Field(default=None, ge=0)
    income_max: float | None = Field(default=None, ge=0)
    eligible_states: list[str] = Field(default_factory=list)
    genders: list[str] = Field(default_factory=list)
    occupations: list[str] = Field(default_factory=list)
    source_url: str | None = None
    development_sample: bool = False


class AnswerResult(BaseModel):
    """Structured draft returned by an LLM before grounding enforcement."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    benefits: list[str]
    eligibility: list[str]
    documents: list[str]
    how_to_apply: list[str]
    source_scheme_ids: list[str]


class GroundedAnswer(BaseModel):
    """Response fields copied from retrieved records after validating citations."""

    model_config = ConfigDict(extra="forbid")

    summary: str
    benefits: list[str]
    eligibility: list[str]
    documents: list[str]
    how_to_apply: list[str]
    source_scheme_ids: list[str]
    schemes: list[SchemeRecord]
    related_schemes: list[SchemeRecord] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    offline: bool = False


class ChatRequest(BaseModel):
    """Typed kiosk question; personal details are processed only for this request."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=4000)
    language: str
    category: str | None = None


class ChatAudioRequest(BaseModel):
    """Base64 WAV request kept in memory instead of framework upload temp files."""

    model_config = ConfigDict(extra="forbid")

    audio_base64: str = Field(min_length=1, max_length=16_777_216)
    language: str
    category: str | None = None


class BrowseRequest(BaseModel):
    """Category selected through touch navigation."""

    model_config = ConfigDict(extra="forbid")

    category: str
    language: str
