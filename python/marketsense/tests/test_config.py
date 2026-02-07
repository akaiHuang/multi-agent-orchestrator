import os

from marketsense.config import Settings


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("FIREBASE_SERVICE_ACCOUNT", "serviceAccountKey.json")
    monkeypatch.setenv("FIREBASE_STORAGE_BUCKET", "bucket")
    monkeypatch.setenv("MAX_CONCURRENT", "5")
    monkeypatch.setenv("MIN_DELAY", "1.5")
    monkeypatch.setenv("MAX_DELAY", "3.5")
    monkeypatch.setenv("RETRIES", "2")
    monkeypatch.setenv("HEADLESS", "false")
    monkeypatch.setenv("OLLAMA_API_KEY", "test-key")
    monkeypatch.setenv("OLLAMA_API_KEY_HEADER", "X-API-Key")

    settings = Settings.from_env()

    assert settings.firebase_service_account == "serviceAccountKey.json"
    assert settings.firebase_storage_bucket == "bucket"
    assert settings.max_concurrent == 5
    assert settings.min_delay == 1.5
    assert settings.max_delay == 3.5
    assert settings.retries == 2
    assert settings.headless is False
    assert settings.ollama_api_key == "test-key"
    assert settings.ollama_api_key_header == "X-API-Key"
