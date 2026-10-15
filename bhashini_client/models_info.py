from __future__ import annotations


MODELS_INFO = {
    "asr": [
        {"service_name": "ASR", "serviceId": "bhashini/iitm/asr-dravidian--gpu--t4", "supported_languages": ["te", "kn", "ml", "ta"], "provider": "IIT Madras"},
        {"service_name": "ASR", "serviceId": "ai4bharat/conformer-hi-gpu--t4", "supported_languages": ["hi"], "provider": "AI4Bharat"},
        {"service_name": "ASR", "serviceId": "ai4bharat/conformer-multilingual-dravidian-gpu--t4", "supported_languages": ["kn", "ml", "ta", "te"], "provider": "AI4Bharat"},
        {"service_name": "ASR", "serviceId": "ai4bharat/conformer-multilingual-indo_aryan-gpu--t4", "supported_languages": ["hi", "bn", "mr", "ur", "or", "pa", "gu", "sa"], "provider": "AI4Bharat"},
        {"service_name": "ASR", "serviceId": "ai4bharat/whisper-medium-en--gpu--t4", "supported_languages": ["en"], "provider": "AI4Bharat"},
        {"service_name": "ASR", "serviceId": "bhashini/ai4bharat/conformer-multilingual-asr", "supported_languages": ["as", "bn", "brx", "doi", "gu", "hi", "kn", "ks", "gom", "mai", "ml", "mni", "mr", "ne", "or", "pa", "sa", "sat", "sd", "ta", "te", "ur"], "provider": "AI4Bharat"},
        {"service_name": "ASR", "serviceId": "bhashini/iitm/asr-indoaryan--gpu--t4", "supported_languages": ["gu", "or", "hi", "mr", "pa", "bn"], "provider": "IIT Madras"},
        {"service_name": "ASR", "serviceId": "bhashini/iitm/asr-misc--gpu--t4", "supported_languages": ["bho", "ur"], "provider": "IIT Madras"},
        {"service_name": "ASR", "serviceId": "bhashini/iisc/asr-mai-t4", "supported_languages": ["mai"], "provider": "IISC"},
        {"service_name": "ASR", "serviceId": "bhashini/iisc/asr-bho-t4", "supported_languages": ["bho"], "provider": "IISC"},
    ],
    "nmt": [
        {"service_name": "NMT", "serviceId": "bhashini/iiith/nmt-all", "supported_languages": ["hi", "en", "as", "awa", "bn", "bho", "bra", "brx", "doi", "gom", "gon", "gu", "hing", "hoc", "kn", "ks", "kha", "lus", "mai", "mag", "ml", "mr", "mni", "ne", "or", "pa", "sa", "sat", "si", "sd", "ta", "tcy", "te", "ur", "xnr"], "provider": "IIIT Hyderabad"},
        {"service_name": "NMT", "serviceId": "ai4bharat/indictrans-v2-all-gpu--t4", "supported_languages": ["en", "gom", "gu", "sa", "te", "mr", "hi", "or", "mni", "ml", "as", "doi", "sat", "ta", "sd", "bn", "ks", "kn", "ne"], "provider": "AI4Bharat"},
        {"service_name": "NMT", "serviceId": "Bhashini/IIITH/Trans/V1", "supported_languages": ["hi", "en", "te", "or", "gu", "ur", "pa", "sd", "doi", "ks"], "provider": "IIIT Hyderabad"},
        {"service_name": "NMT", "serviceId": "iitb/trilingual-en_hi_mr-v1-gpu--t4", "supported_languages": ["en", "as", "mr", "hi", "brx", "ne", "mai", "gom"], "provider": "IIT Bombay"},
        {"service_name": "NMT", "serviceId": "bhashini/aukbc/disco-nmt", "supported_languages": ["ml", "hi", "ta"], "provider": "AUKBC"},
        {"service_name": "NMT", "serviceId": "bhashini/cdac-noida/nmt", "supported_languages": ["en", "hi", "ta", "or", "bn"], "provider": "CDAC-Noida"},
        {"service_name": "NMT", "serviceId": "bhashini/cdac-pune/nmt", "supported_languages": ["en", "kn", "gu", "ml"], "provider": "CDAC-Pune"},
        {"service_name": "NMT", "serviceId": "bhashini/ai4bharat/indictrans-v3", "supported_languages": ["as", "bn", "en", "gu", "hi", "kn", "ml", "mr", "ne", "or", "pa", "sa", "ta", "te", "ur"], "provider": "AI4Bharat"},
        {"service_name": "NMT", "serviceId": "bhashini/iitkhg/nmt", "supported_languages": ["hi", "sa"], "provider": "IIT Kharagpur"},
    ],
    "tts": [
        {"service_name": "TTS", "serviceId": "Bhashini/IITM/TTS", "supported_languages": ["as", "bn", "brx", "doi", "en", "gu", "hi", "kn", "gom", "mai", "ml", "mni", "mr", "ne", "or", "pa", "raj", "sa", "ta", "te", "ur", "sat", "sd", "ks"], "supported_speakers": [], "provider": "IIT Madras"},
        {"service_name": "TTS", "serviceId": "ai4bharat/indic-tts-coqui-dravidian-gpu--t4", "supported_languages": ["ml", "kn", "ta", "te"], "supported_speakers": [], "provider": "AI4Bharat"},
        {"service_name": "TTS", "serviceId": "ai4bharat/indic-tts-coqui-indo_aryan-gpu--t4", "supported_languages": ["hi", "mr", "as", "bn", "gu", "or", "raj", "pa"], "supported_speakers": [], "provider": "AI4Bharat"},
        {"service_name": "TTS", "serviceId": "ai4bharat/indic-tts-coqui-misc-gpu--t4", "supported_languages": ["en", "mni", "brx"], "supported_speakers": [], "provider": "AI4Bharat"},
        {"service_name": "TTS", "serviceId": "Bhashini/IISC/TTS", "supported_languages": ["kn", "te", "en", "hi", "mr", "bn", "gu", "mai", "bho", "hne", "mag"], "supported_speakers": [], "provider": "IISC (SYSPIN)"},
    ],
    "transliteration": [
        {"service_name": "Transliteration", "serviceId": "ai4bharat/indicxlit--cpu-fsv2", "supported_languages": ["en", "gom", "gu", "sa", "te", "mr", "hi", "or", "mni", "ml", "as", "doi", "sat", "ta", "sd", "bn", "ks", "kn", "ne", "pa", "mai", "ur", "si", "brx"], "provider": "AI4Bharat"},
    ],
    "language detection": [
        {"service_name": "Language Detection", "serviceId": "bhashini/indic-lang-detection-all", "supported_languages": ["as", "bn", "brx", "doi", "en", "gu", "hi", "kn", "ks", "gom", "mai", "ml", "mni", "mr", "ne", "or", "pa", "sa", "sat", "sd", "ta", "te", "ur"], "provider": "AI4Bharat"},
        {"service_name": "Language Detection", "serviceId": "bhashini/iiiith/indic-lang-detection-all", "supported_languages": ["as", "bn", "en", "gu", "hi", "kn", "ml", "mni", "mr", "or", "pa", "ta", "te", "ur"], "provider": "IIIT Hyderabad"},
        {"service_name": "Language Detection", "serviceId": "bhashini/indic/tld", "supported_languages": ["as", "brx", "bn", "doi", "en", "gu", "hi", "kn", "ks", "gom", "mai", "ml", "mni", "mr", "ne", "or", "pa", "sa", "sat", "sd", "ta", "te", "ur"], "provider": "-"},
    ],
    "ner": [
        {"service_name": "NER", "serviceId": "bhashini/iiith/ner", "supported_languages": ["hi", "ur", "or", "te"], "provider": "IIIT Hyderabad"},
        {"service_name": "NER", "serviceId": "bhashini/ai4bharat/indic-ner", "supported_languages": ["as", "bn", "gu", "hi", "kn", "ml", "te", "mr", "or", "pa", "ta"], "provider": "AI4Bharat"},
        {"service_name": "NER", "serviceId": "bhashini/aukbc/ner", "supported_languages": ["hi", "bn", "mr", "pa", "kn", "ml", "ta", "en"], "provider": "AUKBC"},
    ],
    "ocr": [
        {"service_name": "OCR", "serviceId": "bhashini/iiith-ocr-sceneText-all", "supported_languages": ["as", "bn", "gu", "hi", "kn", "ml", "mni", "mr", "or", "pa", "ta", "te", "ur"], "provider": "IIIT Hyderabad"},
        {"service_name": "OCR", "serviceId": "bhashini/iiith/ocr-hw-bhaasha", "supported_languages": ["bn", "hi", "ml", "mr", "pa", "te", "kn", "ta"], "provider": "IIIT Hyderabad"},
        {"service_name": "OCR", "serviceId": "bhashini/iiith-bhasha-ocr", "supported_languages": ["as", "bn", "brx", "doi", "en", "gu", "hi", "kn", "ks", "gom", "mai", "ne", "ml", "mni", "mr", "or", "pa", "sa", "sat", "sd", "ta", "te"], "provider": "IIIT Hyderabad"},
    ],
    "audio language detection": [
        {"service_name": "Audio Language Detection", "serviceId": "bhashini/iitmandi/audio-lang-detection/gpu", "supported_languages": ["as", "bn", "en", "hi", "kn", "gu", "ml", "mr", "or", "pa", "ta", "te"], "provider": "IIT Mandi"},
        {"service_name": "Audio Language Detection", "serviceId": "bhashini/ald", "supported_languages": ["as", "bn", "en", "hi", "kn", "gu", "ml", "mr", "or", "pa", "ta", "te"], "provider": "-"},
    ],
    "speaker diarization": [
        {"service_name": "Speaker Diarization", "serviceId": "bhashini/iisc/speaker-diarization", "supported_languages": ["all"], "provider": "IISC"},
        {"service_name": "Speaker Diarization", "serviceId": "bhashini/speaker-diarization", "supported_languages": ["all"], "provider": "Open Source"},
    ],
    "speaker enrollment": [
        {"service_name": "Speaker Enrollment", "serviceId": "bhashini/iitdharwad/speaker-enrollment", "supported_languages": ["all"], "provider": "IIT Dharwad"},
    ],
    "speaker verification": [
        {"service_name": "Speaker Verification", "serviceId": "bhashini/iitdharwad/speaker-verification", "supported_languages": ["all"], "provider": "IIT Dharwad"},
    ],
    "voice cloning": [
        {"service_name": "Voice Cloning", "serviceId": "bhashini/ai4b/indicf5-tts", "supported_languages": ["as", "bn", "en", "gu", "hi", "kn", "ml", "mr", "or", "pa", "ta", "te"], "provider": "AI4Bharat"},
    ],
    "image language detection": [
        {"service_name": "Image Language Detection", "serviceId": "bhashini/iiith/img-lang-detection", "supported_languages": ["all"], "provider": "IIIT Hyderabad"},
    ],
    "text normalization": [
        {"service_name": "Text Normalization", "serviceId": "bhashini/textnormalization/gpu-t4", "supported_languages": ["en"], "provider": "Bhashini"},
    ],
    "inverse text normalization": [
        {"service_name": "Inverse Text Normalization", "serviceId": "bhashini/itn/gpu-t4", "supported_languages": ["en"], "provider": "Bhashini"},
    ],
    "denoiser": [
        {"service_name": "Denoiser", "serviceId": "bhashini/facebook/denoiser--gpu-t4", "supported_languages": ["all"], "provider": "Meta"},
    ],
}


