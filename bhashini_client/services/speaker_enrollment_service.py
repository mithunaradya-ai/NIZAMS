from ..models_info import validate_model_request
from .audio_input_utils import preprocess_audio_or_uri_input
from .service_utils import api_error, is_error_response, require_identifier


class SpeakerEnrollmentService:
    DEFAULT_SERVICE_ID = "bhashini/iitdharwad/speaker-enrollment"

    def __init__(self, handler):
        self.handler = handler

    def preprocess(self, audio_input, speaker_name):
        processed_audio = preprocess_audio_or_uri_input(
            audio_input,
            require_wav=True,
            sampling_rate=16000,
            require_speech=True,
        )
        if is_error_response(processed_audio):
            return processed_audio
        normalized_speaker_name = require_identifier(speaker_name, field_name="speaker name")
        if is_error_response(normalized_speaker_name):
            return normalized_speaker_name
        return {
            "audio": processed_audio,
            "speaker_name": normalized_speaker_name,
        }

    def enroll(self, audio_input, speaker_name: str, service_id: str = None):
        processed_input = self.preprocess(audio_input, speaker_name)
        if is_error_response(processed_input):
            return processed_input
        model_validation = validate_model_request("speaker enrollment", service_id=service_id)
        if model_validation:
            return model_validation
        response = self.handler.post(
            self._build_payload(
                processed_input["audio"],
                processed_input["speaker_name"],
                service_id or self.DEFAULT_SERVICE_ID,
            )
        )
        if not response:
            return api_error("Speaker enrollment service did not return a valid response.")
        return self.postprocess(response)

    def _build_payload(self, audio_input, speaker_name: str, service_id: str):
        audio_payload = {}
        if audio_input.get("audioContent"):
            audio_payload["audioContent"] = audio_input["audioContent"]
        if audio_input.get("audioUri"):
            audio_payload["audioUri"] = audio_input["audioUri"]
        return {
            "pipelineTasks": [
                {
                    "taskType": "speaker-enrollment",
                    "config": {
                        "serviceId": service_id,
                        "speakerName": speaker_name,
                    },
                }
            ],
            "inputData": {
                "audio": [audio_payload],
            },
        }

    def postprocess(self, response):
        try:
            output = response.get("pipelineResponse", [{}])[0].get("output", [{}])[0]
            return (
                output.get("speakerId")
                or output.get("speaker_id")
                or output.get("source")
                or api_error("Speaker enrollment response did not include a speaker id.")
            )
        except Exception:
            return api_error("Speaker enrollment service returned a malformed response.")
