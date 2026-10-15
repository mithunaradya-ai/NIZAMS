import asyncio
import audioop
from array import array
import inspect
import json
from urllib.parse import quote

from ..config import API_KEY
from .service_utils import api_error, input_error


DEFAULT_ASR_STREAM_URL = "wss://dhruva-api.bhashini.gov.in/ws/v1/asr/stream"
DEFAULT_STREAMING_SERVICE_ID = "bhashini/ai4b/indic-conformer/grpc"
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_CHUNK_DURATION_MS = 200
VALID_AUDIO_SAMPLE_FORMATS = {"int16", "float32", "raw"}


def int16_pcm_to_float32_bytes(audio_chunk):
    samples = array("h")
    samples.frombytes(bytes(audio_chunk))
    scale = 32768.0
    return array("f", (max(-1.0, min(1.0, sample / scale)) for sample in samples)).tobytes()


def float_samples_to_bytes(audio_chunk):
    if isinstance(audio_chunk, (bytes, bytearray)):
        return bytes(audio_chunk)
    return array("f", audio_chunk).tobytes()


class VADProcessor:
    def __init__(
        self,
        *,
        speech_start_rms=0.020,
        speech_end_rms=0.010,
        min_speech_ms=200,
        min_pause_ms=800,
        chunk_duration_ms=DEFAULT_CHUNK_DURATION_MS,
    ):
        self.speech_start_rms = speech_start_rms
        self.speech_end_rms = speech_end_rms
        self.min_speech_ms = min_speech_ms
        self.min_pause_ms = min_pause_ms
        self.chunk_duration_ms = chunk_duration_ms
        self.is_speaking = False
        self.speech_run_ms = 0
        self.silence_run_ms = 0

    def process_chunk(self, audio_chunk):
        if not audio_chunk:
            return "IDLE"
        rms = audioop.rms(audio_chunk, 2) / 32768.0
        if not self.is_speaking:
            if rms > self.speech_start_rms:
                self.speech_run_ms += self.chunk_duration_ms
                if self.speech_run_ms >= self.min_speech_ms:
                    self.is_speaking = True
                    self.speech_run_ms = 0
                    return "START"
            else:
                self.speech_run_ms = 0
        else:
            if rms < self.speech_end_rms:
                self.silence_run_ms += self.chunk_duration_ms
                if self.silence_run_ms >= self.min_pause_ms:
                    self.is_speaking = False
                    self.silence_run_ms = 0
                    return "STOP"
            else:
                self.silence_run_ms = 0
        return "CONTINUE" if self.is_speaking else "IDLE"


