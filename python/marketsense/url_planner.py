from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

try:
    from firebase_admin import firestore
except ImportError:  # pragma: no cover
    class _FirestoreFallback:
        SERVER_TIMESTAMP = "SERVER_TIMESTAMP"

    firestore = _FirestoreFallback()

from .config import Settings
from .firebase_client import get_db_and_bucket
from .llm_client import LLMClient
from .url_search import search_urls
from .url_validator import validate_urls


def _extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        pass
    import re

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def generate_url_plan(
    client: LLMClient,
    brand: str,
    product: str,
    objective: str,
    report: Dict[str, Any],
) -> Dict[str, Any]:
    if client.dry_run or client.settings.llm_provider.lower() == "mock":
        return {
            "search_queries": [f"{brand} {product}", f"{product} 評價", f"{product} 香氛皂"],
            "platform_categories": ["官方網站", "電商", "社群", "論壇", "媒體"],
            "keywords": [brand, product, "香氛皂", "手工皂", "療癒"],
        }

    prompt = (
        "請根據以下報告，產出可用於搜尋 URL 的規劃，輸出 JSON：\n"
        "{search_queries:[], platform_categories:[], keywords:[]}\n\n"
        f"品牌: {brand}\n產品: {product}\n目標: {objective}\n報告: {report}"
    )
    raw = client._call_llm("你是資料規劃師，輸出必須是 JSON。", prompt)
    if "error" in raw or not raw:
        return {"search_queries": [], "platform_categories": [], "keywords": []}
    return raw


def build_url_plan(
    settings: Settings,
    brand: str,
    product: str,
    objective: str,
    report: Dict[str, Any],
    manual_urls: Optional[List[str]] = None,
    auto_search: bool = False,
    limit_per_query: int = 10,
) -> Dict[str, Any]:
    client = LLMClient(settings)
    plan = generate_url_plan(client, brand, product, objective, report)

    urls: List[str] = []
    if manual_urls:
        urls.extend(manual_urls)
    if auto_search:
        queries = plan.get("search_queries", [])
        urls.extend(search_urls(queries, limit_per_query))

    # dedupe
    deduped = []
    seen = set()
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        deduped.append(url)

    allowed, rejected = validate_urls(deduped, settings)

    return {
        "brand": brand,
        "product": product,
        "objective": objective,
        "plan": plan,
        "urls": allowed,
        "rejected": rejected,
    }


def save_url_plan(settings: Settings, payload: Dict[str, Any]) -> None:
    db, _ = get_db_and_bucket(settings)
    db.collection("url_plans").add(
        {
            **payload,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )
