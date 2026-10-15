import base64

from ..models_info import validate_model_request
from .audio_input_utils import preprocess_audio_or_uri_input
from .service_utils import api_error, is_error_response, require_output_file


class DenoiserService:
    DEFAULT_SERVICE_ID = "bhashini/facebook/denoiser--gpu-t4"
    DEFAULT_URL = "https://dhruva-api.bhashini.gov.in/services/inference/denoiser"

    def __init__(self, handler):
        self.handler = handler

    def preprocess(self, input_data):
        return preprocess_audio_or_uri_input(
            input_data,
            require_wav=True,
            sampling_rate=16000,
            require_speech=True,
        )

    def denoise(self, input_data, service_id: str = None, output_file: str = "denoised_output.wav"):
        processed_input = self.preprocess(input_data)
        if is_error_response(processed_input):
            return processed_input
        normalized_output_file = require_output_file(output_file)
        if is_error_response(normalized_output_file):
            return normalized_output_file
        model_validation = validate_model_request("denoiser", service_id=service_id)
        if model_validation:
            return model_validation
        response = self.handler.post(
            self._build_payload(processed_input, service_id or self.DEFAULT_SERVICE_ID),
            url=self.DEFAULT_URL,
        )
        if not response:
            return api_error("Denoiser service did not return a valid response.")
        return self.postprocess(response, normalized_output_file)

    def _build_payload(self, audio_input, service_id: str):
        audio_payload = {}
        if audio_input.get("audioContent"):
            audio_payload["audioContent"] = audio_input["audioContent"]
        if audio_input.get("audioUri"):
            audio_payload["audioUri"] = audio_input["audioUri"]
        return {
            "config": {
                "serviceId": service_id,
            },
            "audio": [audio_payload],
        }

    def postprocess(self, response, output_file: str):
        try:
            output = response.get("audio", [{}])[0]
            if not output:
                output = response.get("pipelineResponse", [{}])[0].get("audio", [{}])[0]
            audio_content = output.get("audioContent")
            if audio_content:
                with open(output_file, "wb") as audio_file:
                    audio_file.write(base64.b64decode(audio_content))
                return output_file
            if output.get("audioUri"):
                return output["audioUri"]
            return api_error("Denoiser response did not include audio output.")
        except Exception:
            return api_error("Denoiser service returned a malformed response.")
