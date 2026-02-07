from marketsense.quality_review import review_analyzed_tasks
from marketsense.config import Settings


class FakeDocRef:
    def __init__(self, data):
        self.data = data
        self.updated = None

    def update(self, payload):
        self.updated = payload
        self.data.update(payload)


class FakeDoc:
    def __init__(self, data):
        self._data = data
        self.reference = FakeDocRef(data)

    def to_dict(self):
        return self._data


class FakeCollection:
    def __init__(self, docs):
        self._docs = docs

    def where(self, *_args, **_kwargs):
        return self

    def stream(self):
        return self._docs


class FakeDB:
    def __init__(self, docs):
        self._collection = FakeCollection(docs)

    def collection(self, _name: str):
        return self._collection


def test_quality_review_dry_run(monkeypatch):
    monkeypatch.setenv("FIREBASE_STORAGE_BUCKET", "bucket")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    settings = Settings.from_env()

    fake_doc = FakeDoc(
        {"status": "analyzed", "analysis": {"sentiment_score": 7}, "title": "T", "url": "U"}
    )

    def fake_get_db_and_bucket(_settings):
        return FakeDB([fake_doc]), None

    monkeypatch.setattr("marketsense.quality_review.get_db_and_bucket", fake_get_db_and_bucket)

    processed = review_analyzed_tasks(settings, limit=1, dry_run=True)
    assert processed == 1
    assert fake_doc.reference.updated is not None
    assert "quality_review" in fake_doc.reference.updated
