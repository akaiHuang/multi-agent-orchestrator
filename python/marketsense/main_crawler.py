from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import List

from .config import Settings
from .crawler import CrawlTarget, run_crawl
from .firebase_client import get_db_and_bucket
from datetime import datetime, timezone

from .task_queue import claim_pending_tasks, reclaim_expired_leases


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MarketSense crawler")
    parser.add_argument("--env-file", help="Path to env file for crawler")
    parser.add_argument("--url", action="append", default=[], help="Target URL (can repeat)")
    parser.add_argument("--urls-file", help="File with URLs (one per line)")
    parser.add_argument("--from-firestore", action="store_true", help="Fetch pending tasks from Firestore")
    parser.add_argument("--limit", type=int, default=50, help="Limit pending tasks from Firestore")
    parser.add_argument("--lease-seconds", type=int, default=600, help="Lease duration for running tasks")
    parser.add_argument("--brand", help="Brand name")
    parser.add_argument("--product", help="Product name")
    parser.add_argument("--objective", help="Marketing objective")
    parser.add_argument("--max-concurrent", type=int, help="Max concurrent pages")
    parser.add_argument("--min-delay", type=float, help="Min delay seconds")
    parser.add_argument("--max-delay", type=float, help="Max delay seconds")
    parser.add_argument("--retries", type=int, help="Retry attempts")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=None)
    parser.add_argument("--user-agent", help="Override user agent")
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
        headless=args.headless,
        user_agent=args.user_agent,
    )

    targets: List[CrawlTarget]
    if args.from_firestore:
        db, _ = get_db_and_bucket(settings)
        reclaim_expired_leases(db, args.limit, datetime.now(timezone.utc))
        pending = claim_pending_tasks(db, args.limit, lease_seconds=args.lease_seconds)
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
        urls = load_urls(args)
        if not urls:
            raise SystemExit("No URLs provided. Use --url or --urls-file.")
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
    print(f"Completed: {success}/{len(results)} | Blocked suspected: {blocked}")


if __name__ == "__main__":
    main()
