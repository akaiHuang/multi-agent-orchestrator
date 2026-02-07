from __future__ import annotations

import argparse
import json
from pathlib import Path

from .briefing import run_briefing
from .config import Settings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MarketSense LLM briefing")
    parser.add_argument("--env-file", help="Path to env file")
    parser.add_argument("--brand", required=True, help="Brand name")
    parser.add_argument("--product", required=True, help="Product name")
    parser.add_argument("--objective", required=True, help="Marketing objective")
    parser.add_argument("--mode", choices=["interactive", "auto"], default="interactive")
    parser.add_argument("--max-rounds", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-firestore", action="store_true")
    parser.add_argument("--output", default="brief_report.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = Settings.from_env(args.env_file)

    result = run_briefing(
        settings,
        brand=args.brand,
        product=args.product,
        objective=args.objective,
        mode=args.mode,
        max_rounds=args.max_rounds,
        dry_run=args.dry_run,
        save_firestore=not args.no_firestore,
    )

    output_path = Path(args.output)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    md_path = output_path.with_suffix(".md")
    md_content = [
        f"# Brief Report\n\n品牌: {args.brand}\n產品: {args.product}\n目標: {args.objective}\n",
        "## Answers\n",
        json.dumps(result.get("answers", {}), ensure_ascii=False, indent=2),
        "\n\n## Report\n",
        json.dumps(result.get("report", {}), ensure_ascii=False, indent=2),
    ]
    md_path.write_text("\n".join(md_content), encoding="utf-8")

    print(f"✅ 已輸出: {output_path} & {md_path}")


if __name__ == "__main__":
    main()
