from ..models_info import get_available_models, validate_model_request
from .audio_input_utils import preprocess_audio_or_uri_input
from .service_utils import api_error, is_error_response


class AudioLanguageDetectionService:
    DEFAULT_SERVICE_ID = "bhashini/iitmandi/audio-lang-detection/gpu"
    FALLBACK_SERVICE_ID = "bhashini/ald"

    def __init__(self, handler):
        self.handler = handler

    def preprocess(self, input_data):
        return preprocess_audio_or_uri_input(
            input_data,
            require_wav=True,
            sampling_rate=16000,
            min_duration_seconds=3,
            require_speech=True,
        )

    def get_supported_models(self, language=None):
        return get_available_models("audio language detection", language=language)

    def detect(self, input_data, service_id: str = None):
        processed_input = self.preprocess(input_data)
        if is_error_response(processed_input):
            return processed_input

        model_validation = validate_model_request(
            "audio language detection",
            service_id=service_id,
        )
        if model_validation:
            return model_validation

        response = self.handler.post(
            self._build_payload(
                processed_input,
                service_id or self.DEFAULT_SERVICE_ID,
            )
        )
        if not response and service_id is None:
            response = self.handler.post(
                self._build_payload(
                    processed_input,
                    self.FALLBACK_SERVICE_ID,
                )
            )
        if not response:
            return api_error("Audio language detection service did not return a valid response.")
        return self.postprocess(response)

    def _build_payload(self, audio_input, service_id: str):
        audio_payload = {}
        if audio_input.get("audioContent"):
            audio_payload["audioContent"] = audio_input["audioContent"]
        if audio_input.get("audioUri"):
            audio_payload["audioUri"] = audio_input["audioUri"]
        return {
            "pipelineTasks": [
                {
                    "taskType": "audio-lang-detection",
                    "config": {
                        "serviceId": service_id,
                    },
                }
            ],
            "inputData": {
                "audio": [
                    audio_payload
                ]
            },
        }

    def postprocess(self, response):
        try:
            output = response.get("pipelineResponse", [{}])[0].get("output", [{}])[0]
            predictions = output.get("langPrediction", [])
            if predictions:
                return predictions[0].get("langCode") or api_error(
                    "Audio language detection response did not include a language code."
                )
            return api_error("Audio language detection response did not include any predictions.")
        except Exception:
            return api_error("Audio language detection service returned a malformed response.")
