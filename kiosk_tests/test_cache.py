import json

from kiosk_app.cache import STATIC_PHRASES_EN, StaticPhraseCache


def test_disk_cache_accepts_only_static_non_personal_phrases(tmp_path):
    cache = StaticPhraseCache(tmp_path)
    greeting = STATIC_PHRASES_EN["greeting"]

    cache.store_translation(greeting, "ta", "தமிழ் வாழ்த்து")
    cache.store_audio(greeting, "ta", b"RIFFstatic")
    cache.store_translation("citizen-specific income and age", "ta", "private content")
    cache.store_audio("citizen-specific income and age", "ta", b"private")

    assert cache.get_translation(greeting, "ta") == "தமிழ் வாழ்த்து"
    assert cache.get_audio(greeting, "ta") == b"RIFFstatic"
    assert cache.get_translation("citizen-specific income and age", "ta") is None
    files = list(cache.directory.iterdir())
    assert len(files) == 2
    assert all("private" not in path.read_text(encoding="utf-8") for path in files if path.suffix == ".json")
