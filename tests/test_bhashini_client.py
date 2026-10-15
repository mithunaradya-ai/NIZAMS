"""Tests for the top-level client."""

from bhashini_client import BhashiniClient, get_available_models


def test_client_init():
    client = BhashiniClient(api_key="CsFWOur9eN-PjvPQ_taMD0_ewNfnxQP-L3rO8AWOWJEJTKqrtBdnzzPlx0dd-u2S")
    assert client is not None
    assert hasattr(client, "nmt_service")
    assert hasattr(client, "tts_service")
    assert hasattr(client, "transliteration_service")
    assert hasattr(client, "language_detection_service")
    assert hasattr(client, "ocr_service")
    assert hasattr(client, "ner_service")


def test_get_available_models_export():
    models = get_available_models("asr", language="hi")
    assert isinstance(models, list)
    assert models


def test_public_methods_forward_service_id():
    client = BhashiniClient(api_key="test-key")
    calls = {}

    class ASRService:
        def transcribe(self, audio_input, source_lang, service_id=None):
            calls["asr"] = (audio_input, source_lang, service_id)

        def get_streaming_config(self, source_lang, **kwargs):
            calls["asr_streaming_config"] = (source_lang, kwargs)

        async def stream_transcribe(self, audio_chunks, source_lang, **kwargs):
            calls["asr_stream"] = (audio_chunks, source_lang, kwargs)

        def stream_transcribe_sync(self, audio_chunks, source_lang, **kwargs):
            calls["asr_stream_sync"] = (audio_chunks, source_lang, kwargs)

    class NMTService:
        def translate(self, text, source_lang, target_lang, service_id=None):
            calls["nmt"] = (text, source_lang, target_lang, service_id)

    class TTSService:
        def synthesize(self, text, source_lang, gender="female", output_file="output.wav", service_id=None):
            calls["tts"] = (text, source_lang, gender, output_file, service_id)

    class TextLanguageDetectionService:
        def detect(self, text, service_id=None):
            calls["text_language_detection"] = (text, service_id)

    class AudioLanguageDetectionService:
        def detect(self, audio_input, service_id=None):
            calls["audio_language_detection"] = (audio_input, service_id)

    class TransliterationService:
        def transliterate(self, text, source_lang, target_lang, service_id=None):
            calls["transliteration"] = (text, source_lang, target_lang, service_id)

    class OCRService:
        def extract_text(self, image_path, source_lang, service_id=None):
            calls["ocr"] = (image_path, source_lang, service_id)

    class NERService:
        def recognize_entities(self, text, source_lang, service_id=None):
            calls["ner"] = (text, source_lang, service_id)

    class SpeakerEnrollmentService:
        def enroll(self, audio_input, speaker_name, service_id=None):
            calls["speaker_enrollment"] = (audio_input, speaker_name, service_id)

    class SpeakerVerificationService:
        def verify(self, audio_input, speaker_id, service_id=None):
            calls["speaker_verification"] = (audio_input, speaker_id, service_id)

    class SpeakerDiarizationService:
        def diarize(self, audio_input, service_id=None):
            calls["speaker_diarization"] = (audio_input, service_id)

    class VoiceCloningService:
        def clone_voice(
            self,
            text,
            ref_text,
            ref_audio_input,
            source_lang="te",
            service_id=None,
            output_file="voice_clone_output.wav",
        ):
            calls["voice_cloning"] = (text, ref_text, ref_audio_input, source_lang, output_file, service_id)

    class ImageLanguageDetectionService:
        def detect(self, image_input, service_id=None):
            calls["image_language_detection"] = (image_input, service_id)

    class TextNormalizationService:
        def normalize(self, text, source_lang="en", service_id=None):
            calls["text_normalization"] = (text, source_lang, service_id)

    class InverseTextNormalizationService:
        def normalize(self, text, source_lang="en", service_id=None):
            calls["inverse_text_normalization"] = (text, source_lang, service_id)

    class DenoiserService:
        def denoise(self, audio_input, service_id=None, output_file="denoised_output.wav"):
            calls["denoiser"] = (audio_input, output_file, service_id)

    client.asr_service = ASRService()
    client.nmt_service = NMTService()
    client.tts_service = TTSService()
    client.text_language_detection_service = TextLanguageDetectionService()
    client.audio_language_detection_service = AudioLanguageDetectionService()
    client.transliteration_service = TransliterationService()
    client.ocr_service = OCRService()
    client.ner_service = NERService()
    client.speaker_enrollment_service = SpeakerEnrollmentService()
    client.speaker_verification_service = SpeakerVerificationService()
    client.speaker_diarization_service = SpeakerDiarizationService()
    client.voice_cloning_service = VoiceCloningService()
    client.image_language_detection_service = ImageLanguageDetectionService()
    client.text_normalization_service = TextNormalizationService()
    client.inverse_text_normalization_service = InverseTextNormalizationService()
    client.denoiser_service = DenoiserService()

    client.asr("audio.wav", "hi", service_id="asr-model")
    client.asr_streaming_config("hi", service_id="stream-model")
    client.asr_stream_sync([b"audio"], "hi", service_id="stream-model")
    client.nmt("Hello", "en", "hi", service_id="nmt-model")
    client.tts("Hello", "en", output_file="tts.wav", service_id="tts-model")
    client.text_language_detection("Hello", service_id="tld-model")
    client.language_detection("Hello", service_id="tld-alias-model")
    client.audio_language_detection("audio.wav", service_id="ald-model")
    client.transliteration("namaste", "en", "hi", service_id="xlit-model")
    client.ocr("image.png", "en", service_id="ocr-model")
    client.ner("Narendra Modi", "en", service_id="ner-model")
    client.speaker_enrollment("audio.wav", "speaker", service_id="enroll-model")
    client.speaker_verification("audio.wav", "speaker-id", service_id="verify-model")
    client.speaker_diarization("audio.wav", service_id="diarization-model")
    client.voice_cloning("Hello", "Reference", "audio.wav", service_id="clone-model")
    client.image_language_detection("image.png", service_id="ild-model")
    client.text_normalization("twenty one", service_id="tn-model")
    client.inverse_text_normalization("twenty one", service_id="itn-model")
    client.denoiser("audio.wav", output_file="denoised.wav", service_id="denoiser-model")

    assert calls["asr"] == ("audio.wav", "hi", "asr-model")
    assert calls["asr_streaming_config"] == ("hi", {"service_id": "stream-model"})
    assert calls["asr_stream_sync"] == ([b"audio"], "hi", {"service_id": "stream-model"})
    assert calls["nmt"] == ("Hello", "en", "hi", "nmt-model")
    assert calls["tts"] == ("Hello", "en", "female", "tts.wav", "tts-model")
    assert calls["text_language_detection"] == ("Hello", "tld-alias-model")
    assert calls["audio_language_detection"] == ("audio.wav", "ald-model")
    assert calls["transliteration"] == ("namaste", "en", "hi", "xlit-model")
    assert calls["ocr"] == ("image.png", "en", "ocr-model")
    assert calls["ner"] == ("Narendra Modi", "en", "ner-model")
    assert calls["speaker_enrollment"] == ("audio.wav", "speaker", "enroll-model")
    assert calls["speaker_verification"] == ("audio.wav", "speaker-id", "verify-model")
    assert calls["speaker_diarization"] == ("audio.wav", "diarization-model")
    assert calls["voice_cloning"] == ("Hello", "Reference", "audio.wav", "te", "voice_clone_output.wav", "clone-model")
    assert calls["image_language_detection"] == ("image.png", "ild-model")
    assert calls["text_normalization"] == ("twenty one", "en", "tn-model")
    assert calls["inverse_text_normalization"] == ("twenty one", "en", "itn-model")
    assert calls["denoiser"] == ("audio.wav", "denoised.wav", "denoiser-model")
