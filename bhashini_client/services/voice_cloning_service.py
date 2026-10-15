import base64
import os

from ..models_info import validate_model_request
from .audio_input_utils import preprocess_audio_input
from .service_utils import api_error, input_error, is_error_response, require_language, require_output_file, require_text


class VoiceCloningService:
    DEFAULT_SERVICE_ID = "bhashini/ai4b/indicf5-tts"
    DEFAULT_URL = "https://dhruva-api.bhashini.gov.in/services/inference/tts/voice-cloning"

    def __init__(self, handler):
        self.handler = handler

    def preprocess(self, text_input, ref_text, ref_audio_input):
        normalized_text = require_text(text_input)
        if is_error_response(normalized_text):
            return normalized_text
        normalized_ref_text = require_text(ref_text, field_name="reference text")
        if is_error_response(normalized_ref_text):
            return normalized_ref_text
        processed_ref_audio = self._preprocess_ref_audio(ref_audio_input)
        if is_error_response(processed_ref_audio):
            return processed_ref_audio
        return {
            "source": normalized_text,
            "refText": normalized_ref_text,
            "refAudioContent": processed_ref_audio,
        }

    def clone_voice(
        self,
        text_input,
        ref_text: str,
        ref_audio_input,
        source_lang: str = "te",
        service_id: str = None,
        output_file: str = "voice_clone_output.wav",
    ):
        processed_input = self.preprocess(text_input, ref_text, ref_audio_input)
        if is_error_response(processed_input):
            return processed_input
        normalized_source_lang = require_language(source_lang, field_name="source language")
        if is_error_response(normalized_source_lang):
            return normalized_source_lang
        normalized_output_file = require_output_file(output_file)
        if is_error_response(normalized_output_file):
            return normalized_output_file

        model_validation = validate_model_request(
            "voice cloning",
            service_id=service_id,
            languages=[normalized_source_lang],
        )
        if model_validation:
            return model_validation

        response = self.handler.post(
            self._build_payload(
                processed_input,
                normalized_source_lang,
                service_id or self.DEFAULT_SERVICE_ID,
            ),
            url=self.DEFAULT_URL,
            headers={"x-auth-source": "API_KEY", "accept": "application/json"},
        )
        if not response:
            return api_error("Voice cloning service did not return a valid response.")
        return self.postprocess(response, normalized_output_file)

    def _preprocess_ref_audio(self, ref_audio_input):
        if ref_audio_input is None:
            return input_error("Reference audio is missing. Please provide a WAV file path or base64 audio.")
        if isinstance(ref_audio_input, bytes):
            processed_audio = preprocess_audio_input(
                ref_audio_input,
                require_wav=True,
                sampling_rate=16000,
                require_speech=True,
            )
            if is_error_response(processed_audio):
                return processed_audio
            return processed_audio["audioContent"]
        if not isinstance(ref_audio_input, str):
            return input_error("Reference audio input type is invalid.")
        cleaned_input = ref_audio_input.strip()
        if not cleaned_input:
            return input_error("Reference audio is empty. Please provide a valid audio sample.")
        if os.path.isfile(cleaned_input):
            processed_audio = preprocess_audio_input(
                cleaned_input,
                require_wav=True,
                sampling_rate=16000,
                require_speech=True,
            )
            if is_error_response(processed_audio):
                return processed_audio
            return processed_audio["audioContent"]
        processed_audio = preprocess_audio_input(
            cleaned_input,
            require_wav=True,
            sampling_rate=16000,
            require_speech=True,
        )
        if is_error_response(processed_audio):
            return processed_audio
        return processed_audio["audioContent"]

    def _build_payload(self, processed_input, source_lang: str, service_id: str):
        return {
            "config": {
                "language": {
                    "sourceLanguage": source_lang,
                },
                "serviceId": service_id,
            },
            "input": [
                {
                    "source": processed_input["source"],
                    "refText": processed_input["refText"],
                    "refAudioContent": processed_input["refAudioContent"],
                }
            ],
        }

    def postprocess(self, response, output_file: str):
        try:
            output = response.get("audio", [{}])[0]
            if not output:
                output = response.get("output", [{}])[0]
            if not output:
                output = response.get("pipelineResponse", [{}])[0].get("audio", [{}])[0]
            audio_content = output.get("audioContent")
            if not audio_content:
                return api_error("Voice cloning response did not include synthesized audio.")
            with open(output_file, "wb") as audio_file:
                audio_file.write(base64.b64decode(audio_content))
            return output_file
        except Exception:
            return api_error("Voice cloning service returned a malformed response.")
