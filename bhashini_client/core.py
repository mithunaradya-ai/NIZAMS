from typing import Optional

from .config import API_KEY
from .models_info import get_models_info
from .services.asr_service import ASRService
from .services.audio_language_detection_service import AudioLanguageDetectionService
from .services.denoiser_service import DenoiserService
from .services.image_lang_detection_service import ImageLanguageDetectionService
from .services.itn_service import InverseTextNormalizationService
from .services.language_detection_service import TextLanguageDetectionService
from .services.nmt_service import NMTService
from .services.ner_service import NERService
from .services.ocr_service import OCRService
from .services.speaker_enrollment_service import SpeakerEnrollmentService
from .services.speaker_diarization_service import SpeakerDiarizationService
from .services.speaker_verification_service import SpeakerVerificationService
from .services.text_normalization_service import TextNormalizationService
from .services.transliteration_service import TransliterationService
from .services.tts_service import TTSService
from .services.voice_cloning_service import VoiceCloningService
from .utils.request_handler import RequestHandler


class BhashiniClient:
    def __init__(self, api_key: Optional[str] = None):
        self.handler = RequestHandler(api_key or API_KEY)
        self.asr_service = ASRService(self.handler)
        self.nmt_service = NMTService(self.handler)
        self.tts_service = TTSService(self.handler)
        self.text_language_detection_service = TextLanguageDetectionService(self.handler)
        self.language_detection_service = self.text_language_detection_service
        self.audio_language_detection_service = AudioLanguageDetectionService(self.handler)
        self.transliteration_service = TransliterationService(self.handler)
        self.ocr_service = OCRService(self.handler)
        self.ner_service = NERService(self.handler)
        self.speaker_enrollment_service = SpeakerEnrollmentService(self.handler)
        self.speaker_verification_service = SpeakerVerificationService(self.handler)
        self.speaker_diarization_service = SpeakerDiarizationService(self.handler)
        self.voice_cloning_service = VoiceCloningService(self.handler)
        self.image_language_detection_service = ImageLanguageDetectionService(self.handler)
        self.text_normalization_service = TextNormalizationService(self.handler)
        self.inverse_text_normalization_service = InverseTextNormalizationService(self.handler)
        self.denoiser_service = DenoiserService(self.handler)

    def asr(self, audio_input, source_lang: str, service_id: str = None):
        return self.asr_service.transcribe(audio_input, source_lang, service_id=service_id)

    def asr_streaming_config(self, source_lang: str, **kwargs):
        return self.asr_service.get_streaming_config(source_lang, **kwargs)

    async def asr_stream(self, audio_chunks, source_lang: str, **kwargs):
        return await self.asr_service.stream_transcribe(audio_chunks, source_lang, **kwargs)

    def asr_stream_sync(self, audio_chunks, source_lang: str, **kwargs):
        return self.asr_service.stream_transcribe_sync(audio_chunks, source_lang, **kwargs)

    def nmt(self, text: str, source_lang: str, target_lang: str, service_id: str = None):
        return self.nmt_service.translate(text, source_lang, target_lang, service_id=service_id)

    def tts(
        self,
        text: str,
        source_lang: str,
        gender: str = "female",
        output_file: str = "output.wav",
        service_id: str = None,
    ):
        return self.tts_service.synthesize(
            text,
            source_lang,
            gender,
            output_file,
            service_id=service_id or "Bhashini/IITM/TTS",
        )

    def text_language_detection(self, text: str, service_id: str = None):
        return self.text_language_detection_service.detect(text, service_id=service_id)

    def language_detection(self, text: str, service_id: str = None):
        return self.text_language_detection(text, service_id=service_id)

    def audio_language_detection(self, audio_input, service_id: str = None):
        return self.audio_language_detection_service.detect(audio_input, service_id=service_id)

    def transliteration(self, text: str, source_lang: str, target_lang: str, service_id: str = None):
        return self.transliteration_service.transliterate(text, source_lang, target_lang, service_id=service_id or "ai4bharat/indicxlit--cpu-fsv2")

    def ocr(self, image_path: str, source_lang: str, service_id: str = None):
        return self.ocr_service.extract_text(image_path, source_lang, service_id=service_id or "bhashini/iiith-bhasha-ocr")

    def ner(self, text: str, source_lang: str, service_id: str = None):
        return self.ner_service.recognize_entities(text, source_lang, service_id=service_id or "bhashini/aukbc/ner")

    def speaker_enrollment(self, audio_input, speaker_name: str, service_id: str = None):
        return self.speaker_enrollment_service.enroll(audio_input, speaker_name, service_id=service_id)

    def speaker_verification(self, audio_input, speaker_id: str, service_id: str = None):
        return self.speaker_verification_service.verify(audio_input, speaker_id, service_id=service_id)

    def speaker_diarization(self, audio_input, service_id: str = None):
        return self.speaker_diarization_service.diarize(audio_input, service_id=service_id)

    def voice_cloning(
        self,
        text: str,
        ref_text: str,
        ref_audio_input,
        source_lang: str = "te",
        output_file: str = "voice_clone_output.wav",
        service_id: str = None,
    ):
        return self.voice_cloning_service.clone_voice(
            text,
            ref_text,
            ref_audio_input,
            source_lang=source_lang,
            service_id=service_id,
            output_file=output_file,
        )

    def image_language_detection(self, image_input, service_id: str = None):
        return self.image_language_detection_service.detect(image_input, service_id=service_id)

    def text_normalization(self, text: str, source_lang: str = "en", service_id: str = None):
        return self.text_normalization_service.normalize(text, source_lang, service_id=service_id)

    def inverse_text_normalization(self, text: str, source_lang: str = "en", service_id: str = None):
        return self.inverse_text_normalization_service.normalize(text, source_lang, service_id=service_id)

    def denoiser(self, audio_input, output_file: str = "denoised_output.wav", service_id: str = None):
        return self.denoiser_service.denoise(audio_input, service_id=service_id, output_file=output_file)

    def models_info(self, service_name: str = None):
        return get_models_info(service_name)