class ASRStreamingClient:
    def __init__(
        self,
        *,
        api_key=None,
        websocket_url=DEFAULT_ASR_STREAM_URL,
        service_id=DEFAULT_STREAMING_SERVICE_ID,
        source_lang="hi",
        sample_rate=DEFAULT_SAMPLE_RATE,
        chunk_duration_ms=DEFAULT_CHUNK_DURATION_MS,
    ):
        self.api_key = (api_key or API_KEY).strip()
        self.websocket_url = websocket_url
        self.service_id = service_id
        self.source_lang = source_lang
        self.sample_rate = sample_rate
        self.chunk_duration_ms = chunk_duration_ms

    def get_websocket_url(self):
        if not self.api_key:
            return input_error("BHASHINI_API_KEY is missing. Please set it before using ASR streaming.")
        return f"{self.websocket_url}?api_key={quote(self.api_key)}"

    def get_start_config(
        self,
        *,
        source_lang=None,
        service_id=None,
        audio_format="pcm",
        encoding="raw",
        sampling_rate=None,
        post_processors=None,
        interim_results=True,
        end_of_stream_policy="client_signal",
        profanity_filter=True,
    ):
        resolved_source_lang = (source_lang or self.source_lang or "").strip().lower()
        if not resolved_source_lang:
            return input_error("Source language is missing. Please provide a valid ASR source language code.")
        resolved_sampling_rate = sampling_rate or self.sample_rate
        if resolved_sampling_rate != DEFAULT_SAMPLE_RATE:
            return input_error("ASR streaming supports only 16000 Hz PCM audio chunks.")
        return {
            "type": "start",
            "controlConfig": {"dataTracking": False},
            "config": {
                "serviceId": service_id or self.service_id,
                "language": {"sourceLanguage": resolved_source_lang},
                "audioFormat": audio_format,
                "encoding": encoding,
                "samplingRate": resolved_sampling_rate,
                "transcriptionFormat": {"value": "transcript"},
                "profanityFilter": profanity_filter,
                "postProcessors": post_processors or ["itn", "punctuation"],
            },
            "streamingConfig": {
                "chunkDurationMs": self.chunk_duration_ms,
                "interimResults": interim_results,
                "endOfStreamPolicy": end_of_stream_policy,
            },
        }

    async def transcribe_audio_chunks(
        self,
        audio_chunks,
        *,
        source_lang=None,
        service_id=None,
        post_processors=None,
        interim_results=True,
        receive_timeout=5,
        chunk_delay_seconds=0,
        return_details=False,
        wait_for_ready=True,
        audio_sample_format="int16",
    ):
        try:
            import websockets
        except ImportError:
            return input_error("The 'websockets' package is required for ASR streaming. Install it before using this feature.")

        if audio_sample_format not in VALID_AUDIO_SAMPLE_FORMATS:
            return input_error("audio_sample_format must be one of: int16, float32, raw.")

        websocket_url = self.get_websocket_url()
        if isinstance(websocket_url, str) and websocket_url.startswith("Input Error:"):
            return websocket_url

        start_config = self.get_start_config(
            source_lang=source_lang,
            service_id=service_id,
            post_processors=post_processors,
            interim_results=interim_results,
        )
        if isinstance(start_config, str) and start_config.startswith("Input Error:"):
            return start_config

        transcripts = []
        messages = []

        async def wait_until_ready(websocket):
            while True:
                message = await asyncio.wait_for(websocket.recv(), timeout=receive_timeout)
                response = json.loads(message)
                messages.append(response)
                if response.get("type") == "ready":
                    return None
                if response.get("type") == "error":
                    return response

        async def receive_transcripts(websocket):
            try:
                while True:
                    message = await websocket.recv()
                    response = json.loads(message)
                    messages.append(response)
                    if response.get("type") != "transcript":
                        continue
                    text = (response.get("output") or [{}])[0].get("source")
                    if text:
                        transcripts.append(
                            {
                                "source": text,
                                "isFinal": response.get("isFinal", False),
                                "raw": response,
                            }
                        )
                    if response.get("isFinal"):
                        break
            except Exception:
                # Normal WebSocket closure is expected after the service finishes a stream.
                return

        def prepare_chunk(chunk):
            if not isinstance(chunk, (bytes, bytearray)) or not chunk:
                if audio_sample_format == "float32" and chunk:
                    return float_samples_to_bytes(chunk)
                return None
            if audio_sample_format == "int16":
                return int16_pcm_to_float32_bytes(chunk)
            if audio_sample_format == "float32":
                return float_samples_to_bytes(chunk)
            return bytes(chunk)

        async def send_chunk(websocket, chunk):
            prepared_chunk = prepare_chunk(chunk)
            if not prepared_chunk:
                return
            await websocket.send(prepared_chunk)
            if chunk_delay_seconds:
                await asyncio.sleep(chunk_delay_seconds)

        try:
            async with websockets.connect(websocket_url) as websocket:
                await websocket.send(json.dumps(start_config))
                if wait_for_ready:
                    early_error = await wait_until_ready(websocket)
                    if early_error:
                        if return_details:
                            return {
                                "transcript": None,
                                "messages": messages,
                                "error": early_error.get("message") or "ASR streaming backend returned an error.",
                            }
                        return api_error(early_error.get("message") or "ASR streaming backend returned an error.")
                receiver_task = asyncio.create_task(receive_transcripts(websocket))
                if inspect.isasyncgen(audio_chunks):
                    async for chunk in audio_chunks:
                        await send_chunk(websocket, chunk)
                else:
                    for chunk in audio_chunks:
                        await send_chunk(websocket, chunk)
                try:
                    await websocket.send(json.dumps({"type": "end"}))
                except Exception:
                    pass
                try:
                    await asyncio.wait_for(receiver_task, timeout=receive_timeout)
                except asyncio.TimeoutError:
                    receiver_task.cancel()
        except Exception as exc:
            error_messages = [message for message in messages if message.get("type") == "error"]
            if error_messages:
                backend_message = error_messages[-1].get("message") or "ASR streaming backend returned an error."
                if return_details:
                    return {
                        "transcript": None,
                        "messages": messages,
                        "error": backend_message,
                    }
                return api_error(backend_message)
            if return_details:
                return {
                    "transcript": None,
                    "messages": messages,
                    "error": "ASR streaming service did not return a valid response.",
                    "exception": f"{type(exc).__name__}: {exc}",
                }
            return api_error("ASR streaming service did not return a valid response.")

        error_messages = [message for message in messages if message.get("type") == "error"]
        if error_messages:
            backend_message = error_messages[-1].get("message") or "ASR streaming backend returned an error."
            if return_details:
                return {
                    "transcript": None,
                    "messages": messages,
                    "error": backend_message,
                }
            return api_error(backend_message)
        if not transcripts:
            if return_details:
                return {
                    "transcript": None,
                    "messages": messages,
                    "error": "ASR streaming service returned an empty transcription.",
                }
            return api_error("ASR streaming service returned an empty transcription.")
        final_transcripts = [item for item in transcripts if item["isFinal"]]
        transcript = (final_transcripts or transcripts)[-1]["source"]
        if return_details:
            return {
                "transcript": transcript,
                "messages": messages,
                "final": bool(final_transcripts),
            }
        return transcript

    async def transcribe_microphone(
        self,
        *,
        source_lang=None,
        service_id=None,
        post_processors=None,
        interim_results=True,
    ):
        try:
            import pyaudio
        except ImportError:
            return input_error("The 'pyaudio' package is required for microphone ASR streaming.")

        vad = VADProcessor(chunk_duration_ms=self.chunk_duration_ms)
        samples_per_chunk = int(self.sample_rate * self.chunk_duration_ms / 1000)
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=samples_per_chunk,
        )

        async def chunk_generator():
            try:
                while True:
                    chunk = stream.read(samples_per_chunk, exception_on_overflow=False)
                    state = vad.process_chunk(chunk)
                    if state in {"START", "CONTINUE"}:
                        yield chunk
                    if state == "STOP":
                        break
                    await asyncio.sleep(0.01)
            finally:
                stream.stop_stream()
                stream.close()
                audio.terminate()

        return await self.transcribe_audio_chunks(
            chunk_generator(),
            source_lang=source_lang,
            service_id=service_id,
            post_processors=post_processors,
            interim_results=interim_results,
            chunk_delay_seconds=0,
        )
