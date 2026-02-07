from marketsense.config import Settings
from marketsense.llm_client import LLMClient


def test_llm_client_dry_run(monkeypatch):
    monkeypatch.setenv("FIREBASE_SERVICE_ACCOUNT", "serviceAccountKey.json")
    monkeypatch.setenv("FIREBASE_STORAGE_BUCKET", "bucket")
    monkeypatch.setenv("OLLAMA_API_KEY", "dummy")
    settings = Settings.from_env()

    client = LLMClient(settings, dry_run=True)
    result = client.analyze("hello")

    assert result["sentiment_score"]
    assert result["sentiment_summary"]
    assert result["key_discussions"]
    assert result["buying_intent"]


def test_llm_quality_review_dry_run(monkeypatch):
    monkeypatch.setenv("FIREBASE_STORAGE_BUCKET", "bucket")
    monkeypatch.setenv("OLLAMA_API_KEY", "dummy")
    settings = Settings.from_env()

    client = LLMClient(settings, dry_run=True)
    result = client.review_quality({"sentiment_score": 7})

    assert result["quality_score"] >= 0
    assert "optimized_insights" in result
