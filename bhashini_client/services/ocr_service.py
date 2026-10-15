import base64
import os

from ..models_info import validate_model_request
from .service_utils import api_error, input_error, is_error_response, require_language


class OCRService:
    def __init__(self, handler):
        self.handler = handler

    def preprocess(self, input_data):
        if input_data is None or not isinstance(input_data, str):
            return input_error("OCR input must be a valid image file path.")
        cleaned_input = input_data.strip()
        if not cleaned_input:
            return input_error("OCR image path is empty. Please provide a valid image file path.")
        if not os.path.isfile(cleaned_input):
            return input_error("OCR image file was not found at the provided path.")
        if os.path.getsize(cleaned_input) == 0:
            return input_error("OCR image file is empty. Please provide an image that contains text.")
        with open(cleaned_input, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")

    def extract_text(
        self,
        input_data,
        source_lang: str,
        service_id: str = "bhashini/iiith-bhasha-ocr",
        source_script_code: str = None,
        domain: str = None,
        text_detection: str = "False",
    ):
        processed_input = self.preprocess(input_data)
        if is_error_response(processed_input):
            return processed_input
        normalized_source = require_language(source_lang, field_name="source language")
        if is_error_response(normalized_source):
            return normalized_source

        model_validation = validate_model_request(
            "ocr",
            service_id=service_id,
            languages=[normalized_source],
        )
        if model_validation:
            return model_validation
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "ocr",
                    "config": self._build_config(
                        normalized_source,
                        service_id,
                        source_script_code=source_script_code,
                        domain=domain,
                        text_detection=text_detection,
                    ),
                }
            ],
            "inputData": {
                "image": [
                    {
                        "imageContent": processed_input,
                    }
                ]
            },
        }
        response = self.handler.post(payload)
        if not response:
            return api_error("OCR service did not return a valid response.")
        return self.postprocess(response)

    def _build_config(self, source_lang: str, service_id: str, source_script_code=None, domain=None, text_detection="False"):
        language_config = {"sourceLanguage": source_lang}
        if source_script_code:
            language_config["sourceScriptCode"] = source_script_code
        config = {
            "language": language_config,
            "serviceId": service_id,
            "textDetection": text_detection,
        }
        if domain:
            config["domain"] = domain
        return config

    def postprocess(self, response):
        try:
            output = response.get("pipelineResponse", [{}])[0].get("output", [{}])[0]
            if output.get("source"):
                return output["source"]
            return api_error("OCR response did not include extracted text.")
        except Exception:
            return api_error("OCR service returned a malformed response.")
