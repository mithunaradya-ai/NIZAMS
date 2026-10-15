from ..models_info import validate_model_request
from .service_utils import api_error, input_error, is_error_response, require_language, require_text


class TransliterationService:
    def __init__(self, handler):
        self.handler = handler

    def preprocess(self, input_data):
        return require_text(input_data)

    def transliterate(
        self,
        input_data,
        source_lang: str,
        target_lang: str,
        service_id: str = "ai4bharat/indicxlit--cpu-fsv2",
        source_script_code: str = None,
        target_script_code: str = None,
        num_suggestions: int = 1,
        is_sentence: bool = True,
        domain: str = None,
        numeric_transliteration: bool = False,
    ):
        processed_input = self.preprocess(input_data)
        if is_error_response(processed_input):
            return processed_input
        normalized_source = require_language(source_lang, field_name="source language")
        if is_error_response(normalized_source):
            return normalized_source
        normalized_target = require_language(target_lang, field_name="target language")
        if is_error_response(normalized_target):
            return normalized_target
        if num_suggestions < 1:
            return input_error("num_suggestions must be 1 or greater for transliteration.")
        if not isinstance(numeric_transliteration, bool):
            return input_error("numeric_transliteration must be a boolean value.")

        model_validation = validate_model_request(
            "transliteration",
            service_id=service_id,
            languages=[normalized_source, normalized_target],
        )
        if model_validation:
            return model_validation
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "transliteration",
                    "config": self._build_config(
                        normalized_source,
                        normalized_target,
                        service_id,
                        source_script_code=source_script_code,
                        target_script_code=target_script_code,
                        num_suggestions=num_suggestions,
                        is_sentence=is_sentence,
                        numeric_transliteration=numeric_transliteration,
                    ),
                }
            ],
            "inputData": {"input": [{"source": processed_input}]},
        }
        response = self.handler.post(payload)
        if not response:
            return api_error("Transliteration service did not return a valid response.")
        return self.postprocess(response)

    def _build_config(
        self,
        source_lang: str,
        target_lang: str,
        service_id: str,
        source_script_code=None,
        target_script_code=None,
        num_suggestions=1,
        is_sentence=True,
        numeric_transliteration=False,
    ):
        language_config = {
            "sourceLanguage": source_lang,
            "targetLanguage": target_lang,
        }
        if source_script_code:
            language_config["sourceScriptCode"] = source_script_code
        if target_script_code:
            language_config["targetScriptCode"] = target_script_code
        config = {
            "language": language_config,
            "serviceId": service_id,
            "isSentence": is_sentence,
            "numSuggestions": num_suggestions,
            "numericTransliteration": numeric_transliteration,
        }
        return config

    def postprocess(self, response):
        try:
            output = response.get("pipelineResponse", [{}])[0].get("output", [{}])[0]
            if output.get("target"):
                return output["target"]
            suggestions = output.get("targetOptions", [])
            if suggestions:
                return suggestions[0]
            return api_error("Transliteration response did not include any output text.")
        except Exception:
            return api_error("Transliteration service returned a malformed response.")
