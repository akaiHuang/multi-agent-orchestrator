from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import List

from .analyzer import process_pending_tasks
from .config import Settings
from .crawler import CrawlTarget, run_crawl
from .firebase_client import get_db_and_bucket
from .quality_review import review_analyzed_tasks
from datetime import datetime, timedelta, timezone

from .task_queue import (
    enqueue_urls,
    claim_pending_tasks,
    reclaim_expired_leases,
    requeue_stale_tasks,
    requeue_error_tasks,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MarketSense local batch pipeline")
    parser.add_argument("--env-file", help="Path to env file")
    parser.add_argument("--url", action="append", default=[], help="Target URL (can repeat)")
    parser.add_argument("--urls-file", help="File with URLs (one per line)")
    parser.add_argument("--use-firestore", action="store_true", help="Use Firestore pending queue")
    parser.add_argument("--limit-pending", type=int, default=50, help="Limit pending tasks")
    parser.add_argument("--lease-seconds", type=int, default=600, help="Lease duration for running tasks")
    parser.add_argument("--limit-analyze", type=int, help="Limit analyzed tasks")
    parser.add_argument("--dry-run", action="store_true", help="Skip LLM call and return mock analysis")
    parser.add_argument("--quality-review", action="store_true", help="Run LLM quality review and optimization")
    parser.add_argument("--brand", help="Brand name")
    parser.add_argument("--product", help="Product name")
    parser.add_argument("--objective", help="Marketing objective")
    parser.add_argument("--max-concurrent", type=int, help="Max concurrent pages")
    parser.add_argument("--min-delay", type=float, help="Min delay seconds")
    parser.add_argument("--max-delay", type=float, help="Max delay seconds")
    parser.add_argument("--retries", type=int, help="Retry attempts")
    return parser.parse_args()


def load_urls(args: argparse.Namespace) -> List[str]:
    urls = list(args.url)

    if args.urls_file:
        content = Path(args.urls_file).read_text(encoding="utf-8")
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                urls.append(line)

    return urls


def main() -> None:
    args = parse_args()
    settings = Settings.from_env(args.env_file).with_overrides(
        max_concurrent=args.max_concurrent,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        retries=args.retries,
    )

    urls = load_urls(args)
    if not urls:
        raise SystemExit("No URLs provided. Use --url or --urls-file.")

    if args.use_firestore:
        db, _ = get_db_and_bucket(settings)
        now = datetime.now(timezone.utc)
        reclaim_expired_leases(db, args.limit_pending, now)
        if settings.requeue_analyzed_after_hours > 0:
            requeue_stale_tasks(
                db,
                "analyzed",
                now - timedelta(hours=settings.requeue_analyzed_after_hours),
                args.limit_pending,
            )
        if settings.requeue_downloaded_after_hours > 0:
            requeue_stale_tasks(
                db,
                "downloaded",
                now - timedelta(hours=settings.requeue_downloaded_after_hours),
                args.limit_pending,
            )
        if settings.requeue_error_after_hours > 0:
            requeue_error_tasks(
                db,
                now - timedelta(hours=settings.requeue_error_after_hours),
                args.limit_pending,
            )
        enqueue_urls(
            db,
            urls,
            brand=args.brand or "",
            product=args.product or "",
            objective=args.objective or "",
        )
        pending = claim_pending_tasks(db, args.limit_pending, lease_seconds=args.lease_seconds)
        if not pending:
            raise SystemExit("No pending tasks found in Firestore.")
        targets = [
            CrawlTarget(
                url=data.get("url", ""),
                ref=ref,
                brand=data.get("brand", "") or (args.brand or ""),
                product=data.get("product", "") or (args.product or ""),
                objective=data.get("objective", "") or (args.objective or ""),
            )
            for ref, data in pending
            if data.get("url")
        ]
    else:
        targets = [
            CrawlTarget(
                url=url,
                brand=args.brand or "",
                product=args.product or "",
                objective=args.objective or "",
            )
            for url in urls
        ]

    results = asyncio.run(run_crawl(targets, settings))
    success = sum(1 for r in results if r.get("success"))
    blocked = sum(1 for r in results if r.get("blocked_suspected"))
    print(f"Crawler completed: {success}/{len(results)} | Blocked suspected: {blocked}")

    processed = process_pending_tasks(settings, limit=args.limit_analyze, dry_run=args.dry_run)
    print(f"Analyzer processed: {processed}")

    if args.quality_review:
        reviewed = review_analyzed_tasks(
            settings,
            limit=args.limit_analyze,
            dry_run=args.dry_run,
            brand=args.brand or "",
            product=args.product or "",
            objective=args.objective or "",
        )
        print(f"Quality reviewed: {reviewed}")


if __name__ == "__main__":
    main()
