import base64

from ..models_info import validate_model_request
from .service_utils import api_error, input_error, is_error_response, require_language, require_output_file, require_text


class TTSService:
    def __init__(self, handler):
        self.handler = handler

    def preprocess(self, input_data, *, text_normalization: bool = False):
        processed_input = require_text(input_data)
        if is_error_response(processed_input):
            return processed_input
        if text_normalization:
            return " ".join(processed_input.split())
        return processed_input

    def synthesize(
        self,
        input_data,
        source_lang: str,
        gender: str = "female",
        output_file: str = "output.wav",
        service_id: str = "Bhashini/IITM/TTS",
        source_script_code: str = None,
        audio_format: str = "wav",
        sampling_rate: int = 16000,
        encoding: str = None,
        supported_voice: str = None,
        domain: str = None,
        speed: float = None,
        speaker_name: str = None,
        profanity_filter: bool = None,
        text_normalization: bool = False,
        return_base64: bool = False,
    ):
        processed_input = self.preprocess(input_data, text_normalization=text_normalization)
        if is_error_response(processed_input):
            return processed_input
        normalized_source_lang = require_language(source_lang, field_name="source language")
        if is_error_response(normalized_source_lang):
            return normalized_source_lang
        if sampling_rate != 16000:
            return input_error(
                f"TTS supports only 16000 Hz output. Please use sampling_rate=16000 instead of {sampling_rate}."
            )
        if speed is not None and not isinstance(speed, (int, float)):
            return input_error("speed must be a numeric value when provided.")
        if speed is not None and speed <= 0:
            return input_error("speed must be greater than 0 when provided.")
        if profanity_filter is not None and not isinstance(profanity_filter, bool):
            return input_error("profanity_filter must be a boolean value.")
        normalized_speaker_name = None
        if speaker_name is not None:
            normalized_speaker_name = require_text(speaker_name, field_name="speaker name")
            if is_error_response(normalized_speaker_name):
                return normalized_speaker_name
        normalized_output_file = None
        if not return_base64:
            normalized_output_file = require_output_file(output_file)
            if is_error_response(normalized_output_file):
                return normalized_output_file

        model_validation = validate_model_request(
            "tts",
            service_id=service_id,
            languages=[normalized_source_lang],
        )
        if model_validation:
            return model_validation
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "tts",
                    "config": self._build_config(
                        normalized_source_lang,
                        gender,
                        service_id,
                        source_script_code=source_script_code,
                        audio_format=audio_format,
                        sampling_rate=sampling_rate,
                        encoding=encoding,
                        supported_voice=supported_voice,
                        domain=domain,
                        speed=speed,
                        speaker_name=normalized_speaker_name,
                        profanity_filter=profanity_filter,
                    ),
                }
            ],
            "inputData": {"input": [{"source": processed_input}]},
        }
        response = self.handler.post(payload)
        if not response:
            return api_error("TTS service did not return a valid response.")
        return self.postprocess(response, normalized_output_file or output_file, return_base64=return_base64)

    def _build_config(
        self,
        source_lang: str,
        gender: str,
        service_id: str,
        source_script_code=None,
        audio_format="wav",
        sampling_rate=16000,
        encoding=None,
        supported_voice=None,
        domain=None,
        speed=None,
        speaker_name=None,
        profanity_filter=None,
    ):
        language_config = {"sourceLanguage": source_lang}
        if source_script_code:
            language_config["sourceScriptCode"] = source_script_code
        config = {
            "language": language_config,
            "gender": gender,
            "serviceId": service_id,
            "audioFormat": audio_format,
            "samplingRate": sampling_rate,
        }
        if encoding is not None:
            config["encoding"] = encoding
        if supported_voice:
            config["supportedVoice"] = supported_voice
        if domain:
            config["domain"] = domain
        if speed is not None:
            config["speed"] = speed
        if speaker_name:
            config["speakerName"] = speaker_name
        if profanity_filter is not None:
            config["profanityFilter"] = profanity_filter
        return config

    def postprocess(self, response, output_file: str = "output.wav", *, return_base64: bool = False):
        try:
            pipeline_response = response.get("pipelineResponse", [{}])[0]
            audio_content = None
            if pipeline_response.get("audio"):
                audio_content = pipeline_response["audio"][0].get("audioContent")
            if not audio_content and pipeline_response.get("output"):
                audio_content = pipeline_response["output"][0].get("audio", {}).get("audioContent")
            if not audio_content:
                return api_error("TTS response did not include synthesized audio.")
            if return_base64:
                return audio_content
            with open(output_file, "wb") as audio_file:
                audio_file.write(base64.b64decode(audio_content))
            return output_file
        except Exception:
            return api_error("TTS service returned a malformed response.")