SERVICE_NAME_ALIASES = {
    "asr": "asr",
    "nmt": "nmt",
    "tts": "tts",
    "transliteration": "transliteration",
    "language detection": "language detection",
    "text language detection": "language detection",
    "language_detection": "language detection",
    "text_language_detection": "language detection",
    "ner": "ner",
    "ocr": "ocr",
    "audio language detection": "audio language detection",
    "audio_language_detection": "audio language detection",
    "speaker diarization": "speaker diarization",
    "speaker_diarization": "speaker diarization",
    "speaker enrollment": "speaker enrollment",
    "speaker_enrollment": "speaker enrollment",
    "speaker verification": "speaker verification",
    "speaker_verification": "speaker verification",
    "voice cloning": "voice cloning",
    "voice_cloning": "voice cloning",
    "image language detection": "image language detection",
    "image_language_detection": "image language detection",
    "text normalization": "text normalization",
    "text_normalization": "text normalization",
    "inverse text normalization": "inverse text normalization",
    "inverse_text_normalization": "inverse text normalization",
    "itn": "inverse text normalization",
    "denoiser": "denoiser",
}


def normalize_service_name(service_name=None):
    if not isinstance(service_name, str):
        return ""
    normalized_name = service_name.strip().lower().replace("-", " ").replace("_", " ")
    normalized_name = " ".join(normalized_name.split())
    return SERVICE_NAME_ALIASES.get(normalized_name, "")


