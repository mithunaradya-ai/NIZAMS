from ..models_info import validate_model_request
from .service_utils import api_error, is_error_response, require_language, require_text


class InverseTextNormalizationService:
    DEFAULT_SERVICE_ID = "bhashini/itn/gpu-t4"
    DEFAULT_URL = "https://dhruva-api.bhashini.gov.in/services/inference/itn"

    def __init__(self, handler):
        self.handler = handler

    def preprocess(self, input_data, source_lang):
        cleaned_input = require_text(input_data)
        if is_error_response(cleaned_input):
            return cleaned_input
        cleaned_lang = require_language(source_lang, field_name="source language")
        if is_error_response(cleaned_lang):
            return cleaned_lang
        return cleaned_input, cleaned_lang

    def normalize(self, input_data, source_lang: str = "en", service_id: str = None):
        processed_input = self.preprocess(input_data, source_lang)
        if is_error_response(processed_input):
            return processed_input
        model_validation = validate_model_request(
            "inverse text normalization",
            service_id=service_id,
            languages=[processed_input[1]],
        )
        if model_validation:
            return model_validation
        response = self.handler.post(
            self._build_payload(processed_input[0], processed_input[1], service_id or self.DEFAULT_SERVICE_ID),
            url=self.DEFAULT_URL,
        )
        if not response:
            return api_error("Inverse text normalization service did not return a valid response.")
        return self.postprocess(response)

    def _build_payload(self, text_input: str, source_lang: str, service_id: str):
        return {
            "config": {
                "serviceId": service_id,
                "language": {
                    "sourceLanguage": source_lang,
                },
            },
            "input": [
                {
                    "source": text_input,
                }
            ],
        }

    def postprocess(self, response):
        try:
            output = response.get("output", [{}])[0]
            if not output:
                output = response.get("pipelineResponse", [{}])[0].get("output", [{}])[0]
            return (
                output.get("target")
                or output.get("source")
                or output.get("normalizedText")
                or api_error("Inverse text normalization response did not include normalized text.")
            )
        except Exception:
            return api_error("Inverse text normalization service returned a malformed response.")
