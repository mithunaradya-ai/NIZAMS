# Multilingual Government Schemes Kiosk

Voice-first, touch-first citizen kiosk implemented separately from the bundled
`bhashini_client` SDK. The SDK source and its model table were inspected before
building this application. The kiosk uses FastAPI, Pydantic, a small plain HTML/CSS/JS
client, and a repository boundary; the workspace had no existing application framework
or UI to extend.

## SDK findings

- Import `BhashiniClient` from `bhashini_client`; the API key is passed to its constructor or read from `BHASHINI_API_KEY`.
- Text/audio calls include `asr`, `nmt`, `tts`, text/audio language detection, transliteration, normalization, inverse normalization, and denoising.
- SDK failures are returned as strings beginning `Input Error:`, `Validation Error:`, or `API Error:`; `BhashiniGateway` wraps and raises these as `BhashiniCallError`.
- `get_available_models(service, language=...)` supplies supported `serviceId` values; the gateway chooses and caches a model at startup and accepts JSON per-language overrides.
- ASR batch processing expects WAV; the kiosk resamples to mono, signed 16-bit, 16 kHz using ffmpeg pipes, without writing the user's recording to disk.
- ASR has both batch and WebSocket streaming entry points. Streaming accepts raw PCM chunks at 16 kHz; the kiosk currently uses browser VAD and batch ASR.
- In the inspected SDK model table, ASR, NMT and TTS all include English (`en`), Hindi (`hi`), Marathi (`mr`), Kannada (`kn`), Malayalam (`ml`), Tamil (`ta`) and Telugu (`te`).
- The SDK has no LLM or chatbot. Its source imports `audioop`, which was removed from Python 3.13; use Python 3.10–3.12 for the bundled SDK unless its compatibility is separately addressed.

The mocked transport smoke check replaced `RequestHandler.post` with a function
returning `None`: text-language detection, NMT, and TTS each returned an `API Error:`
string. This confirmed the SDK's error shape before adding the typed wrapper.

## Architecture

```text
Browser microphone / typed question / category browse
  -> VAD and 16 kHz mono WAV in browser memory
  -> FastAPI (stateless request; no audio upload spool)
  -> Bhashini ASR -> Bhashini NMT (citizen language to English)
  -> intent and explicit filters (configured LLM or local fallback)
  -> SchemeRepository (MongoDB contract or marked development mock)
  -> answer selection (configured LLM or keyword fallback)
  -> grounding projection from retrieved Pydantic records only
  -> Bhashini NMT -> Bhashini TTS -> browser speaker
```

```text
kiosk_app/
  api.py                 FastAPI app factory, health endpoint, stateless routes
  config.py              .env configuration, languages, categories, limits
  schemas.py             Canonical Pydantic scheme and request/response contracts
  bhashini.py             SDK model selection, typed results, errors, memory-only text cache
  llm.py                  Gemini, Anthropic, and OpenAI-compatible JSON adapters
  repository.py           SchemeRepository protocol, Mongo adapter, dev mock and search
  grounding.py             Citation validation and record-only answer projection
  pipeline.py              Typed/voice/browse orchestration, localization and VAD WAV validation
  cache.py                 Disk cache allow-listed to non-personal static phrases
  observability.py         PII-free JSON logs and per-stage latency metrics
  systemd_watchdog.py      systemd readiness and health-checked watchdog notifications
  main.py                  Server entry point; access logging disabled
  smoke_cli.py             WAV-file pipeline harness
kiosk_web/
  index.html kiosk.css kiosk.js
deploy/
  scheme-kiosk.service kiosk-autostart.sh
scripts/
  generate_static_audio.py
kiosk_tests/
  wrapper, grounding, adapter, repository, mocked integration tests
```

## Data contract and grounding

MongoDB documents must match `SchemeRecord` in `schemas.py`, with canonical fields
`scheme_id`, `title`, `summary`, `benefits`, `eligibility`, `documents`, `how_to_apply`,
`categories`, `eligible_age_min`, `eligible_age_max`, `income_min`, `income_max`,
`eligible_states`, `genders`, `occupations`, `source_url`, and
`development_sample`. The schema rejects extra or invalid fields and returns a
field-path-only `mongo_schema_mismatch` event so the teammate can identify a contract
mismatch without placing document values in logs. The adapter expects a text index over
`title`, `summary`, `benefits`, `eligibility`, `documents`, `how_to_apply`, and
`categories`; if Mongo reports that the index is missing, it logs the condition and uses
a bounded metadata-filtered scan plus local keyword ranking. Other Mongo errors are
handled using a bounded in-process cache of previously retrieved, validated scheme
records and local keyword/metadata filtering. Schema mismatches are not hidden or cached.

