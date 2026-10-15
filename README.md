
# Bhashini Client SDK (Python)

Python SDK for the Bhashini Inference API. It provides a unified `BhashiniClient` for speech, text, speaker, and image-language services, while keeping validation, model routing, payload construction, and response parsing inside dedicated service modules.

## Overview

This SDK wraps the Bhashini API into a clean Python interface. Each service is modular and independently handles:

- input validation
- payload construction
- API dispatch through a shared request handler
- response parsing

Supported service categories:

| Category | Services |
| --- | --- |
| Speech / Audio | ASR, TTS, Audio Language Detection, Speaker Diarization, Speaker Enrollment, Speaker Verification, Voice Cloning, Denoiser |
| Text | NMT, Transliteration, Text Language Detection, Text Normalization, Inverse Text Normalization, NER |
| Vision | OCR, Image Language Detection |

## Architecture

The main flow is:

`User Input -> BhashiniClient -> Service Validation -> Payload Construction -> RequestHandler -> Response Parsing`

Core design principles:

- Service isolation: each service owns its own validation and parsing logic.
- Shared transport: HTTP/auth handling is centralized in `request_handler.py`.
- Model-aware routing: selected services use primary and fallback `serviceId` routing.
- Flexible inputs: several services accept file paths, base64 data, and URIs.
- Structured SDK errors: services return `Input Error:`, `Validation Error:`, or `API Error:` messages.

## Project Structure

```text
bhashini-client/
├── bhashini_client/
│   ├── __init__.py
│   ├── config.py
│   ├── core.py
│   ├── models_info.py
│   ├── services/
│   │   ├── asr_service.py
│   │   ├── nmt_service.py
│   │   ├── tts_service.py
│   │   ├── transliteration_service.py
│   │   ├── language_detection_service.py
│   │   ├── audio_language_detection_service.py
│   │   ├── ner_service.py
│   │   ├── ocr_service.py
│   │   ├── speaker_diarization_service.py
│   │   ├── speaker_enrollment_service.py
│   │   ├── speaker_verification_service.py
│   │   ├── voice_cloning_service.py
│   │   ├── image_lang_detection_service.py
│   │   ├── text_normalization_service.py
│   │   ├── itn_service.py
│   │   ├── denoiser_service.py
│   │   ├── audio_input_utils.py
│   │   └── service_utils.py
│   └── utils/
│       └── request_handler.py
├── tests/
├── demo.py
├── requirements.txt
└── run_all_checks.ps1
```

## Installation

Requirements:

- Python `3.8+`

Install from PyPI:

```bash
pip install bhashini-client-sdk
```

For Google Colab, use:

```python
%pip install -U bhashini-client-sdk
```

For local development from this repository:

```bash
pip install -r requirements.txt
pip install -e .
```

## Authentication

The SDK reads the API key from `BHASHINI_API_KEY`, or you can pass it explicitly when creating the client.

Environment variable:

```powershell
$env:BHASHINI_API_KEY="your_api_key"
```

Or in code:

```python
from bhashini_client import BhashiniClient

client = BhashiniClient(api_key="your_api_key")
```

In notebooks and Colab, prefer `getpass` so the key is not printed or saved directly in the notebook:

```python
import os
from getpass import getpass
from bhashini_client import BhashiniClient

os.environ["BHASHINI_API_KEY"] = getpass("Enter BHASHINI API key: ")
client = BhashiniClient(os.environ["BHASHINI_API_KEY"])

print("API key loaded:", bool(client.handler.api_key))
```

## Use In Colab, Notebook, And VS Code

### Google Colab

Run these cells in order in every new Colab runtime:

```python
%pip install -U bhashini-client-sdk
```

```python
import os
from getpass import getpass
from bhashini_client import BhashiniClient

os.environ["BHASHINI_API_KEY"] = getpass("Enter BHASHINI API key: ")
client = BhashiniClient(os.environ["BHASHINI_API_KEY"])

print("API key loaded:", bool(client.handler.api_key))
```

Upload local files before using audio or image services:

```python
from google.colab import files

uploaded = files.upload()
file_path = list(uploaded.keys())[0]
print("Uploaded:", file_path)
```

Colab runs on a remote machine, so local paths such as `C:\Users\name\Downloads\sample.wav` do not work there. Use the uploaded filename, for example `sample.wav`.

### Jupyter Notebook

Install once in a notebook cell:

```python
%pip install -U bhashini-client-sdk
```

Then create the client:

```python
import os
from getpass import getpass
from bhashini_client import BhashiniClient

os.environ["BHASHINI_API_KEY"] = getpass("Enter BHASHINI API key: ")
client = BhashiniClient(os.environ["BHASHINI_API_KEY"])
```