def get_models_info(service_name=None):
    if service_name is None:
        return MODELS_INFO
    normalized_name = normalize_service_name(service_name)
    if not normalized_name:
        supported_services = ", ".join(sorted(MODELS_INFO.keys()))
        return f"Validation Error: Unsupported service '{service_name}'. Supported services are: {supported_services}."
    return MODELS_INFO.get(normalized_name, [])


def get_available_models(service_name: str, language=None):
    normalized_name = normalize_service_name(service_name)
    if not normalized_name:
        supported_services = ", ".join(sorted(MODELS_INFO.keys()))
        return f"Validation Error: Unsupported service '{service_name}'. Supported services are: {supported_services}."

    available_models = MODELS_INFO.get(normalized_name, [])
    formatted_models = []
    for model in available_models:
        if not _model_matches_language_filter(normalized_name, model, language):
            continue
        formatted_models.append(_format_available_model(normalized_name, model))
    return formatted_models


def get_model_details(service_name: str, service_id: str):
    normalized_name = normalize_service_name(service_name)
    if not normalized_name:
        return None
    for model in MODELS_INFO.get(normalized_name, []):
        if model["serviceId"] == service_id:
            return model
    return None


def validate_model_request(service_name: str, *, service_id: str = None, languages=None):
    normalized_name = normalize_service_name(service_name)
    if not normalized_name:
        supported_services = ", ".join(sorted(MODELS_INFO.keys()))
        return f"Validation Error: Unsupported service '{service_name}'. Supported services are: {supported_services}."

    available_models = MODELS_INFO.get(normalized_name, [])
    if service_id:
        model_details = get_model_details(normalized_name, service_id)
        if model_details is None:
            available_ids = ", ".join(model["serviceId"] for model in available_models) or "none"
            return (
                f"Validation Error: Unsupported model id '{service_id}' for {available_models[0]['service_name'] if available_models else normalized_name}. "
                f"Supported model ids are: {available_ids}."
            )
    else:
        model_details = None

    if languages:
        requested_languages = [lang for lang in languages if lang]
        if not requested_languages:
            return None

        models_to_check = [model_details] if model_details else available_models
        if not models_to_check:
            return None

        for model in models_to_check:
            supported_languages = model.get("supported_languages", [])
            if "all" in supported_languages or all(lang in supported_languages for lang in requested_languages):
                return None

        supported_union = sorted(
            {
                language
                for model in models_to_check
                for language in model.get("supported_languages", [])
            }
        )
        return (
            f"Validation Error: Unsupported language configuration {requested_languages} for {models_to_check[0]['service_name']}. "
            f"Supported languages are: {', '.join(supported_union)}."
        )

    return None


