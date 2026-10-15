import base64
import os

from ..models_info import validate_model_request
from .service_utils import api_error, input_error, is_error_response


class ImageLanguageDetectionService:
    DEFAULT_SERVICE_ID = "bhashini/iiith/img-lang-detection"
    DEFAULT_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

    def __init__(self, handler):
        self.handler = handler

    def preprocess(self, input_data):
        if input_data is None or not isinstance(input_data, str):
            return input_error("Image language detection expects a valid image path, URI, or base64 string.")
        cleaned_input = input_data.strip()
        if not cleaned_input:
            return input_error("Image input is empty. Please provide a valid image path, URI, or base64 string.")
        if os.path.isfile(cleaned_input):
            if os.path.getsize(cleaned_input) == 0:
                return input_error("Image file is empty. Please provide a valid image.")
            with open(cleaned_input, "rb") as image_file:
                return {"imageContent": base64.b64encode(image_file.read()).decode("utf-8")}
        lowered = cleaned_input.lower()
        if lowered.startswith("http://") or lowered.startswith("https://"):
            return {"imageUri": cleaned_input}
        try:
            decoded_bytes = base64.b64decode(cleaned_input, validate=True)
        except Exception:
            return input_error(
                "Image input must be a valid local file path, public HTTP/HTTPS image URI, or base64-encoded image."
            )
        if not decoded_bytes:
            return input_error("Base64 image content is empty. Please provide a valid image payload.")
        return {"imageContent": cleaned_input}

    def detect(self, input_data, service_id: str = None):
        processed_input = self.preprocess(input_data)
        if is_error_response(processed_input):
            return processed_input
        model_validation = validate_model_request("image language detection", service_id=service_id)
        if model_validation:
            return model_validation
        response = self.handler.post(
            self._build_payload(processed_input, service_id or self.DEFAULT_SERVICE_ID),
            url=self.DEFAULT_URL,
        )
        if not response:
            return api_error("Image language detection service did not return a valid response.")
        return self.postprocess(response)

    def _build_payload(self, image_input: dict, service_id: str):
        return {
            "pipelineTasks": [
                {
                    "taskType": "img-lang-detection",
                    "config": {
                        "serviceId": service_id,
                    },
                }
            ],
            "inputData": {
                "image": [image_input]
            },
        }

    def postprocess(self, response):
        try:
            pipeline_response = response.get("pipelineResponse", [{}])[0]
            output = pipeline_response.get("output", [{}])[0]
            predictions = output.get("langPrediction", [])
            if predictions:
                return predictions[0].get("langCode") or api_error(
                    "Image language detection response did not include a language code."
                )
            return output.get("langCode") or output.get("source") or pipeline_response.get("langCode") or api_error(
                "Image language detection response did not include any predictions."
            )
        except Exception:
            return api_error("Image language detection service returned a malformed response.")
