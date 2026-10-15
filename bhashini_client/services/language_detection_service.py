from ..models_info import get_available_models, validate_model_request
from .service_utils import api_error, is_error_response, require_text


class TextLanguageDetectionService:
    DEFAULT_SERVICE_ID = "bhashini/indic-lang-detection-all"

    def __init__(self, handler):
        self.handler = handler

    def preprocess(self, input_data):
        return require_text(input_data)

    def get_supported_models(self, language=None):
        return get_available_models("language detection", language=language)

    def detect_language(self, input_data, service_id: str = None):
        if not isinstance(input_data, str):
            return "Invalid input"

        cleaned_input = input_data.strip()
        if not cleaned_input or cleaned_input.isdigit():
            return "Invalid input"

        model_validation = validate_model_request(
            "language detection",
            service_id=service_id,
        )
        if model_validation:
            return "API Error"

        payload = {
            "pipelineTasks": [
                {
                    "taskType": "txt-lang-detection",
                    "config": {
                        "serviceId": service_id or self.DEFAULT_SERVICE_ID,
                    },
                }
            ],
            "inputData": {"input": [{"source": cleaned_input}]},
        }

        response = self.handler.post(payload)
        if not response:
            return "API Error"

        try:
            output = response.get("pipelineResponse", [{}])[0].get("output", [{}])[0]
            predictions = output.get("langPrediction", [])
            if not predictions:
                return "API Error"
            prediction = predictions[0]
            language = prediction.get("langCode")
            score = prediction.get("langScore")
            if not language:
                return "API Error"
            return {"language": language, "score": score}
        except Exception:
            return "API Error"

    def detect(self, input_data, service_id: str = None):
        processed_input = self.preprocess(input_data)
        if is_error_response(processed_input):
            return processed_input

        model_validation = validate_model_request(
            "language detection",
            service_id=service_id or self.DEFAULT_SERVICE_ID,
        )
        if model_validation:
            return model_validation
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "txt-lang-detection",
                    "config": {
                        "serviceId": service_id or self.DEFAULT_SERVICE_ID,
                    },
                }
            ],
            "inputData": {"input": [{"source": processed_input}]},
        }
        response = self.handler.post(payload)
        if not response:
            return api_error("Text language detection service did not return a valid response.")
        return self.postprocess(response)

    def postprocess(self, response):
        try:
            output = response.get("pipelineResponse", [{}])[0].get("output", [{}])[0]
            predictions = output.get("langPrediction", [])
            if predictions:
                return predictions[0].get("langCode") or api_error(
                    "Text language detection response did not include a language code."
                )
            return api_error("Text language detection response did not include any predictions.")
        except Exception:
            return api_error("Text language detection service returned a malformed response.")


LanguageDetectionService = TextLanguageDetectionService