def _format_available_model(service_name: str, model: dict):
    formatted_model = {
        "serviceId": model["serviceId"],
        "provider": model.get("provider"),
    }
    if service_name == "nmt":
        formatted_model["supported_language_pairs"] = _build_language_pairs(model.get("supported_languages", []))
    else:
        formatted_model["supported_languages"] = model.get("supported_languages", [])
    if service_name == "tts":
        formatted_model["supported_speakers"] = model.get("supported_speakers", [])
    return formatted_model


def _build_language_pairs(supported_languages):
    pairs = []
    normalized_languages = [lang for lang in supported_languages if lang]
    for source_language in normalized_languages:
        for target_language in normalized_languages:
            if source_language != target_language:
                pairs.append((source_language, target_language))
    return pairs


def _model_matches_language_filter(service_name: str, model: dict, language):
    if language is None:
        return True
    supported_languages = model.get("supported_languages", [])
    if service_name == "nmt" and isinstance(language, (tuple, list)) and len(language) == 2:
        source_language = _normalize_language_value(language[0])
        target_language = _normalize_language_value(language[1])
        return bool(source_language and target_language) and source_language in supported_languages and target_language in supported_languages
    normalized_language = _normalize_language_value(language)
    if not normalized_language:
        return True
    if "all" in supported_languages:
        return True
    return normalized_language in supported_languages


def _normalize_language_value(language):
    if not isinstance(language, str):
        return ""
    return language.strip().lower()
