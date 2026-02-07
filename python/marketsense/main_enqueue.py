from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .config import Settings
from .firebase_client import get_db_and_bucket
from .task_queue import enqueue_urls


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MarketSense enqueue URLs")
    parser.add_argument("--env-file", help="Path to env file for Firebase")
    parser.add_argument("--url", action="append", default=[], help="Target URL (can repeat)")
    parser.add_argument("--urls-file", help="File with URLs (one per line)")
    parser.add_argument("--force", action="store_true", help="Allow duplicates or requeue existing URLs")
    parser.add_argument("--brand", help="Brand name")
    parser.add_argument("--product", help="Product name")
    parser.add_argument("--objective", help="Marketing objective")
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
    settings = Settings.from_env(args.env_file)

    urls = load_urls(args)
    if not urls:
        raise SystemExit("No URLs provided. Use --url or --urls-file.")

    db, _ = get_db_and_bucket(settings)
    count = enqueue_urls(
        db,
        urls,
        allow_duplicates=args.force,
        brand=args.brand or "",
        product=args.product or "",
        objective=args.objective or "",
    )
    print(f"Enqueued: {count}")


if __name__ == "__main__":
    main()
