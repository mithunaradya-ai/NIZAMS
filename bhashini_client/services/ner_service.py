from ..models_info import get_available_models, validate_model_request
from .service_utils import api_error, is_error_response, require_language, require_text


class NERService:
    def __init__(self, handler):
        self.handler = handler

    def preprocess(self, input_data):
        return require_text(input_data)

    def get_supported_models(self, language=None):
        return get_available_models("ner", language=language)

    def recognize_entities(
        self,
        input_data,
        source_lang: str,
        service_id: str = "bhashini/aukbc/ner",
        source_script_code: str = None,
        domain: str = None,
    ):
        processed_input = self.preprocess(input_data)
        if is_error_response(processed_input):
            return processed_input
        normalized_source = require_language(source_lang, field_name="source language")
        if is_error_response(normalized_source):
            return normalized_source

        model_validation = validate_model_request(
            "ner",
            service_id=service_id,
            languages=[normalized_source],
        )
        if model_validation:
            return model_validation
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "ner",
                    "config": self._build_config(
                        normalized_source,
                        service_id,
                        source_script_code=source_script_code,
                    ),
                }
            ],
            "inputData": {"input": [{"source": processed_input}]},
        }
        response = self.handler.post(payload)
        if not response:
            return api_error("NER service did not return a valid response.")
        return self.postprocess(response)

    def _build_config(self, source_lang: str, service_id: str, source_script_code=None):
        language_config = {"sourceLanguage": source_lang}
        if source_script_code:
            language_config["sourceScriptCode"] = source_script_code
        config = {
            "language": language_config,
            "serviceId": service_id,
        }
        return config

    def postprocess(self, response):
        try:
            output = response.get("pipelineResponse", [{}])[0].get("output", [{}])[0]
            entities = output.get("nerPrediction")
            if entities is None:
                entities = output.get("entities")
            if entities is None:
                return api_error("NER response did not include any entities.")
            return {"entities": entities}
        except Exception:
            return api_error("NER service returned a malformed response.")