The ten in-memory records are explicitly labelled **DEVELOPMENT SAMPLE — not official**
and contain no asserted eligibility, amounts, dates, phone numbers, or URLs. Configure
MongoDB before any public/production kiosk use. Admin writes remain outside this
read-only repository interface.

Intent/filter JSON is validated with Pydantic. The LLM answer draft is also structured,
but its generated text fields are intentionally discarded: the kiosk validates its
scheme IDs against retrieved IDs, then copies benefits, eligibility, documents,
application steps and titles verbatim from the repository records. This makes a
hallucinated payment, qualification, deadline, or link unable to enter the displayed
scheme details through the answer-generation step. Missing fields are called out and
other retrieved records are offered as related schemes.

## Setup and run

Use Python 3.10–3.12. The existing workspace `.venv` is Python 3.15, does not contain
the SDK's declared `requests` dependency, and cannot import the SDK's `audioop` usage.
It was left unchanged as requested. Install the kiosk in a separate supported runtime
(do not reuse or modify that protected `.venv`):

```powershell
py -3.12 -m venv .venv-kiosk
.\.venv-kiosk\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r kiosk_requirements.txt
python -m pip install -e .
Copy-Item .env.example .env
```

Edit `.env` with `BHASHINI_API_KEY`. `LLM_PROVIDER=none` is the offline/default mode;
to enable an approved provider, set `LLM_PROVIDER`, `LLM_API_KEY`, and `LLM_MODEL`.
For `openai-compatible`, optionally set `LLM_BASE_URL`; for Anthropic it can override
the Messages endpoint. No keys belong in source code or logs. An enabled remote LLM
receives the translated citizen question and retrieved scheme records; use only a
provider approved for this data and tell kiosk users not to enter names, phone numbers,
account details, or other identifiers.

With no Mongo URI, local development uses the clearly labelled sample repository:

```powershell
python -m kiosk_app
```

Open `http://127.0.0.1:8080`. Check `http://127.0.0.1:8080/health`.
To use MongoDB set `MONGO_URI`, `MONGO_DATABASE`, and `MONGO_COLLECTION`; set
`KIOSK_ENV=production` to require Mongo instead of silently starting with the mock.
The schema and text index above must be agreed with the data owner before connecting
their collection.

To test the voice pipeline from a WAV without the UI:

```powershell
python -m kiosk_app.smoke_cli .\question.wav --language ta
```

The WAV is read into memory. Non-mono/non-16 kHz input is converted through ffmpeg
pipes; install ffmpeg or supply mono 16 kHz, 16-bit PCM WAV.

Run the focused application tests in the supported, fully provisioned runtime:

```powershell
python -m pytest kiosk_tests
```

The provider tests stub HTTP; integration tests stub both Bhashini and MongoDB.
No live Bhashini, LLM, or Mongo credentials are needed for that test suite.

## Raspberry Pi OS deployment

Install system packages (package names can differ between Raspberry Pi OS releases):

```bash
sudo apt update
sudo apt install python3.11-venv python3-pip ffmpeg chromium curl \
  alsa-utils fonts-noto-core fonts-noto-extra
```

Create a dedicated service account and deployment directories, place this project at
`/opt/scheme-kiosk`, then as that account create its venv and install the app:

```bash
sudo useradd --system --create-home --groups audio kiosk
sudo mkdir -p /opt/scheme-kiosk/data/cache
sudo chown -R kiosk:kiosk /opt/scheme-kiosk
sudo -u kiosk python3.11 -m venv /opt/scheme-kiosk/.venv
sudo -u kiosk /opt/scheme-kiosk/.venv/bin/pip install \
  -r /opt/scheme-kiosk/kiosk_requirements.txt
sudo -u kiosk /opt/scheme-kiosk/.venv/bin/pip install -e /opt/scheme-kiosk
sudo install -m 600 /opt/scheme-kiosk/.env.example /opt/scheme-kiosk/.env
```

Set real credentials and Mongo connection values in `/opt/scheme-kiosk/.env`; use
`KIOSK_ENV=production`. Generate the static greeting and connection-error audio during
provisioning, while connectivity and the Bhashini key are available:

