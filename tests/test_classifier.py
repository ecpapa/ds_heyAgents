from slack_error_stats.classifier import ErrorClassifier


def test_parse_json_plain():
    data = ErrorClassifier._parse_json(
        '{"is_error": true, "error_type": "DB 오류", "severity": "high", "summary": "s"}'
    )
    assert data["is_error"] is True
    assert data["error_type"] == "DB 오류"


def test_parse_json_wrapped_in_code_block():
    raw = '```json\n{"is_error": false, "error_type": "", "severity": "", "summary": ""}\n```'
    data = ErrorClassifier._parse_json(raw)
    assert data["is_error"] is False


def test_parse_json_invalid_falls_back_to_not_error():
    data = ErrorClassifier._parse_json("이건 JSON이 아님")
    assert data == {"is_error": False, "error_type": "", "severity": "", "summary": ""}
