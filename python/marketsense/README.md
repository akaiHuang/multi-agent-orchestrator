# MarketSense (Python)

This folder contains the local batch crawler/analyzer for MarketSense.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r python/marketsense/requirements.txt
playwright install
```

## Env file

Create `python/marketsense/.env` (see `.env.example`).

### 合規與節流設定
- `ALLOW_DOMAINS` / `DENY_DOMAINS`：以逗號分隔的白名單/黑名單
- `ROBOTS_ENABLED` / `ROBOTS_USER_AGENT`：是否遵守 robots.txt 與使用的 UA
- `DOMAIN_DELAY_BASE` / `DOMAIN_DELAY_MAX`：站點級節流延遲

## Run

```bash
PYTHONPATH=python python -m marketsense.main_crawler --env-file python/marketsense/.env --urls-file urls.txt
PYTHONPATH=python python -m marketsense.main_analyzer --env-file python/marketsense/.env --limit 10
```

### 只下載到本機（避免頻繁抓取）

設定 `.env`：
```
LOCAL_RAW_DIR=./raw_html
LOCAL_STORE_ONLY=true
```

然後正常執行 crawler/analyzer，分析器會優先讀取 `local_path`。

## LLM Brief 互動分析 → 產生報告

```bash
PYTHONPATH=python python -m marketsense.main_brief --env-file python/marketsense/.env --brand "OPS" --product "Oyster Pink Studio 香氛皂" --objective "提升分享" --mode interactive
```

若想全自動：

```bash
PYTHONPATH=python python -m marketsense.main_brief --env-file python/marketsense/.env --brand "OPS" --product "Oyster Pink Studio 香氛皂" --objective "提升分享" --mode auto
```

## 產生 url.txt（可選自動搜尋）

```bash
PYTHONPATH=python python -m marketsense.main_url_planner --env-file python/marketsense/.env --report-file brief_report.json --output url.txt --json-output url_report.json --auto-search
```

## Firestore 任務佇列

先把 URL 送入 Firestore（狀態為 pending）：

```bash
PYTHONPATH=python python -m marketsense.main_enqueue --env-file python/marketsense/.env --urls-file urls.txt --brand "Apple" --product "iPhone 17" --objective "提升轉換"
# 如需忽略去重請加上 --force
```

再由 crawler 取出 pending 任務執行：

```bash
PYTHONPATH=python python -m marketsense.main_crawler --env-file python/marketsense/.env --from-firestore --limit 50 --lease-seconds 600
```

## 一鍵批次流程

```bash
PYTHONPATH=python python -m marketsense.run_pipeline --env-file python/marketsense/.env --urls-file urls.txt --use-firestore --limit-pending 50 --limit-analyze 50 --lease-seconds 600 --quality-review --brand "Apple" --product "iPhone 17" --objective "提升轉換"
```

### 品質回測與第二級優化

```bash
PYTHONPATH=python python -m marketsense.main_quality_review --env-file python/marketsense/.env --limit 50 --brand "Apple" --product "iPhone" --objective "提升轉換"
```

## 維護任務（回收鎖/重新排程）

```bash
PYTHONPATH=python python -m marketsense.main_maintenance --env-file python/marketsense/.env --reclaim-running --requeue-error-hours 24 --limit 200
```

## 報表與儀表板

匯出風險報表（JSON/CSV）：

```bash
PYTHONPATH=python python -m marketsense.main_report --env-file python/marketsense/.env --limit 200 --output-json report.json --output-csv report.csv
```

CLI 儀表板：

```bash
PYTHONPATH=python python -m marketsense.main_dashboard --env-file python/marketsense/.env --limit 200
```

## Probe (安全上限測試)

逐步提高併發並觀察封鎖訊號：

```bash
PYTHONPATH=python python -m marketsense.probe_crawler --env-file python/marketsense/.env --urls-file urls.txt --levels 1,2,3,4 --stop-block-rate 0.05
```
