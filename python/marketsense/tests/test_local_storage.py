from pathlib import Path
import gzip

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


class FakeBucket:
    def blob(self, _path: str):
        raise AssertionError("Should not access Firebase when local_path exists")


def test_analyzer_reads_local_path(tmp_path, monkeypatch):
    html = "<html><body>Hello</body></html>".encode("utf-8")
    raw_path = tmp_path / "sample.html.gz"
    raw_path.write_bytes(gzip.compress(html))

    fake_doc = FakeDoc({"status": "downloaded", "local_path": str(raw_path)})

    def fake_get_db_and_bucket(_settings):
        return FakeDB([fake_doc]), FakeBucket()

    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LOCAL_RAW_DIR", str(tmp_path))

    settings = Settings.from_env()
    monkeypatch.setattr("marketsense.analyzer.get_db_and_bucket", fake_get_db_and_bucket)

    processed = process_pending_tasks(settings, limit=1, dry_run=True)
    assert processed == 1
    assert fake_doc.reference.updated is not None
