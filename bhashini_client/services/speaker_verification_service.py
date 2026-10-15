from ..models_info import validate_model_request
from .audio_input_utils import preprocess_audio_or_uri_input
from .service_utils import api_error, is_error_response, require_identifier


class SpeakerVerificationService:
    DEFAULT_SERVICE_ID = "bhashini/iitdharwad/speaker-verification"

    def __init__(self, handler):
        self.handler = handler

    def preprocess(self, audio_input, speaker_id):
        processed_audio = preprocess_audio_or_uri_input(
            audio_input,
            require_wav=True,
            sampling_rate=16000,
            require_speech=True,
        )
        if is_error_response(processed_audio):
            return processed_audio
        normalized_speaker_id = require_identifier(speaker_id, field_name="speaker id")
        if is_error_response(normalized_speaker_id):
            return normalized_speaker_id
        return {
            "audio": processed_audio,
            "speaker_id": normalized_speaker_id,
        }

    def verify(self, audio_input, speaker_id: str, service_id: str = None):
        processed_input = self.preprocess(audio_input, speaker_id)
        if is_error_response(processed_input):
            return processed_input
        model_validation = validate_model_request("speaker verification", service_id=service_id)
        if model_validation:
            return model_validation
        response = self.handler.post(
            self._build_payload(
                processed_input["audio"],
                processed_input["speaker_id"],
                service_id or self.DEFAULT_SERVICE_ID,
            )
        )
        if not response:
            return api_error("Speaker verification service did not return a valid response.")
        return self.postprocess(response)

    def _build_payload(self, audio_input, speaker_id: str, service_id: str):
        audio_payload = {}
        if audio_input.get("audioContent"):
            audio_payload["audioContent"] = audio_input["audioContent"]
        if audio_input.get("audioUri"):
            audio_payload["audioUri"] = audio_input["audioUri"]
        return {
            "pipelineTasks": [
                {
                    "taskType": "speaker-verification",
                    "config": {
                        "serviceId": service_id,
                        "speakerId": speaker_id,
                    },
                }
            ],
            "inputData": {
                "audio": [audio_payload],
            },
        }

    def postprocess(self, response):
        try:
            pipeline_response = response.get("pipelineResponse", [{}])[0]
            output = pipeline_response.get("output", [{}])[0]
            verification_result = self._extract_verification_result(output)
            if verification_result is None:
                verification_result = self._extract_verification_result(pipeline_response)
            if verification_result is not None:
                return verification_result
            return (
                output.get("source")
                or output.get("target")
                or pipeline_response.get("source")
                or pipeline_response.get("target")
                or api_error("Speaker verification response did not include a verification result.")
            )
        except Exception:
            return api_error("Speaker verification service returned a malformed response.")

    def _extract_verification_result(self, value):
        if isinstance(value, dict):
            for key in (
                "verified",
                "verificationResult",
                "isVerified",
                "match",
                "matched",
                "success",
                "score",
                "confidence",
                "similarity",
            ):
                if key in value and isinstance(value[key], (bool, int, float)):
                    return value[key]
            for nested_value in value.values():
                nested_result = self._extract_verification_result(nested_value)
                if nested_result is not None:
                    return nested_result
        elif isinstance(value, list):
            for item in value:
                nested_result = self._extract_verification_result(item)
                if nested_result is not None:
                    return nested_result
        return None
