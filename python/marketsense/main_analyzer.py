from __future__ import annotations

import argparse

from .analyzer import process_pending_tasks
from .config import Settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MarketSense analyzer")
    parser.add_argument("--env-file", help="Path to env file for analyzer")
    parser.add_argument("--limit", type=int, help="Max number of tasks to process")
    parser.add_argument("--dry-run", action="store_true", help="Skip LLM call and return mock analysis")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env(args.env_file)
    processed = process_pending_tasks(settings, limit=args.limit, dry_run=args.dry_run)
    print(f"Processed: {processed}")


if __name__ == "__main__":
    main()
