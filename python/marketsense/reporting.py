from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Tuple
from urllib.parse import urlparse


def summarize_tasks(tasks: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    task_list = list(tasks)
    total = len(task_list)

    status_counts: Counter[str] = Counter()
    response_status_counts: Counter[str] = Counter()
    block_signal_counts: Counter[str] = Counter()

    blocked_count = 0
    eligible_count = 0
    fetch_attempts_total = 0
    fetch_attempts_count = 0
    errors = 0
    latency_values: List[int] = []
    domain_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "blocked": 0})
    quality_scores: List[int] = []
    quality_pass_count = 0

    for task in task_list:
        status = task.get("status", "unknown")
        status_counts[status] += 1

        if task.get("blocked_suspected") is not None:
            eligible_count += 1
            if task.get("blocked_suspected"):
                blocked_count += 1

        response_status = task.get("response_status")
        if response_status is not None:
            response_status_counts[str(response_status)] += 1

        block_signals = task.get("block_signals") or []
        if isinstance(block_signals, list):
            block_signal_counts.update(block_signals)
        elif isinstance(block_signals, str):
            block_signal_counts.update([block_signals])

        fetch_attempts = task.get("fetch_attempts")
        if isinstance(fetch_attempts, int):
            fetch_attempts_total += fetch_attempts
            fetch_attempts_count += 1

        if status == "error":
            errors += 1

        latency = task.get("fetch_latency_ms")
        if isinstance(latency, int):
            latency_values.append(latency)

        url = task.get("url", "")
        if url:
            domain = urlparse(url).netloc.lower()
            if domain:
                domain_stats[domain]["total"] += 1
                if task.get("blocked_suspected"):
                    domain_stats[domain]["blocked"] += 1

        quality = task.get("quality_review")
        if isinstance(quality, dict):
            score = quality.get("quality_score")
            if isinstance(score, int):
                quality_scores.append(score)
            elif isinstance(score, float):
                quality_scores.append(int(score))
            if quality.get("quality_pass") is True:
                quality_pass_count += 1

    avg_fetch_attempts = fetch_attempts_total / fetch_attempts_count if fetch_attempts_count else 0
    block_rate = blocked_count / eligible_count if eligible_count else 0
    error_rate = errors / total if total else 0

    latency_values_sorted = sorted(latency_values)
    avg_latency = sum(latency_values_sorted) / len(latency_values_sorted) if latency_values_sorted else 0
    p50 = _percentile(latency_values_sorted, 50)
    p95 = _percentile(latency_values_sorted, 95)

    domain_metrics = []
    for domain, stats in domain_stats.items():
        total_count = stats["total"]
        blocked = stats["blocked"]
        domain_metrics.append(
            {
                "domain": domain,
                "total": total_count,
                "blocked": blocked,
                "block_rate": blocked / total_count if total_count else 0,
            }
        )
    domain_metrics.sort(key=lambda item: item["block_rate"], reverse=True)

    return {
        "total": total,
        "status_counts": dict(status_counts),
        "blocked_suspected": blocked_count,
        "block_rate": block_rate,
        "response_status_counts": dict(response_status_counts),
        "top_block_signals": block_signal_counts.most_common(10),
        "avg_fetch_attempts": avg_fetch_attempts,
        "error_rate": error_rate,
        "avg_latency_ms": avg_latency,
        "p50_latency_ms": p50,
        "p95_latency_ms": p95,
        "domain_block_rates": domain_metrics[:10],
        "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
        "quality_pass_rate": quality_pass_count / len(quality_scores) if quality_scores else 0,
    }


def _percentile(values: List[int], percentile: int) -> float:
    if not values:
        return 0
    k = (len(values) - 1) * (percentile / 100)
    f = int(k)
    c = min(f + 1, len(values) - 1)
    if f == c:
        return float(values[f])
    d0 = values[f] * (c - k)
    d1 = values[c] * (k - f)
    return float(d0 + d1)


def task_rows(tasks: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for task in tasks:
        rows.append(
            {
                "url": task.get("url", ""),
                "status": task.get("status", ""),
                "response_status": task.get("response_status", ""),
                "blocked_suspected": task.get("blocked_suspected", ""),
                "fetch_attempts": task.get("fetch_attempts", ""),
                "fetch_latency_ms": task.get("fetch_latency_ms", ""),
                "title": task.get("title", ""),
                "storage_path": task.get("storage_path", ""),
                "local_path": task.get("local_path", ""),
                "quality_score": (task.get("quality_review") or {}).get("quality_score", ""),
                "quality_pass": (task.get("quality_review") or {}).get("quality_pass", ""),
                "error_log": task.get("error_log", ""),
                "created_at": str(task.get("created_at", "")),
                "analyzed_at": str(task.get("analyzed_at", "")),
                "quality_reviewed_at": str(task.get("quality_reviewed_at", "")),
            }
        )
    return rows
