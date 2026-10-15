from ..models_info import validate_model_request
from .service_utils import api_error, input_error, is_error_response, require_language, require_text


class NMTService:
    VALID_PRE_PROCESSORS = {"html"}
    VALID_POST_PROCESSORS = {"glossary"}

    def __init__(self, handler):
        self.handler = handler

    def preprocess(self, input_data):
        return require_text(input_data)

    def translate(
        self,
        input_data,
        source_lang: str,
        target_lang: str,
        service_id: str = None,
        source_script_code: str = None,
        target_script_code: str = None,
        glossary=None,
        domain: str = None,
        gender: str = None,
        enable_number_translation: bool = None,
        profanity_filter: bool = None,
        pre_processors=None,
        post_processors=None,
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
        normalized_domain = self._normalize_optional_string(domain, field_name="domain")
        if is_error_response(normalized_domain):
            return normalized_domain
        normalized_gender = self._normalize_optional_string(gender, field_name="gender")
        if is_error_response(normalized_gender):
            return normalized_gender
        if enable_number_translation is not None and not isinstance(enable_number_translation, bool):
            return input_error("enable_number_translation must be a boolean value.")
        if profanity_filter is not None and not isinstance(profanity_filter, bool):
            return input_error("profanity_filter must be a boolean value.")
        if pre_processors is not None and not self._is_valid_pre_processors(pre_processors):
            return input_error("Unsupported NMT pre-processors were provided. Supported values are: html.")
        if post_processors is not None and not self._is_valid_post_processors(post_processors):
            return input_error("Unsupported NMT post-processors were provided. Supported values are: glossary.")
        normalized_glossary = self._normalize_glossary(glossary)
        if is_error_response(normalized_glossary):
            return normalized_glossary
        if post_processors and "glossary" in post_processors and normalized_glossary is None:
            return input_error("The glossary post-processor requires a non-empty glossary configuration.")

        model_validation = validate_model_request(
            "nmt",
            service_id=service_id,
            languages=[normalized_source, normalized_target],
        )
        if model_validation:
            return model_validation
        response = self.handler.post(
            self._build_payload(
                processed_input,
                normalized_source,
                normalized_target,
                service_id or self._get_primary_service_id(normalized_source, normalized_target),
                source_script_code=source_script_code,
                target_script_code=target_script_code,
                glossary=normalized_glossary,
                domain=normalized_domain,
                gender=normalized_gender,
                enable_number_translation=enable_number_translation,
                profanity_filter=profanity_filter,
                pre_processors=pre_processors,
                post_processors=post_processors,
            )
        )
        if not response and service_id is None:
            response = self.handler.post(
                self._build_payload(
                    processed_input,
                    normalized_source,
                    normalized_target,
                    self._get_fallback_service_id(normalized_source, normalized_target),
                    source_script_code=source_script_code,
                    target_script_code=target_script_code,
                    glossary=normalized_glossary,
                    domain=normalized_domain,
                    gender=normalized_gender,
                    enable_number_translation=enable_number_translation,
                    profanity_filter=profanity_filter,
                    pre_processors=pre_processors,
                    post_processors=post_processors,
                )
            )
        if not response:
            return api_error("NMT service did not return a valid response.")
        return self.postprocess(response)

    def _build_payload(
        self,
        input_data,
        source_lang: str,
        target_lang: str,
        service_id: str,
        source_script_code=None,
        target_script_code=None,
        glossary=None,
        domain=None,
        gender=None,
        enable_number_translation=None,
        profanity_filter=None,
        pre_processors=None,
        post_processors=None,
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
        }
        if glossary is not None:
            config["glossary"] = glossary
        if domain:
            config["domain"] = domain
        if gender:
            config["gender"] = gender
        if enable_number_translation is not None:
            config["enableNumberTranslation"] = enable_number_translation
        if profanity_filter is not None:
            config["profanityFilter"] = profanity_filter
        if pre_processors:
            config["preProcessors"] = pre_processors
        if post_processors:
            config["postProcessors"] = post_processors
        return {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": config,
                }
            ],
            "inputData": {"input": [{"source": input_data}]},
        }

    def _get_primary_service_id(self, source_lang: str, target_lang: str):
        return "ai4bharat/indictrans-v2-all-gpu--t4"

    def _get_fallback_service_id(self, source_lang: str, target_lang: str):
        return "bhashini/iiith/nmt-all"

    def _normalize_optional_string(self, value, *, field_name: str):
        if value is None:
            return None
        if not isinstance(value, str):
            return input_error(f"{field_name.replace('_', ' ').capitalize()} must be provided as a string.")
        cleaned_value = value.strip()
        if not cleaned_value:
            return input_error(f"{field_name.replace('_', ' ').capitalize()} cannot be empty when provided.")
        return cleaned_value

    def _normalize_glossary(self, glossary):
        if glossary is None:
            return None
        if isinstance(glossary, dict):
            if not glossary:
                return input_error("glossary cannot be empty when provided.")
            if not all(isinstance(key, str) and key.strip() for key in glossary.keys()):
                return input_error("glossary dictionary keys must be non-empty strings.")
            if not all(isinstance(value, str) and value.strip() for value in glossary.values()):
                return input_error("glossary dictionary values must be non-empty strings.")
            return glossary
        if isinstance(glossary, list):
            if not glossary:
                return input_error("glossary cannot be empty when provided.")
            if not all(isinstance(item, dict) and item for item in glossary):
                return input_error("glossary list items must be non-empty dictionaries.")
            return glossary
        return input_error("glossary must be provided as a non-empty dictionary or list of dictionaries.")

    def _is_valid_pre_processors(self, pre_processors):
        return isinstance(pre_processors, list) and all(item in self.VALID_PRE_PROCESSORS for item in pre_processors)

    def _is_valid_post_processors(self, post_processors):
        return isinstance(post_processors, list) and all(item in self.VALID_POST_PROCESSORS for item in post_processors)

    def postprocess(self, response):
        try:
            return (
                response.get("pipelineResponse", [{}])[0]
                .get("output", [{}])[0]
                .get("target")
            ) or api_error("NMT response did not include translated text.")
        except Exception:
            return api_error("NMT service returned a malformed response.")
