from __future__ import annotations

import argparse
from typing import List

from .config import Settings
from .firebase_client import get_db_and_bucket
from .reporting import summarize_tasks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MarketSense CLI dashboard")
    parser.add_argument("--env-file", help="Path to env file")
    parser.add_argument("--limit", type=int, default=200, help="Limit number of tasks")
    parser.add_argument("--status", help="Filter by status (pending/downloaded/analyzed/error)")
    return parser.parse_args()


def fetch_tasks(settings: Settings, limit: int, status: str = None) -> List[dict]:
    db, _ = get_db_and_bucket(settings)
    query = db.collection("crawling_tasks")
    if status:
        query = query.where("status", "==", status)
    if limit:
        query = query.limit(limit)
    docs = query.stream()
    return [doc.to_dict() for doc in docs]


def main() -> None:
    args = parse_args()
    settings = Settings.from_env(args.env_file)

    tasks = fetch_tasks(settings, args.limit, args.status)
    summary = summarize_tasks(tasks)

    print("=== MarketSense Dashboard ===")
    print(f"Total tasks: {summary['total']}")
    print(f"Status counts: {summary['status_counts']}")
    print(f"Blocked suspected: {summary['blocked_suspected']} ({summary['block_rate']:.2%})")
    print(f"Response status counts: {summary['response_status_counts']}")
    print(f"Avg fetch attempts: {summary['avg_fetch_attempts']:.2f}")
    print(f"Error rate: {summary['error_rate']:.2%}")
    if summary["top_block_signals"]:
        print(f"Top block signals: {summary['top_block_signals']}")


if __name__ == "__main__":
    main()
