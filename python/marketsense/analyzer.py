from __future__ import annotations

import gzip
from typing import Optional

try:
    import trafilatura
except ImportError:  # pragma: no cover - fallback when dependency not installed
    trafilatura = None
try:
    from firebase_admin import firestore
except ImportError:  # pragma: no cover - fallback for test environments
    class _FirestoreFallback:
        SERVER_TIMESTAMP = "SERVER_TIMESTAMP"

    firestore = _FirestoreFallback()

from .config import Settings
from .firebase_client import get_db_and_bucket
from .llm_client import LLMClient


def clean_html_smart(html_content: str, max_chars: int) -> str:
    if trafilatura is None:
        # Fallback: strip basic HTML tags to keep pipeline usable without dependency.
        text = html_content
        text = text.replace("\n", " ")
        while "<" in text and ">" in text:
            start = text.find("<")
            end = text.find(">", start)
            if end == -1:
                break
            text = text[:start] + " " + text[end + 1 :]
    else:
        text = trafilatura.extract(html_content, include_comments=True)
    if text is None:
        return ""
    return text[:max_chars]


def process_pending_tasks(settings: Settings, limit: Optional[int] = None, dry_run: bool = False) -> int:
    db, bucket = get_db_and_bucket(settings)

    if not settings.firebase_storage_bucket and not settings.local_raw_dir:
        raise ValueError("FIREBASE_STORAGE_BUCKET or LOCAL_RAW_DIR is required")

    docs = db.collection("crawling_tasks").where("status", "==", "downloaded").stream()
    client = LLMClient(settings, dry_run=dry_run)

    processed = 0
    for doc in docs:
        if limit is not None and processed >= limit:
            break

        data = doc.to_dict()
        title = data.get("title", "")
        url = data.get("url", "")

        try:
            raw_bytes = None
            local_path = data.get("local_path")
            if local_path:
                try:
                    with open(local_path, "rb") as handle:
                        raw_bytes = handle.read()
                except Exception as exc:
                    raise RuntimeError(f"Failed to read local_path: {exc}") from exc

            if raw_bytes is None and data.get("storage_path"):
                blob = bucket.blob(data["storage_path"])
                raw_bytes = blob.download_as_bytes()

            if raw_bytes is None:
                raise RuntimeError("No raw bytes available (missing local_path/storage_path)")

            if (data.get("storage_path") or "").endswith(".gz") or (local_path or "").endswith(".gz"):
                try:
                    html_content = gzip.decompress(raw_bytes).decode("utf-8")
                except Exception:
                    html_content = raw_bytes.decode("utf-8")
            else:
                html_content = raw_bytes.decode("utf-8")

            clean_text = clean_html_smart(html_content, settings.max_text_chars)
            analysis_result = client.analyze(clean_text, title=title, url=url)

            if "error" in analysis_result:
                doc.reference.update(
                    {
                        "analysis": analysis_result,
                        "status": "error",
                        "error_log": analysis_result.get("error"),
                        "analyzed_at": firestore.SERVER_TIMESTAMP,
                    }
                )
            else:
                doc.reference.update(
                    {
                        "analysis": analysis_result,
                        "status": "analyzed",
                        "analyzed_at": firestore.SERVER_TIMESTAMP,
                    }
                )
            processed += 1
        except Exception as exc:
            doc.reference.update({"status": "error", "error_log": str(exc)})

    return processed