### VS Code Or Local Python

Install in your terminal:

```bash
pip install -U bhashini-client-sdk
```

Set the API key in PowerShell:

```powershell
$env:BHASHINI_API_KEY="your_api_key"
```

Use it in Python:

```python
import os
from bhashini_client import BhashiniClient

client = BhashiniClient(os.environ["BHASHINI_API_KEY"])
print(client.nmt("Hello", "en", "hi"))
```

If you are testing this repository before a PyPI release, install the local checkout in editable mode:

```bash
pip install -e .
```

## Quick Start

Minimal text translation check:

```python
import os
from bhashini_client import BhashiniClient

client = BhashiniClient(os.environ["BHASHINI_API_KEY"])

print(client.text_language_detection("Hello world"))
print(client.nmt("Hello", "en", "hi"))
```

Choose a specific Bhashini backend model by passing `service_id`:

```python
print(
    client.nmt(
        "Hello",
        "en",
        "hi",
        service_id="bhashini/iiith/nmt-all",
    )
)
```

Upload and test an audio file in Colab:

```python
from google.colab import files
from bhashini_client import BhashiniClient
import os

uploaded = files.upload()
audio_path = list(uploaded.keys())[0]

client = BhashiniClient(os.environ["BHASHINI_API_KEY"])

print(client.audio_language_detection(audio_path))
print(client.asr(audio_path, "hi"))
```

Generate TTS output:

```python
from IPython.display import Audio, display

output_path = client.tts("Hello from Bhashini", "en", output_file="output.wav")
print(output_path)
display(Audio(output_path))
```

Important Colab notes:

- Run `%pip install -U bhashini-client-sdk` in every new runtime.
- Do not use Windows paths like `C:\Users\...\sample.wav` in Colab. Upload the file and use the uploaded filename.
- Do not overwrite a working authenticated client with `client = BhashiniClient()` unless `BHASHINI_API_KEY` is already set in the same runtime.
- Audio services work best with WAV audio containing real speech. ASR and Audio Language Detection normalize many WAV files internally, but 16 kHz mono WAV is the safest format.

## Common Service Examples

### Discover Service IDs

Use model discovery when you want to choose a specific Bhashini backend model:

```python
from bhashini_client import get_available_models

print(get_available_models("nmt", language=("en", "hi")))
print(get_available_models("asr", language="hi"))
print(get_available_models("tts", language="en"))
```

Then pass one returned `serviceId` value:

```python
models = get_available_models("nmt", language=("en", "hi"))
service_id = models[0]["serviceId"]

print(client.nmt("Hello", "en", "hi", service_id=service_id))
```

### NMT

```python
print(client.nmt("Hello, how are you?", "en", "hi"))
```

With a selected model:

```python
print(
    client.nmt(
        "Hello, how are you?",
        "en",
        "hi",
        service_id="bhashini/iiith/nmt-all",
    )
)
```

### ASR

```python
print(client.asr("sample.wav", "hi"))
```

### Audio Language Detection

```python
print(client.audio_language_detection("sample.wav"))
```

### TTS

```python
from IPython.display import Audio, display

output_path = client.tts("Hello from Bhashini", "en", output_file="output.wav")
print(output_path)
display(Audio(output_path))
```

### Transliteration

```python
print(client.transliteration("namaste", "en", "hi"))
```

### Text Language Detection

```python
print(client.text_language_detection("Hello world"))
```

### OCR

```python
print(client.ocr("sample.png", "en"))
```

### Image Language Detection

```python
print(client.image_language_detection("sample.png"))
```

### NER

```python
print(client.ner("Narendra Modi went to Delhi.", "en"))
```

### Speaker Services

```python
speaker_id = client.speaker_enrollment("sample.wav", "demo_speaker")
print(speaker_id)

print(client.speaker_verification("sample.wav", speaker_id))
print(client.speaker_diarization("sample.wav"))
```

### Voice Cloning

```python
print(
    client.voice_cloning(
        "Hello from Bhashini",
        "This is the reference voice sample.",
        "reference.wav",
        source_lang="en",
        output_file="voice_clone_output.wav",
    )
)
```

### Text Normalization And ITN

```python
print(client.text_normalization("i got 2065778 rupees prize", "en"))
print(client.inverse_text_normalization("i got five thousand rupees prize", "en"))
```

### Denoiser

```python
print(client.denoiser("sample.wav", output_file="denoised_output.wav"))
```

## Demo

Run the end-to-end demo:

```powershell
python demo.py
```

Optional sample files:

```powershell
$env:BHASHINI_SAMPLE_AUDIO="C:\full\path\sample.wav"
$env:BHASHINI_SAMPLE_IMAGE="C:\full\path\sample.png"
```

The demo exercises text, speech, speaker, normalization, and image-language services from one script.

## Services Reference

### Public Client Methods

These are the main high-level methods exposed by `BhashiniClient`:

| Method | Purpose | Return Type |
| --- | --- | --- |
| `client.asr(audio_input, source_lang, service_id=None)` | Speech to text | `str` transcription |
| `client.nmt(text, source_lang, target_lang, service_id=None)` | Translation | `str` translated text |
| `client.tts(text, source_lang, gender="female", output_file="output.wav", service_id=None)` | Text to speech | output file path `str` |
| `client.transliteration(text, source_lang, target_lang, service_id=None)` | Script conversion | transliterated text `str` |
| `client.text_language_detection(text, service_id=None)` | Text language detection | language code `str` |
| `client.audio_language_detection(audio_input, service_id=None)` | Audio language detection | language code `str` |
| `client.ocr(image_path, source_lang, service_id=None)` | OCR from local image | extracted text `str` |
| `client.ner(text, source_lang, service_id=None)` | Named entity recognition | `dict` with `entities` |
| `client.speaker_diarization(audio_input, service_id=None)` | Speaker segmentation | `list` of speaker blocks |
| `client.speaker_enrollment(audio_input, speaker_name, service_id=None)` | Speaker profile creation | speaker ID `str` |
| `client.speaker_verification(audio_input, speaker_id, service_id=None)` | Speaker verification | verification result |
| `client.voice_cloning(text, ref_text, ref_audio_input, source_lang="te", output_file="voice_clone_output.wav", service_id=None)` | Voice cloning | output file path `str` |
| `client.image_language_detection(image_input, service_id=None)` | Image language detection | language code `str` |
| `client.text_normalization(text, source_lang="en", service_id=None)` | Text normalization | normalized text `str` |
| `client.inverse_text_normalization(text, source_lang="en", service_id=None)` | ITN | normalized text `str` |
| `client.denoiser(audio_input, output_file="denoised_output.wav", service_id=None)` | Audio denoising | output file path `str` or audio URI `str` |

If `service_id` is omitted, the SDK uses its default model routing. If `service_id` is provided, the SDK validates that model against the service and language before calling the API.

### Speech / Audio

#### ASR

- Converts speech to text.
- Supports local WAV input, base64 audio, and audio URI input.
- Validates sampling rate, mono audio, speech presence, and processor values.
- Supports optional audio metadata like `audio_format`, `sampling_rate`, and `encoding` through `client.asr_service.transcribe(...)`.
- Supports ASR pre-processors: `vad`, `denoiser`
- Supports ASR post-processors: `itn`, `punctuation`

#### ASR Streaming

ASR streaming uses the WebSocket API and sends audio as chunks. The streaming API expects 16 kHz mono PCM audio chunks.

In Colab, convert an uploaded WAV file to the expected format first:

```python
import subprocess

input_audio = "sample.wav"
stream_audio = "stream_16k_mono.wav"

subprocess.run(
    [
        "ffmpeg", "-y",
        "-i", input_audio,
        "-ac", "1",
        "-ar", "16000",
        "-sample_fmt", "s16",
        stream_audio,
    ],
    check=True,
)
```

Then stream chunks:

```python
import wave

def wav_chunks(path, chunk_ms=200):
    with wave.open(path, "rb") as wf:
        frames_per_chunk = int(wf.getframerate() * chunk_ms / 1000)
        while True:
            data = wf.readframes(frames_per_chunk)
            if not data:
                break
            yield data

result = await client.asr_stream(
    wav_chunks(stream_audio),
    "hi",
    receive_timeout=15,
    chunk_delay_seconds=0.05,
    return_details=True,
    audio_sample_format="int16",
)

print(result.get("transcript") if isinstance(result, dict) else result)
```

In a normal Python script where no event loop is already running, you can use the sync wrapper:

```python
result = client.asr_stream_sync(
    wav_chunks("stream_16k_mono.wav"),
    "hi",
    receive_timeout=15,
    chunk_delay_seconds=0.05,
)

print(result)
```

#### TTS

- Synthesizes speech from input text.
- Public method writes output to a file path.
- Advanced service call supports optional `speed`, `speaker_name`, `text_normalization`, `profanity_filter`, and `return_base64`.
- Advanced usage is available through `client.tts_service.synthesize(...)`.

#### Audio Language Detection

- Detects spoken language from audio input.
- Supports local WAV input, base64 audio, and audio URI input.
- Uses default and fallback service routing internally.

