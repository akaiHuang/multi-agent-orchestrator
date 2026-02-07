from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import List

from .config import Settings
from .crawler import CrawlTarget, run_crawl


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe crawler throughput safely")
    parser.add_argument("--env-file", help="Path to env file for crawler")
    parser.add_argument("--url", action="append", default=[], help="Target URL (can repeat)")
    parser.add_argument("--urls-file", help="File with URLs (one per line)")
    parser.add_argument("--levels", default="1,2,3", help="Comma separated concurrency levels")
    parser.add_argument("--min-delay", type=float, help="Min delay seconds")
    parser.add_argument("--max-delay", type=float, help="Max delay seconds")
    parser.add_argument("--retries", type=int, help="Retry attempts")
    parser.add_argument("--stop-block-rate", type=float, default=0.05, help="Stop if blocked ratio exceeds this")
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
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        retries=args.retries,
    )

    urls = load_urls(args)
    if not urls:
        raise SystemExit("No URLs provided. Use --url or --urls-file.")
    targets = [CrawlTarget(url=url) for url in urls]

    levels = [int(x.strip()) for x in args.levels.split(",") if x.strip()]
    for level in levels:
        print(f"\n== Probe level: concurrency={level} ==")
        probe_settings = settings.with_overrides(max_concurrent=level)
        results = asyncio.run(run_crawl(targets, probe_settings))

        total = len(results)
        success = sum(1 for r in results if r.get("success"))
        blocked = sum(1 for r in results if r.get("blocked_suspected"))
        block_rate = blocked / total if total else 0

        print(f"Success: {success}/{total} | Blocked suspected: {blocked} ({block_rate:.2%})")
        if block_rate >= args.stop_block_rate:
            print("Stop: block rate exceeded threshold")
            break


if __name__ == "__main__":
    main()
