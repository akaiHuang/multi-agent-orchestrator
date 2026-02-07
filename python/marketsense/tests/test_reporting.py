from marketsense.reporting import summarize_tasks, task_rows


def test_summarize_tasks_basic():
    tasks = [
        {"status": "downloaded", "blocked_suspected": False, "response_status": 200, "fetch_attempts": 1},
        {
            "status": "analyzed",
            "blocked_suspected": True,
            "response_status": 403,
            "block_signals": ["captcha"],
            "fetch_attempts": 2,
            "quality_review": {"quality_score": 80, "quality_pass": True},
        },
        {"status": "error", "error_log": "fail"},
    ]

    summary = summarize_tasks(tasks)
    assert summary["total"] == 3
    assert summary["status_counts"]["downloaded"] == 1
    assert summary["status_counts"]["analyzed"] == 1
    assert summary["status_counts"]["error"] == 1
    assert summary["blocked_suspected"] == 1
    assert summary["response_status_counts"]["200"] == 1
    assert summary["response_status_counts"]["403"] == 1
    assert summary["avg_fetch_attempts"] > 0
    assert summary["avg_quality_score"] >= 0


def test_task_rows_shape():
    rows = task_rows([{"url": "https://example.com", "status": "downloaded"}])
    assert rows[0]["url"] == "https://example.com"
    assert rows[0]["status"] == "downloaded"