#### Speaker Diarization

- Splits audio into speaker segments with timestamps.
- Supports validated audio input and optional pre-processors.

#### Speaker Enrollment

- Enrolls a speaker from local audio, base64 audio, or audio URI input.
- Returns a reusable speaker ID.

#### Speaker Verification

- Verifies whether a voice sample matches an enrolled speaker.
- Supports local audio, base64 audio, and audio URI input.
- Handles nested verification response shapes.

#### Voice Cloning

- Generates speech from reference text and reference audio.
- Writes cloned audio output to a file.

#### Denoiser

- Removes noise from audio input.
- Supports local audio, base64 audio, and audio URI input.

### Text

#### NMT

- Translates text between supported language pairs.
- Validates source and target languages through the model registry.
- Uses primary/fallback routing internally.
- Advanced service call supports:
  - `glossary`
  - `domain`
  - `gender`
  - `enable_number_translation`
  - `profanity_filter`
  - `pre_processors=["html"]`
  - `post_processors=["glossary"]`
- Advanced usage is available through `client.nmt_service.translate(...)`.

#### Transliteration

- Converts text across scripts without translation.
- Supports suggestion count, sentence mode, and `numeric_transliteration` in the service layer.

#### Text Language Detection

- Detects the top language from input text.
- Public methods:
  - `client.text_language_detection(text)`
  - `client.language_detection(text)`

#### Text Normalization

- Normalizes text using a dedicated endpoint.
- Public method returns normalized text.

#### Inverse Text Normalization

- Converts spoken-style text into normalized written text.
- Public method returns normalized text.

#### NER

- Extracts entities from text.
- Returns a normalized dictionary with `entities`.

### Vision

#### OCR

- Extracts text from a local image file.
- Validates file existence and converts the image to base64 internally.

#### Image Language Detection

- Detects language from:
  - local image path
  - public image URL
  - base64 image content

## Advanced Features

### Input Flexibility

The SDK supports different input styles depending on the service:

| Input Type | Supported In |
| --- | --- |
| Local file path | audio, OCR image, image language detection |
| Base64 string | audio services, image language detection |
| Remote URI | ASR, Audio Language Detection, Speaker Enrollment, Speaker Verification, Denoiser, Image Language Detection |

### Model Registry

`models_info.py` is the central model catalog for service IDs, supported languages, and filtering.

Available helpers:

```python
from bhashini_client import get_models_info, get_available_models

print(get_models_info("asr"))
print(get_available_models("asr", language="hi"))
print(get_available_models("nmt", language=("en", "hi")))
print(get_available_models("tts", language="en"))
```

Use one of the returned `serviceId` values in a public method:

```python
models = get_available_models("nmt", language=("en", "hi"))
service_id = models[0]["serviceId"]

print(client.nmt("Hello", "en", "hi", service_id=service_id))
```

### Shared Request Layer

- `bhashini_client/utils/request_handler.py` centralizes HTTP request handling.
- `bhashini_client/config.py` defines:
  - `BASE_URL`
  - `BHASHINI_API_KEY`
  - default timeout
  - default headers

## Error Handling

The SDK returns structured string errors from service methods:

| Error Prefix | Meaning |
| --- | --- |
| `Input Error:` | Missing input, wrong type, wrong format, unsupported processor, invalid path, or invalid local media |
| `Validation Error:` | Unsupported service, model, or language configuration |
| `API Error:` | Empty, malformed, or invalid backend response |

Examples:

- missing file path
- unsupported language pair
- invalid sampling rate
- malformed API response

## Testing

Run the full suite:

```powershell
python -m pytest tests -v
```

Run a specific service:

```powershell
python -m pytest tests\test_asr.py -v
```

Run the full check script:

```powershell
.\run_all_checks.ps1
```

Test outputs are logged into:

- `final_bhashini_test_results.xlsx`

## Design Decisions

- One file per service keeps changes isolated and easier to test.
- `request_handler.py` keeps transport logic centralized.
- `models_info.py` keeps service IDs and language support centralized.
- `demo.py` acts as an end-to-end smoke test across major services.

## Known Limitations

- Public `BhashiniClient` methods expose a simple interface; some advanced parameters are available through the underlying service objects instead of the top-level methods.
- Most service methods return strings, file paths, lists, or dictionaries rather than custom exception objects or typed response classes.
- Some compatibility parameters remain in service signatures even when they are no longer active in payload construction.
- Calls are synchronous through the current request layer.

## Package Contents

- `bhashini_client.BhashiniClient`
- `bhashini_client.get_models_info`
- `bhashini_client.get_available_models`

## License

MIT
