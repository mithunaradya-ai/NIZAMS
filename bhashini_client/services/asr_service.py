import asyncio

from ..models_info import get_available_models, validate_model_request
from .audio_input_utils import preprocess_audio_or_uri_input
from .asr_streaming_client import ASRStreamingClient
from .service_utils import api_error, input_error, is_error_response


class ASRService:
    VALID_PRE_PROCESSORS = {"vad", "denoiser"}
    VALID_POST_PROCESSORS = {"itn", "punctuation"}
    SUPPORTED_AUDIO_FORMATS = {"wav", "flac"}

    def __init__(self, handler):
        self.handler = handler

    def preprocess(self, input_data):
        return preprocess_audio_or_uri_input(
            input_data,
            require_wav=True,
            sampling_rate=16000,
            require_mono=True,
            require_speech=True,
        )

    def get_supported_models(self, language=None):
        return get_available_models("asr", language=language)

    def get_streaming_config(
        self,
        source_lang: str,
        *,
        service_id: str = None,
        post_processors=None,
        interim_results=True,
    ):
        streaming_client = self._get_streaming_client(source_lang=source_lang, service_id=service_id)
        return streaming_client.get_start_config(
            source_lang=source_lang,
            service_id=service_id,
            post_processors=post_processors,
            interim_results=interim_results,
        )

    async def stream_transcribe(
        self,
        audio_chunks,
        source_lang: str,
        *,
        service_id: str = None,
        post_processors=None,
        interim_results=True,
        receive_timeout=5,
        chunk_delay_seconds=0,
        return_details=False,
        audio_sample_format="int16",
    ):
        streaming_client = self._get_streaming_client(source_lang=source_lang, service_id=service_id)
        return await streaming_client.transcribe_audio_chunks(
            audio_chunks,
            source_lang=source_lang,
            service_id=service_id,
            post_processors=post_processors,
            interim_results=interim_results,
            receive_timeout=receive_timeout,
            chunk_delay_seconds=chunk_delay_seconds,
            return_details=return_details,
            audio_sample_format=audio_sample_format,
        )

    def stream_transcribe_sync(
        self,
        audio_chunks,
        source_lang: str,
        *,
        service_id: str = None,
        post_processors=None,
        interim_results=True,
        receive_timeout=5,
        chunk_delay_seconds=0,
        return_details=False,
        audio_sample_format="int16",
    ):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self.stream_transcribe(
                    audio_chunks,
                    source_lang,
                    service_id=service_id,
                    post_processors=post_processors,
                    interim_results=interim_results,
                    receive_timeout=receive_timeout,
                    chunk_delay_seconds=chunk_delay_seconds,
                    return_details=return_details,
                    audio_sample_format=audio_sample_format,
                )
            )
        return input_error("stream_transcribe_sync cannot be used inside a running event loop. Use await stream_transcribe(...) instead.")

    async def stream_microphone(
        self,
        source_lang: str,
        *,
        service_id: str = None,
        post_processors=None,
        interim_results=True,
    ):
        streaming_client = self._get_streaming_client(source_lang=source_lang, service_id=service_id)
        return await streaming_client.transcribe_microphone(
            source_lang=source_lang,
            service_id=service_id,
            post_processors=post_processors,
            interim_results=interim_results,
        )

    def transcribe(
        self,
        input_data,
        source_lang: str,
        service_id: str = None,
        source_script_code: str = None,
        audio_format: str = None,
        sampling_rate: int = None,
        encoding: str = None,
        domain: str = None,
        pre_processors=None,
        post_processors=None,
    ):
        processed_input = self.preprocess(input_data)
        if is_error_response(processed_input):
            return processed_input

        normalized_source_lang = source_lang.strip().lower() if isinstance(source_lang, str) else ""
        if not normalized_source_lang:
            return input_error("Source language is missing. Please provide a valid ASR source language code.")

        resolved_audio_format = audio_format or processed_input.get("audioFormat") or "wav"
        resolved_sampling_rate = sampling_rate if sampling_rate is not None else 16000
        if resolved_audio_format.lower() not in self.SUPPORTED_AUDIO_FORMATS:
            return input_error(
                f"ASR supports only these audio formats: {', '.join(sorted(self.SUPPORTED_AUDIO_FORMATS))}."
            )
        if resolved_sampling_rate != 16000:
            return input_error(
                f"ASR supports only 16000 Hz audio. Please resample the audio from {resolved_sampling_rate} Hz to 16000 Hz."
            )
        if "audioUri" not in processed_input and resolved_audio_format.lower() != "wav":
            return input_error("ASR accepts FLAC only for audio URI input. Local or base64 audio must remain WAV.")
        if pre_processors is not None and not self._is_valid_pre_processors(pre_processors):
            return input_error(
                "Unsupported ASR pre-processors were provided. Supported values are: vad, denoiser."
            )
        if post_processors is not None and not self._is_valid_post_processors(
            post_processors,
            normalized_source_lang,
            service_id or self._get_primary_service_id(normalized_source_lang),
        ):
            return input_error(
                "Unsupported ASR post-processors were provided. Supported values are: itn, punctuation, or valid hotword_list for the Hindi multilingual ASR model."
            )

        model_validation = validate_model_request(
            "asr",
            service_id=service_id,
            languages=[normalized_source_lang],
        )
        if model_validation:
            return model_validation

        response = self.handler.post(
            self._build_payload(
                processed_input,
                normalized_source_lang,
                service_id or self._get_primary_service_id(normalized_source_lang),
                source_script_code=source_script_code,
                audio_format=resolved_audio_format,
                sampling_rate=resolved_sampling_rate,
                encoding=encoding,
                domain=domain,
                pre_processors=pre_processors,
                post_processors=post_processors,
            )
        )
        if not response and service_id is None:
            response = self.handler.post(
                self._build_payload(
                    processed_input,
                    normalized_source_lang,
                    self._get_fallback_service_id(normalized_source_lang),
                    source_script_code=source_script_code,
                    audio_format=resolved_audio_format,
                    sampling_rate=resolved_sampling_rate,
                    encoding=encoding,
                    domain=domain,
                    pre_processors=pre_processors,
                    post_processors=post_processors,
                )
            )
        if not response and service_id is None and normalized_source_lang == "hi":
            response = self.handler.post(
                self._build_payload(
                    processed_input,
                    normalized_source_lang,
                    "bhashini/ai4bharat/conformer-multilingual-asr",
                    source_script_code=source_script_code,
                    audio_format=resolved_audio_format,
                    sampling_rate=resolved_sampling_rate,
                    encoding=encoding,
                    domain=domain,
                    pre_processors=pre_processors,
                    post_processors=post_processors,
                )
            )
        if not response:
            return api_error("ASR service did not return a valid response.")
        return self.postprocess(response)

    def _build_payload(
        self,
        audio_input,
        source_lang: str,
        service_id: str,
        source_script_code=None,
        audio_format="wav",
        sampling_rate=16000,
        encoding=None,
        domain=None,
        pre_processors=None,
        post_processors=None,
    ):
        language_config = {"sourceLanguage": source_lang}
        if source_script_code:
            language_config["sourceScriptCode"] = source_script_code
        config = {
            "language": language_config,
            "serviceId": service_id,
            "audioFormat": audio_format,
            "samplingRate": sampling_rate,
        }
        if encoding is not None:
            config["encoding"] = encoding
        if domain:
            config["domain"] = domain
        if pre_processors:
            config["preProcessors"] = pre_processors
        if post_processors:
            config["postProcessors"] = post_processors
        audio_payload = {}
        if audio_input.get("audioContent"):
            audio_payload["audioContent"] = audio_input["audioContent"]
        if audio_input.get("audioUri"):
            audio_payload["audioUri"] = audio_input["audioUri"]
        return {
            "pipelineTasks": [
                {
                    "taskType": "asr",
                    "config": config,
                }
            ],
            "inputData": {
                "audio": [
                    audio_payload
                ]
            },
        }

    def _is_valid_pre_processors(self, pre_processors):
        if not isinstance(pre_processors, list):
            return False
        return all(item in self.VALID_PRE_PROCESSORS for item in pre_processors)

    def _is_valid_post_processors(self, post_processors, source_lang: str, service_id: str):
        if not isinstance(post_processors, list):
            return False
        for item in post_processors:
            if isinstance(item, str):
                if item not in self.VALID_POST_PROCESSORS:
                    return False
                continue
            if isinstance(item, dict):
                hotword_list = item.get("hotword_list")
                if list(item.keys()) != ["hotword_list"]:
                    return False
                if source_lang != "hi":
                    return False
                if service_id != "bhashini/ai4bharat/conformer-multilingual-asr":
                    return False
                if not isinstance(hotword_list, list) or not hotword_list:
                    return False
                if not all(isinstance(word, str) and word.strip() for word in hotword_list):
                    return False
                continue
            return False
        return True

    def _get_primary_service_id(self, source_lang: str):
        normalized_lang = source_lang.strip().lower()
        if normalized_lang == "hi":
            return "ai4bharat/conformer-hi-gpu--t4"
        if normalized_lang == "en":
            return "ai4bharat/whisper-medium-en--gpu--t4"
        return "bhashini/ai4bharat/conformer-multilingual-asr"

    def _get_fallback_service_id(self, source_lang: str):
        normalized_lang = source_lang.strip().lower()
        if normalized_lang == "hi":
            return "ai4bharat/conformer-multilingual-indo_aryan-gpu--t4"
        return "bhashini/ai4bharat/conformer-multilingual-asr"

    def _get_streaming_client(self, *, source_lang: str, service_id: str = None):
        api_key = getattr(self.handler, "api_key", None)
        return ASRStreamingClient(
            api_key=api_key,
            source_lang=source_lang,
            service_id=service_id or "bhashini/ai4b/indic-conformer/grpc",
        )

    def postprocess(self, response):
        try:
            return (
                response.get("pipelineResponse", [{}])[0]
                .get("output", [{}])[0]
                .get("source")
            ) or api_error("ASR service returned an empty transcription.")
        except Exception:
            return api_error("ASR service returned a malformed response.")
