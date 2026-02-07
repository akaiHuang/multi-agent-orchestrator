from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from .config import Settings
from .url_planner import build_url_plan, save_url_plan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MarketSense URL planner")
    parser.add_argument("--env-file", help="Path to env file")
    parser.add_argument("--report-file", required=True, help="Brief report JSON path")
    parser.add_argument("--output", default="url.txt", help="Output url list")
    parser.add_argument("--json-output", default="url_report.json", help="Output report JSON")
    parser.add_argument("--manual-urls-file", help="Manual URLs file to merge")
    parser.add_argument("--auto-search", action="store_true", help="Use search provider (SERPAPI)")
    parser.add_argument("--limit-per-query", type=int, default=10)
    parser.add_argument("--brand", help="Brand name override")
    parser.add_argument("--product", help="Product name override")
    parser.add_argument("--objective", help="Marketing objective override")
    parser.add_argument("--no-firestore", action="store_true")
    return parser.parse_args()


def load_manual_urls(path_str: str) -> List[str]:
    if not path_str:
        return []
    content = Path(path_str).read_text(encoding="utf-8")
    urls = []
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(line)
    return urls


def main() -> None:
    args = parse_args()
    settings = Settings.from_env(args.env_file)

    report = json.loads(Path(args.report_file).read_text(encoding="utf-8"))
    brand = args.brand or report.get("brand", "")
    product = args.product or report.get("product", "")
    objective = args.objective or report.get("objective", "")

    manual_urls = load_manual_urls(args.manual_urls_file) if args.manual_urls_file else []

    payload = build_url_plan(
        settings,
        brand=brand,
        product=product,
        objective=objective,
        report=report.get("report", report),
        manual_urls=manual_urls,
        auto_search=args.auto_search,
        limit_per_query=args.limit_per_query,
    )

    Path(args.output).write_text("\n".join(payload["urls"]) + "\n", encoding="utf-8")
    Path(args.json_output).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if not args.no_firestore:
        save_url_plan(settings, payload)

    print(f"✅ 已產出: {args.output} & {args.json_output}")


if __name__ == "__main__":
    main()
