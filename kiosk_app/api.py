"""FastAPI application factory and stateless kiosk endpoints."""

from __future__ import annotations

import base64
import binascii
import logging
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.request import urlopen

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from .bhashini import BhashiniGateway
from .cache import StaticPhraseCache
from .config import LANGUAGES, SCHEME_CATEGORIES, Settings
from .errors import BhashiniCallError, KioskError, SchemaMismatchError
from .llm import LLMProvider, create_provider
from .observability import JsonFormatter, StageMetrics
from .pipeline import ChatPipeline, ERROR_MESSAGES
from .repository import (
    InMemorySchemeRepository,
    MongoSchemeRepository,
    ResilientSchemeRepository,
    SchemeRepository,
)
from .schemas import BrowseRequest, ChatAudioRequest, ChatRequest
from .systemd_watchdog import notify

logger = logging.getLogger("scheme_kiosk")
WEB_DIRECTORY = Path(__file__).resolve().parent.parent / "kiosk_web"
DEFAULT_PROVIDER = object()
_LOGGING_CONFIGURED = False


def _configure_logging() -> None:
    global _LOGGING_CONFIGURED
    if _LOGGING_CONFIGURED:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").disabled = True
    _LOGGING_CONFIGURED = True


def create_app(
    settings: Settings | None = None,
    *,
    repository: SchemeRepository | None = None,
    provider: LLMProvider | None | object = DEFAULT_PROVIDER,
    bhashini: BhashiniGateway | None = None,
    metrics: StageMetrics | None = None,
) -> FastAPI:
    """Build the app with injectable boundaries for tests and external deployments."""
    _configure_logging()
    resolved_settings = settings or Settings.from_env()
    if repository is None:
        repository = InMemorySchemeRepository() if not resolved_settings.mongo_uri else ResilientSchemeRepository(
            MongoSchemeRepository(
                resolved_settings.mongo_uri,
                resolved_settings.mongo_database,
                resolved_settings.mongo_collection,
            )
        )
        if not resolved_settings.mongo_uri:
            logger.warning(
                "development_scheme_repository_selected",
                extra={"event": "development_scheme_repository_selected", "fields": {}},
            )
    resolved_bhashini = bhashini or BhashiniGateway(resolved_settings)
    resolved_provider = create_provider(resolved_settings) if provider is DEFAULT_PROVIDER else provider
    resolved_metrics = metrics or StageMetrics()
    cache = StaticPhraseCache(resolved_settings.cache_directory)
    pipeline = ChatPipeline(
        resolved_settings,
        resolved_bhashini,
        repository,
        resolved_provider,  # type: ignore[arg-type]
        resolved_metrics,
        static_cache=cache,
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        stop = threading.Event()
        watchdog_usec = int(os.environ.get("WATCHDOG_USEC", "0") or "0")
        interval = max(5.0, watchdog_usec / 2_000_000) if watchdog_usec else 0

        def monitor_health() -> None:
            while not stop.wait(interval):
                try:
                    with urlopen(f"http://127.0.0.1:{resolved_settings.port}/health", timeout=4) as response:
                        if response.status == 200:
                            notify("WATCHDOG=1")
                except Exception:
                    logger.warning("systemd_health_watchdog_check_failed")

        notify("READY=1")
        watchdog_thread = None
        if interval:
            watchdog_thread = threading.Thread(target=monitor_health, daemon=True)
            watchdog_thread.start()
        try:
            yield
        finally:
            stop.set()
            if watchdog_thread:
                watchdog_thread.join(timeout=1)
            notify("STOPPING=1")

    app = FastAPI(
        title="Multilingual Government Schemes Kiosk",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = resolved_settings
    app.state.repository = repository
    app.state.pipeline = pipeline
    app.state.metrics = resolved_metrics

    @app.middleware("http")
    async def prevent_session_data_caching(request: Request, call_next):
        response = await call_next(request)
        if request.url.path == "/" or request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, max-age=0"
            response.headers["Pragma"] = "no-cache"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request_handler(_request: Request, _exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"detail": "Please check the kiosk input and try again."})

    @app.exception_handler(SchemaMismatchError)
    async def schema_mismatch_handler(_request: Request, _exc: SchemaMismatchError):
        logger.error("scheme_data_contract_mismatch", extra={"event": "scheme_data_contract_mismatch"})
        return JSONResponse(
            status_code=503,
            content={"detail": "Scheme data is temporarily unavailable. Please ask staff for help."},
        )

    @app.exception_handler(BhashiniCallError)
    async def bhashini_error_handler(request: Request, _exc: BhashiniCallError):
        language = request.query_params.get("language", "en")
        message = ERROR_MESSAGES.get(language, ERROR_MESSAGES["en"])
        try:
            voice = await run_in_threadpool(pipeline.speak_static, "connection_error", language)
        except Exception as exc:
            logger.warning("localized_bhashini_error_audio_unavailable error_type=%s", type(exc).__name__)
            voice = {"audio_base64": None}
        return JSONResponse(status_code=503, content={"detail": message, **voice})

    @app.exception_handler(KioskError)
    async def kiosk_error_handler(request: Request, _exc: KioskError):
        language = request.query_params.get("language", "en")
        message = ERROR_MESSAGES.get(language, ERROR_MESSAGES["en"])
        try:
            voice = await run_in_threadpool(pipeline.speak_static, "connection_error", language)
        except Exception as exc:
            logger.warning("localized_service_error_audio_unavailable error_type=%s", type(exc).__name__)
            voice = {"audio_base64": None}
        return JSONResponse(status_code=503, content={"detail": message, **voice})

    @app.get("/", include_in_schema=False)
    def home():
        return FileResponse(WEB_DIRECTORY / "index.html")

    @app.get("/health")
    def health():
        repository_ok = True
        health_check = getattr(repository, "health", None)
        if health_check:
            try:
                repository_ok = bool(health_check())
            except Exception as exc:
                logger.warning("repository_health_failed error_type=%s", type(exc).__name__)
                repository_ok = False
        return JSONResponse(
            status_code=200,
            content={
                "status": "ok" if repository_ok else "degraded",
                "repository": "available" if repository_ok else "unavailable",
                "repository_mode": (
                    "mongodb-resilient"
                    if isinstance(repository, ResilientSchemeRepository)
                    else "mongodb"
                    if isinstance(repository, MongoSchemeRepository)
                    else "development-mock"
                    if isinstance(repository, InMemorySchemeRepository)
                    else "custom"
                ),
                "metrics": resolved_metrics.snapshot(),
            },
        )

    @app.get("/api/config")
    def config():
        return {
            "languages": [
                {
                    "code": item.code,
                    "name": item.name,
                    "native_name": item.native_name,
                    "icon": item.icon,
                }
                for item in LANGUAGES
            ],
            "categories": [{"id": item, "label": item.title()} for item in SCHEME_CATEGORIES],
            "idle_timeout_seconds": resolved_settings.idle_timeout_seconds,
        }

    @app.get("/api/greeting")
    async def greeting(language: str = "en"):
        try:
            return await run_in_threadpool(pipeline.speak_static, "greeting", language)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Unsupported language.") from exc

    @app.get("/api/error-phrase")
    async def error_phrase(language: str = "en"):
        if language not in {item.code for item in LANGUAGES}:
            raise HTTPException(status_code=400, detail="Unsupported language.")
        return await run_in_threadpool(pipeline.speak_static, "connection_error", language)

    @app.post("/api/chat")
    def chat(body: ChatRequest):
        try:
            return pipeline.answer_text(body.text, body.language, body.category)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Please choose a supported language and category.") from exc
        except BhashiniCallError:
            voice = pipeline.speak_static("connection_error", body.language)
            return JSONResponse(status_code=503, content={"detail": ERROR_MESSAGES.get(body.language, ERROR_MESSAGES["en"]), **voice})
        except KioskError as exc:
            if isinstance(exc, SchemaMismatchError):
                return JSONResponse(
                    status_code=503,
                    content={"detail": ERROR_MESSAGES.get(body.language, ERROR_MESSAGES["en"])},
                )
            logger.error("chat_domain_error error_type=%s", type(exc).__name__)
            raise
        except Exception as exc:
            logger.error("chat_request_failed error_type=%s", type(exc).__name__)
            raise HTTPException(
                status_code=503,
                detail=ERROR_MESSAGES.get(body.language, ERROR_MESSAGES["en"]),
            ) from exc

    @app.post("/api/chat/voice")
    async def chat_voice(body: ChatAudioRequest):
        language = body.language
        max_encoded_bytes = 4 * ((resolved_settings.max_audio_bytes + 2) // 3)
        if len(body.audio_base64) > max_encoded_bytes:
            raise HTTPException(status_code=413, detail=ERROR_MESSAGES.get(language, ERROR_MESSAGES["en"]))
        try:
            content = base64.b64decode(body.audio_base64, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise HTTPException(status_code=400, detail=ERROR_MESSAGES.get(language, ERROR_MESSAGES["en"])) from exc
        if len(content) > resolved_settings.max_audio_bytes:
            raise HTTPException(status_code=413, detail=ERROR_MESSAGES.get(language, ERROR_MESSAGES["en"]))
        try:
            return await run_in_threadpool(pipeline.answer_audio, content, language, body.category)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=ERROR_MESSAGES.get(language, ERROR_MESSAGES["en"])) from exc
        except BhashiniCallError:
            voice = await run_in_threadpool(pipeline.speak_static, "connection_error", language)
            return JSONResponse(status_code=503, content={"detail": ERROR_MESSAGES.get(language, ERROR_MESSAGES["en"]), **voice})
        except SchemaMismatchError:
            return JSONResponse(
                status_code=503,
                content={"detail": ERROR_MESSAGES.get(language, ERROR_MESSAGES["en"])},
            )
        except Exception as exc:
            logger.error("voice_request_failed error_type=%s", type(exc).__name__)
            raise HTTPException(status_code=503, detail=ERROR_MESSAGES.get(language, ERROR_MESSAGES["en"])) from exc

    @app.post("/api/browse")
    def browse(body: BrowseRequest):
        try:
            return pipeline.browse(body.category, body.language)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Please choose a supported language and category.") from exc

    @app.get("/api/schemes/{scheme_id}")
    def scheme_detail(scheme_id: str, language: str = "en"):
        try:
            return pipeline.scheme_detail(scheme_id, language)
        except LookupError as exc:
            raise HTTPException(status_code=404, detail="Scheme record was not found.") from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Please choose a supported language.") from exc

    app.mount("/assets", StaticFiles(directory=WEB_DIRECTORY), name="assets")
    return app
