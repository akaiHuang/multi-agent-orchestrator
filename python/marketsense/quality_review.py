from __future__ import annotations

from typing import Any, Dict, Optional

try:
    from firebase_admin import firestore
except ImportError:  # pragma: no cover - fallback for test environments
    class _FirestoreFallback:
        SERVER_TIMESTAMP = "SERVER_TIMESTAMP"

    firestore = _FirestoreFallback()

from .config import Settings
from .firebase_client import get_db_and_bucket
from .llm_client import LLMClient


def _normalize_quality(payload: Dict[str, Any]) -> Dict[str, Any]:
    score = payload.get("quality_score", 0)
    try:
        score = int(score)
    except (TypeError, ValueError):
        score = 0

    quality_pass = payload.get("quality_pass")
    if isinstance(quality_pass, str):
        quality_pass = quality_pass.lower() in {"true", "1", "yes", "y"}
    elif not isinstance(quality_pass, bool):
        quality_pass = score >= 70

    issues = payload.get("issues") or []
    if isinstance(issues, str):
        issues = [issues]
    if not isinstance(issues, list):
        issues = []

    optimized_insights = payload.get("optimized_insights") or {}
    if not isinstance(optimized_insights, dict):
        optimized_insights = {}

    return {
        "quality_score": max(0, min(100, score)),
        "quality_pass": bool(quality_pass),
        "issues": issues,
        "notes": payload.get("notes", ""),
        "optimized_insights": optimized_insights,
    }


def review_analyzed_tasks(
    settings: Settings,
    limit: Optional[int] = None,
    dry_run: bool = False,
    force: bool = False,
    mark_optimized: bool = False,
    brand: str = "",
    product: str = "",
    objective: str = "",
) -> int:
    db, _ = get_db_and_bucket(settings)
    docs = db.collection("crawling_tasks").where("status", "==", "analyzed").stream()
    client = LLMClient(settings, dry_run=dry_run)

    processed = 0
    for doc in docs:
        if limit is not None and processed >= limit:
            break

        data = doc.to_dict()
        if not force and data.get("quality_reviewed_at"):
            continue

        title = data.get("title", "")
        url = data.get("url", "")
        analysis = data.get("analysis", {})

        result = client.review_quality(
            analysis=analysis,
            title=title,
            url=url,
            brand=brand or data.get("brand", ""),
            product=product or data.get("product", ""),
            objective=objective or data.get("objective", ""),
        )

        if "error" in result:
            doc.reference.update(
                {
                    "quality_review": {"error": result.get("error"), "raw": result.get("raw", "")},
                    "quality_reviewed_at": firestore.SERVER_TIMESTAMP,
                }
            )
        else:
            normalized = _normalize_quality(result)
            payload = {
                "quality_review": normalized,
                "quality_reviewed_at": firestore.SERVER_TIMESTAMP,
                "optimized_insights": normalized.get("optimized_insights", {}),
                "optimized_at": firestore.SERVER_TIMESTAMP,
            }
            if mark_optimized:
                payload["status"] = "optimized"
            doc.reference.update(payload)

        processed += 1

    return processed
