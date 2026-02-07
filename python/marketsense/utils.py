from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
import hashlib


BLOCK_PATTERNS = [
    "captcha",
    "verify you are human",
    "access denied",
    "forbidden",
    "too many requests",
]


def detect_block_signals(html: str, status: Optional[int]) -> List[str]:
    signals: List[str] = []
    if status in {403, 429}:
        signals.append(f"http_{status}")
    lower = html.lower()
    for pattern in BLOCK_PATTERNS:
        if pattern in lower:
            signals.append(pattern)
    return signals


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
    normalized = urlunparse((scheme, netloc, path, "", query, ""))
    return normalized


def url_hash(url: str) -> str:
    normalized = normalize_url(url)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def extract_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON object found in response")

    return json.loads(match.group(0))


def normalize_analysis(payload: Dict[str, Any]) -> Dict[str, Any]:
    raw_discussions = payload.get("key_discussions", [])
    if isinstance(raw_discussions, list):
        discussions = raw_discussions
    elif isinstance(raw_discussions, tuple):
        discussions = list(raw_discussions)
    elif isinstance(raw_discussions, str):
        discussions = [raw_discussions]
    else:
        discussions = []

    try:
        score = float(payload.get("sentiment_score", 0)) if payload.get("sentiment_score") is not None else 0
    except (TypeError, ValueError):
        score = 0

    score = max(0.0, min(10.0, score))

    return {
        "sentiment_score": score,
        "sentiment_summary": str(payload.get("sentiment_summary", "")),
        "key_discussions": discussions,
        "buying_intent": str(payload.get("buying_intent", "")),
    }
