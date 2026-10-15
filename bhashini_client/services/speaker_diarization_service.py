from ..models_info import validate_model_request
from .audio_input_utils import preprocess_audio_input
from .service_utils import api_error, input_error, is_error_response


class SpeakerDiarizationService:
    VALID_PRE_PROCESSORS = {"vad", "denoiser"}
    DEFAULT_SERVICE_ID = "bhashini/iisc/speaker-diarization"
    FALLBACK_SERVICE_ID = "bhashini/speaker-diarization"

    def __init__(self, handler):
        self.handler = handler

    def preprocess(self, input_data):
        return preprocess_audio_input(
            input_data,
            require_wav=True,
            sampling_rate=16000,
            require_speech=True,
        )

    def diarize(self, input_data, service_id: str = None, pre_processors=None):
        processed_input = self.preprocess(input_data)
        if is_error_response(processed_input):
            return processed_input
        if pre_processors is not None and not self._is_valid_pre_processors(pre_processors):
            return input_error(
                "Unsupported speaker diarization pre-processors were provided. Supported values are: vad, denoiser."
            )

        model_validation = validate_model_request("speaker diarization", service_id=service_id)
        if model_validation:
            return model_validation

        response = self.handler.post(
            self._build_payload(
                processed_input["audioContent"],
                service_id or self.DEFAULT_SERVICE_ID,
                pre_processors=pre_processors,
            )
        )
        if not response and service_id is None:
            response = self.handler.post(
                self._build_payload(
                    processed_input["audioContent"],
                    self.FALLBACK_SERVICE_ID,
                    pre_processors=pre_processors,
                )
            )
        if not response:
            return api_error("Speaker diarization service did not return a valid response.")
        return self.postprocess(response)

    def _build_payload(self, audio_content, service_id: str, pre_processors=None):
        config = {"serviceId": service_id}
        if pre_processors:
            config["preProcessors"] = pre_processors
        return {
            "pipelineTasks": [
                {
                    "taskType": "speaker-diarization",
                    "config": config,
                }
            ],
            "inputData": {
                "audio": [
                    {
                        "audioContent": audio_content,
                    }
                ]
            },
        }

    def _is_valid_pre_processors(self, pre_processors):
        if not isinstance(pre_processors, list):
            return False
        return all(item in self.VALID_PRE_PROCESSORS for item in pre_processors)

    def postprocess(self, response):
        try:
            output = response.get("pipelineResponse", [{}])[0].get("output", [{}])[0]
            speaker_labels = output.get("speaker_labels", [])
            formatted_output = []
            for speaker_entry in speaker_labels:
                if not isinstance(speaker_entry, dict):
                    continue
                for speaker_name, segments in speaker_entry.items():
                    formatted_output.append(
                        {
                            "speaker": speaker_name,
                            "timestamps": [
                                {
                                    "start_time": segment.get("start_time"),
                                    "duration": segment.get("duration"),
                                }
                                for segment in segments
                                if isinstance(segment, dict)
                            ],
                        }
                    )
            return formatted_output or api_error("Speaker diarization response did not include speaker labels.")
        except Exception:
            return api_error("Speaker diarization service returned a malformed response.")
