from __future__ import annotations

import os
from typing import List

import requests


def search_with_serpapi(query: str, limit: int = 10) -> List[str]:
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return []

    engine = os.getenv("SERPAPI_ENGINE", "google")
    params = {
        "engine": engine,
        "q": query,
        "api_key": api_key,
        "num": limit,
    }
    resp = requests.get("https://serpapi.com/search.json", params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    urls = []
    for item in data.get("organic_results", []):
        link = item.get("link")
        if link:
            urls.append(link)
    return urls


def search_urls(queries: List[str], limit_per_query: int = 10) -> List[str]:
    urls: List[str] = []
    for query in queries:
        urls.extend(search_with_serpapi(query, limit_per_query))
    # dedupe
    seen = set()
    deduped = []
    for url in urls:
        if url in seen:
            continue
        seen.add(url)
        deduped.append(url)
    return deduped
