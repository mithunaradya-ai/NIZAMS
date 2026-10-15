"""Request-scoped multilingual translation, retrieval, grounding, and speech orchestration."""

from __future__ import annotations

import base64
import json
import logging
import io
import wave

from .bhashini import BhashiniGateway
from .cache import STATIC_PHRASES_EN
from .config import LANGUAGES, SCHEME_CATEGORIES, Settings, language_for
from .errors import BhashiniCallError, ProviderError
from .grounding import ground_answer
from .llm import LLMProvider, structured_completion
from .observability import StageMetrics
from .repository import CATEGORY_LABELS, SchemeRepository, category_from_query
from .schemas import AnswerResult, GroundedAnswer, IntentResult, SchemeFilters, SchemeRecord

logger = logging.getLogger(__name__)

ERROR_MESSAGES = {
    "ta": "மன்னிக்கவும். இணைப்பில் சிக்கல் உள்ளது. தயவுசெய்து மீண்டும் முயற்சிக்கவும்.",
    "ml": "ക്ഷമിക്കണം. ബന്ധത്തിൽ ഒരു പ്രശ്നമുണ്ട്. ദയവായി വീണ്ടും ശ്രമിക്കുക.",
    "kn": "ಕ್ಷಮಿಸಿ. ಸಂಪರ್ಕದಲ್ಲಿ ಸಮಸ್ಯೆಯಿದೆ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.",
    "te": "క్షమించండి. కనెక్షన్‌లో సమస్య ఉంది. దయచేసి మళ్లీ ప్రయత్నించండి.",
    "hi": "क्षमा करें। कनेक्शन में समस्या है। कृपया फिर से कोशिश करें।",
    "mr": "क्षमस्व. जोडणीत अडचण आहे. कृपया पुन्हा प्रयत्न करा.",
    "en": "Sorry, there is a connection problem. Please try again.",
}

INTENT_SYSTEM = (
    "Extract the citizen's intent and only eligibility filters explicitly stated in their question. "
    "Never infer an age, income, state, category, gender, or occupation. "
    "Return a JSON object conforming exactly to the supplied schema."
)
ANSWER_SYSTEM = (
    "Select only relevant scheme IDs from the supplied records and return the requested JSON schema. "
    "Do not invent, infer, or alter facts. Use empty strings/lists for unsupported details. "
    "Every source ID must be present in the supplied records."
)


def _validate_wav(audio: bytes) -> bytes:
    """Require WAV container; resample nonconforming audio through ffmpeg pipes."""
    try:
        with wave.open(io.BytesIO(audio), "rb") as stream:
            if stream.getnframes() == 0:
                raise ValueError("WAV audio has no samples.")
            if stream.getnchannels() == 1 and stream.getframerate() == 16000 and stream.getsampwidth() == 2:
                return audio
    except (wave.Error, EOFError) as exc:
        raise ValueError("Audio must be a valid WAV file.") from exc

    import subprocess

    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                "pipe:0",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-sample_fmt",
                "s16",
                "-f",
                "wav",
                "pipe:1",
            ],
            input=audio,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        raise ValueError("Audio conversion is unavailable; send mono 16 kHz PCM WAV audio.") from exc
    if result.returncode != 0 or not result.stdout:
        raise ValueError("Audio could not be converted to mono 16 kHz PCM WAV.")
    try:
        with wave.open(io.BytesIO(result.stdout), "rb") as converted:
            if converted.getnchannels() != 1 or converted.getframerate() != 16000 or converted.getsampwidth() != 2:
                raise ValueError("Audio converter did not produce mono 16 kHz PCM WAV.")
    except (wave.Error, EOFError) as exc:
        raise ValueError("Audio converter returned an invalid WAV file.") from exc
    return result.stdout


def _draft_filters(text: str, category: str | None) -> SchemeFilters:
    """Conservative offline intent extraction; only category is keyword-derived."""
    resolved_category = category if category in SCHEME_CATEGORIES else category_from_query(text)
    return SchemeFilters(category=resolved_category)


def format_answer(answer: GroundedAnswer) -> str:
    """Create one translatable read-aloud string from verbatim scheme fields."""
    sections: list[str] = []
    if answer.summary:
        sections.append(f"Scheme information:\n{answer.summary}")
    for label, values in (
        ("Benefits", answer.benefits),
        ("Eligibility", answer.eligibility),
        ("Documents required", answer.documents),
        ("How to apply", answer.how_to_apply),
    ):
        if values:
            sections.append(f"{label}:\n" + "\n".join(f"- {value}" for value in values))
    if answer.missing_fields:
        labels = {
            "benefits": "benefits",
            "eligibility": "eligibility",
            "documents": "required documents",
            "how_to_apply": "application steps",
        }
        missing = ", ".join(labels[field] for field in answer.missing_fields)
        sections.append(f"The available scheme record does not provide: {missing}.")
    if answer.related_schemes:
        related = "\n".join(
            f"- {record.title}: {record.summary}" for record in answer.related_schemes
        )
        sections.append(f"Related schemes from the available records:\n{related}")
    if not answer.schemes and not answer.related_schemes:
        sections.append("You can browse a category or ask kiosk staff to check for related schemes.")
    return "\n\n".join(sections)