```bash
sudo -u kiosk sh -c 'cd /opt/scheme-kiosk && .venv/bin/python scripts/generate_static_audio.py'
```

Install and enable the service; `Restart=always` plus the health-checked systemd
watchdog restarts a stopped or unresponsive service:

```bash
sudo cp /opt/scheme-kiosk/deploy/scheme-kiosk.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now scheme-kiosk
sudo systemctl status scheme-kiosk
```

For desktop autologin, install the kiosk user's script and create
`~/.config/autostart/scheme-kiosk.desktop` with:

```ini
[Desktop Entry]
Type=Application
Name=Government Schemes Kiosk
Exec=/opt/scheme-kiosk/deploy/kiosk-autostart.sh
X-GNOME-Autostart-enabled=true
```

Make `deploy/kiosk-autostart.sh` executable. It waits for `/health`, then starts
Chromium in full-screen kiosk mode. Confirm the installed browser binary is `chromium`;
adjust the script if the OS names it differently. Connect the USB mic/speaker and verify with
`arecord -l` and `aplay -l`; ensure the service user belongs to the `audio` group.
For PulseAudio/PipeWire systems, select the USB devices as the active input/output in
the kiosk desktop session.

## Verification by stage

| Stage | Manual check | Mocked / external |
| --- | --- | --- |
| Config and SDK wrapper | Set one language override; test typed errors and selected models | SDK network calls mocked in tests |
| Audio/VAD | Speak, pause for endpointing, verify transcript; try a non-16 kHz WAV in CLI | USB hardware and ffmpeg behavior are device/runtime dependent |
| LLM and grounding | Ask for a benefit; inspect that shown text is copied from a retrieved record | Provider HTTP is stubbed in tests; production account is external |
| Repository | Search a category, inspect mismatch event with a deliberately invalid document | Sample mode is fake; Mongo collection/index belong to teammate |
| API | Check `/health`, `/api/config`, typed and WAV endpoints | Bhashini, Mongo and LLM can be injected/mocked |
| UI | Try all seven scripts, voice, keyboard, browse, read-aloud, and 90 s reset | Touchscreen, browser fonts and audio need Pi validation |
| Pi deployment | Reboot Pi, verify service watchdog and Chromium autostart | ALSA/PulseAudio device routing is hardware-specific |
| Tests/docs | Run `python -m pytest kiosk_tests` in Python 3.10–3.12 | This workspace's protected Python 3.15 `.venv` cannot run SDK tests |

## Privacy, caches, and performance

The browser keeps captured audio only in memory and sends JSON/base64; the server
resamples through pipes and calls the SDK's source-verified `TTSService.synthesize`
base64 option. It does not persist user audio. Dynamic user translations and generated speech are not cached, because they can contain
personal details. The disk cache and build-time audio generator are restricted to an explicit
allow-list of static, non-personal phrases (greeting, generic error, no-results),
keyed by phrase/language/voice. This privacy boundary intentionally takes precedence
over persisting arbitrary user translation or TTS content. Reset clears the browser
question, result, microphone buffers, and playback.

Structured JSON logs contain event names, error types, stage names and durations only;
HTTP access logs are disabled, API responses are no-store, and `/health` exposes
per-stage count/average latency. Typical latency is dominated by remote serial
round-trips: ASR, input translation, LLM intent/filter extraction, retrieval, LLM
answer selection, output translation and TTS. A sub-4-second end-of-speech to first
audio response cannot be guaranteed with two LLM calls and Bhashini network calls.
Use nearby low-latency services, a fast configured model, static phrase audio, small
retrieval limits, a healthy connection, and measure the reported stage timings on the
actual Pi before claiming that target.

## Assumptions and open questions for integration

- The teammate's Mongo collection will either adopt the canonical contract above or
  provide a reviewed field mapping. What are the actual document fields, schema version,
  and text-index provisioning owner?
- Scheme values and official sources are external. Who signs off on data freshness,
  official URLs, state-specific wording, and the public use of each record?
- Which LLM provider, model, region, retention policy and government data-processing
  approval should be used? `none` remains the safe default until approved.
- Which Raspberry Pi OS image/desktop release and Chromium binary will be deployed?
  Confirm screen rotation, audio backend, and the kiosk user's session autostart path.
- Bhashini's inspected request handler has a fixed 30-second transport timeout.
  Retry count/backoff are configurable in this app, but timeout control for that bundled
  SDK call needs an upstream SDK change or an agreed wrapper extension.
- No commits were created: the supplied workspace is not a Git repository.
