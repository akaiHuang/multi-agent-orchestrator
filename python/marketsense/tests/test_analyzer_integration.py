from marketsense.analyzer import process_pending_tasks
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


class FakeBlob:
    def __init__(self, content: bytes):
        self._content = content

    def download_as_bytes(self):
        return self._content


class FakeBucket:
    def __init__(self, payload: bytes):
        self._payload = payload

    def blob(self, _path: str):
        return FakeBlob(self._payload)


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


def test_process_pending_tasks(monkeypatch):
    html = b"<html><body><p>Hello</p></body></html>"
    fake_doc = FakeDoc({"storage_path": "raw_html/1.html.gz", "title": "T", "url": "U"})

    monkeypatch.setenv("FIREBASE_STORAGE_BUCKET", "bucket")
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    settings = Settings.from_env()

    def fake_get_db_and_bucket(_settings):
        return FakeDB([fake_doc]), FakeBucket(html)

    monkeypatch.setattr("marketsense.analyzer.get_db_and_bucket", fake_get_db_and_bucket)

    processed = process_pending_tasks(settings, limit=1, dry_run=True)
    assert processed == 1
    assert fake_doc.reference.updated is not None
    assert fake_doc.reference.updated.get("status") in {"analyzed", "error"}
