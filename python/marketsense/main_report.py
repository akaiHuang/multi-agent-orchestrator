from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import List

from .config import Settings
from .firebase_client import get_db_and_bucket
from .reporting import summarize_tasks, task_rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="MarketSense report exporter")
    parser.add_argument("--env-file", help="Path to env file")
    parser.add_argument("--limit", type=int, default=200, help="Limit number of tasks")
    parser.add_argument("--status", help="Filter by status (pending/downloaded/analyzed/error)")
    parser.add_argument("--output-json", help="Write summary JSON to path")
    parser.add_argument("--output-csv", help="Write task rows CSV to path")
    parser.add_argument("--include-tasks", action="store_true", help="Include tasks in JSON output")
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


def write_json(path: str, summary: dict, tasks: List[dict], include_tasks: bool) -> None:
    payload = {"summary": summary}
    if include_tasks:
        payload["tasks"] = tasks
    Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: str, tasks: List[dict]) -> None:
    rows = task_rows(tasks)
    if not rows:
        Path(path).write_text("", encoding="utf-8")
        return
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    settings = Settings.from_env(args.env_file)

    tasks = fetch_tasks(settings, args.limit, args.status)
    summary = summarize_tasks(tasks)

    if args.output_json:
        write_json(args.output_json, summary, tasks, args.include_tasks)
    if args.output_csv:
        write_csv(args.output_csv, tasks)

    if not args.output_json and not args.output_csv:
        print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
