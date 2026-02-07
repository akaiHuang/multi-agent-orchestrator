from __future__ import annotations

import argparse

from .config import Settings
from .quality_review import review_analyzed_tasks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MarketSense quality review")
    parser.add_argument("--env-file", help="Path to env file")
    parser.add_argument("--limit", type=int, help="Max number of tasks to process")
    parser.add_argument("--dry-run", action="store_true", help="Skip LLM call and return mock review")
    parser.add_argument("--force", action="store_true", help="Re-review even if already reviewed")
    parser.add_argument("--mark-optimized", action="store_true", help="Set status=optimized")
    parser.add_argument("--brand", help="Brand name")
    parser.add_argument("--product", help="Product name")
    parser.add_argument("--objective", help="Marketing objective")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env(args.env_file)
    processed = review_analyzed_tasks(
        settings,
        limit=args.limit,
        dry_run=args.dry_run,
        force=args.force,
        mark_optimized=args.mark_optimized,
        brand=args.brand or "",
        product=args.product or "",
        objective=args.objective or "",
    )
    print(f"Quality reviewed: {processed}")


if __name__ == "__main__":
    main()
