from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone

from .config import Settings
from .firebase_client import get_db_and_bucket
from .task_queue import reclaim_expired_leases, requeue_stale_tasks, requeue_error_tasks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MarketSense maintenance tasks")
    parser.add_argument("--env-file", help="Path to env file")
    parser.add_argument("--limit", type=int, default=200, help="Limit tasks per action")
    parser.add_argument("--reclaim-running", action="store_true", help="Reclaim expired running leases")
    parser.add_argument("--requeue-analyzed-hours", type=int, help="Requeue analyzed tasks older than hours")
    parser.add_argument("--requeue-downloaded-hours", type=int, help="Requeue downloaded tasks older than hours")
    parser.add_argument("--requeue-error-hours", type=int, help="Requeue error tasks older than hours")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env(args.env_file)
    db, _ = get_db_and_bucket(settings)

    now = datetime.now(timezone.utc)
    limit = args.limit

    if args.reclaim_running:
        reclaimed = reclaim_expired_leases(db, limit, now)
        print(f"Reclaimed running: {reclaimed}")

    if args.requeue_analyzed_hours is not None:
        older_than = now - timedelta(hours=args.requeue_analyzed_hours)
        reclaimed = requeue_stale_tasks(db, "analyzed", older_than, limit)
        print(f"Requeued analyzed: {reclaimed}")

    if args.requeue_downloaded_hours is not None:
        older_than = now - timedelta(hours=args.requeue_downloaded_hours)
        reclaimed = requeue_stale_tasks(db, "downloaded", older_than, limit)
        print(f"Requeued downloaded: {reclaimed}")

    if args.requeue_error_hours is not None:
        older_than = now - timedelta(hours=args.requeue_error_hours)
        reclaimed = requeue_error_tasks(db, older_than, limit)
        print(f"Requeued errors: {reclaimed}")


if __name__ == "__main__":
    main()