class ChatPipeline:
    """Coordinates Bhashini, LLM classification, scheme retrieval, and TTS per request."""

    def __init__(
        self,
        settings: Settings,
        bhashini: BhashiniGateway,
        repository: SchemeRepository,
        provider: LLMProvider | None,
        metrics: StageMetrics,
        *,
        static_cache=None,
    ) -> None:
        self.settings = settings
        self.bhashini = bhashini
        self.repository = repository
        self.provider = provider
        self.metrics = metrics
        self.static_cache = static_cache

    def _classify(
        self,
        english_text: str,
        category: str | None,
        original_text: str,
    ) -> tuple[IntentResult, bool]:
        if self.provider is None:
            return IntentResult(intent="unknown", filters=_draft_filters(original_text, category)), True
        try:
            with self.metrics.measure("llm"):
                result = structured_completion(
                    self.provider,
                    INTENT_SYSTEM,
                    english_text,
                    IntentResult,
                )
            if not isinstance(result, IntentResult):
                raise ProviderError("Intent response had an unexpected schema.")
            if category in SCHEME_CATEGORIES:
                result.filters.category = category
            elif result.filters.category not in SCHEME_CATEGORIES:
                result.filters.category = None
            return result, False
        except ProviderError as exc:
            logger.warning("llm_classification_fallback error_type=%s", type(exc).__name__)
            return IntentResult(intent="unknown", filters=_draft_filters(original_text, category)), True

    def _answer(
        self,
        english_text: str,
        records: list[SchemeRecord],
    ) -> tuple[GroundedAnswer, bool]:
        if not records:
            return ground_answer(None, records), self.provider is None
        if self.provider is None:
            return ground_answer(None, records, offline=True), True
        context = [record.model_dump(mode="json") for record in records]
        try:
            with self.metrics.measure("llm"):
                result = structured_completion(
                    self.provider,
                    ANSWER_SYSTEM,
                    f"Citizen question:\n{english_text}\n\nRetrieved scheme records:\n"
                    f"{json.dumps(context, ensure_ascii=False)}",
                    AnswerResult,
                )
            if not isinstance(result, AnswerResult):
                raise ProviderError("Answer response had an unexpected schema.")
            return ground_answer(result, records), False
        except (ProviderError, ValueError) as exc:
            logger.warning("llm_answer_fallback error_type=%s", type(exc).__name__)
            return ground_answer(None, records, offline=True), True

    def _localize(self, answer: GroundedAnswer, language: str) -> tuple[str, str | None]:
        english_text = format_answer(answer)
        if not english_text:
            english_text = "No matching scheme information was found in the available records."
        if language == "en":
            localized = english_text
        else:
            try:
                localized = self._translate(english_text, language)
            except BhashiniCallError as exc:
                logger.warning("nmt_output_fallback error_type=%s", type(exc).__name__)
                localized = ERROR_MESSAGES[language]
        audio_base64: str | None = None
        try:
            cached_audio = (
                self.static_cache.get_audio(english_text, language)
                if self.static_cache is not None
                else None
            )
            if cached_audio is not None:
                audio = cached_audio
            else:
                with self.metrics.measure("tts"):
                    audio = self.bhashini.synthesize(localized, language).unwrap()
                if self.static_cache is not None:
                    self.static_cache.store_audio(english_text, language, audio)
            audio_base64 = base64.b64encode(audio).decode("ascii")
        except BhashiniCallError as exc:
            logger.warning("tts_unavailable error_type=%s", type(exc).__name__)
            localized = self._cached_connection_error(language)
            if self.static_cache is not None:
                audio = self.static_cache.get_audio(
                    STATIC_PHRASES_EN["connection_error"],
                    language,
                )
                if audio is not None:
                    audio_base64 = base64.b64encode(audio).decode("ascii")
        return localized, audio_base64

    def _translate(self, text: str, language: str) -> str:
        if self.static_cache is not None:
            cached = self.static_cache.get_translation(text, language)
            if cached is not None:
                return cached
        with self.metrics.measure("nmt"):
            translated = self.bhashini.translate(text, "en", language).unwrap()
        if self.static_cache is not None:
            self.static_cache.store_translation(text, language, translated)
        return translated

    def _cached_connection_error(self, language: str) -> str:
        english_error = STATIC_PHRASES_EN["connection_error"]
        if self.static_cache is not None:
            cached = self.static_cache.get_translation(english_error, language)
            if cached is not None:
                return cached
        return ERROR_MESSAGES[language]

    def speak_static(self, phrase_id: str, language: str) -> dict:
        """Translate and speak an allow-listed static kiosk phrase."""
        language_for(language)
        if phrase_id not in STATIC_PHRASES_EN:
            raise ValueError("Unsupported static phrase.")
        english_text = STATIC_PHRASES_EN[phrase_id]
        if language == "en":
            localized = english_text
        else:
            try:
                localized = self._translate(english_text, language)
            except BhashiniCallError as exc:
                logger.warning("static_phrase_translation_unavailable error_type=%s", type(exc).__name__)
                localized = ERROR_MESSAGES[language]
        audio_base64: str | None = None
        if self.static_cache is not None:
            audio = self.static_cache.get_audio(english_text, language)
        else:
            audio = None
        if audio is None:
            try:
                with self.metrics.measure("tts"):
                    audio = self.bhashini.synthesize(localized, language).unwrap()
                if self.static_cache is not None:
                    self.static_cache.store_audio(english_text, language, audio)
            except BhashiniCallError as exc:
                logger.warning("static_phrase_tts_unavailable error_type=%s", type(exc).__name__)
        if audio is not None:
            audio_base64 = base64.b64encode(audio).decode("ascii")
        return {"language": language, "text": localized, "audio_base64": audio_base64}

    def answer_text(self, text: str, language: str, category: str | None = None) -> dict:
        """Run the shared typed/touch question path and return a localized grounded answer."""
        language_for(language)
        question = text.strip()
        if not question:
            raise ValueError("Question must not be empty.")
        degraded = self.provider is None
        if language == "en":
            english_text = question
        else:
            try:
                with self.metrics.measure("nmt"):
                    english_text = self.bhashini.translate(question, language, "en").unwrap()
            except BhashiniCallError as exc:
                logger.warning("nmt_input_fallback error_type=%s", type(exc).__name__)
                english_text = question
                degraded = True
        intent, classifier_fallback = self._classify(english_text, category, question)
        degraded = degraded or classifier_fallback
        with self.metrics.measure("retrieval"):
            records = self.repository.search(
                english_text,
                intent.filters,
                limit=self.settings.max_retrieval_results,
            )
            resolved_category = category or intent.filters.category
            if not records and resolved_category:
                records = self.repository.search(
                    "", SchemeFilters(category=resolved_category), limit=self.settings.max_retrieval_results
                )
        degraded = degraded or bool(getattr(self.repository, "degraded", False))
        answer, answer_fallback = self._answer(english_text, records)
        degraded = degraded or answer_fallback
        localized, audio_base64 = self._localize(answer, language)
        return {
            "language": language,
            "intent": intent.intent,
            "answer": answer.model_dump(mode="json"),
            "reply": localized,
            "audio_base64": audio_base64,
            "offline": degraded or audio_base64 is None,
        }

    def answer_audio(self, audio: bytes, language: str, category: str | None = None) -> dict:
        """Transcribe request-scoped WAV bytes and forward recognized text through the same path."""
        language_for(language)
        normalized = _validate_wav(audio)
        with self.metrics.measure("asr"):
            recognized = self.bhashini.transcribe(normalized, language).unwrap()
        response = self.answer_text(recognized, language, category)
        response["transcript"] = recognized
        return response

    def browse(self, category: str, language: str) -> dict:
        """Retrieve category records through the same translation and read-aloud services."""
        language_for(language)
        if category not in SCHEME_CATEGORIES:
            raise ValueError("Unsupported scheme category.")
        with self.metrics.measure("retrieval"):
            records = self.repository.search("", SchemeFilters(category=category), limit=10)
        degraded = self.provider is None or bool(getattr(self.repository, "degraded", False))
        answer = ground_answer(None, records, offline=degraded)
        localized, audio_base64 = self._localize(answer, language)
        return {
            "language": language,
            "category": category,
            "category_label": CATEGORY_LABELS[category],
            "answer": answer.model_dump(mode="json"),
            "reply": localized,
            "audio_base64": audio_base64,
            "offline": degraded or audio_base64 is None,
        }

    def scheme_detail(self, scheme_id: str, language: str) -> dict:
        """Present and read aloud one repository-owned scheme record."""
        language_for(language)
        record = self.repository.get(scheme_id)
        if record is None:
            raise LookupError("Scheme record was not found.")
        degraded = self.provider is None or bool(getattr(self.repository, "degraded", False))
        answer = ground_answer(None, [record], offline=degraded)
        localized, audio_base64 = self._localize(answer, language)
        return {
            "language": language,
            "answer": answer.model_dump(mode="json"),
            "reply": localized,
            "audio_base64": audio_base64,
            "offline": degraded or audio_base64 is None,
        }
