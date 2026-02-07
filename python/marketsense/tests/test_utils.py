from marketsense.utils import detect_block_signals, extract_json, normalize_analysis, normalize_url, url_hash


def test_detect_block_signals_status():
    html = "<html><body>OK</body></html>"
    signals = detect_block_signals(html, 403)
    assert "http_403" in signals


def test_detect_block_signals_content():
    html = "<html>captcha required</html>"
    signals = detect_block_signals(html, 200)
    assert "captcha" in signals


def test_extract_json_direct():
    payload = "{\"a\": 1}"
    assert extract_json(payload)["a"] == 1


def test_extract_json_embedded():
    payload = "prefix {\"a\": 2, \"b\": \"x\"} suffix"
    parsed = extract_json(payload)
    assert parsed["a"] == 2
    assert parsed["b"] == "x"


def test_normalize_analysis_discussions():
    payload = {
        "sentiment_score": 5,
        "sentiment_summary": "ok",
        "key_discussions": "battery",
        "buying_intent": "中",
    }
    normalized = normalize_analysis(payload)
    assert normalized["key_discussions"] == ["battery"]


def test_normalize_analysis_score_clamped():
    payload = {"sentiment_score": 99, "sentiment_summary": "", "key_discussions": [], "buying_intent": ""}
    normalized = normalize_analysis(payload)
    assert normalized["sentiment_score"] == 10.0


def test_normalize_url_and_hash():
    raw = "HTTPS://Example.com/path/?b=2&a=1#frag"
    normalized = normalize_url(raw)
    assert normalized == "https://example.com/path?a=1&b=2"
    assert url_hash(raw) == url_hash(normalized)
