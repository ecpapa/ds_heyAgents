from datetime import datetime
from zoneinfo import ZoneInfo

from slack_error_stats.report import aggregate, compute_period

KST = ZoneInfo("Asia/Seoul")


def test_aggregate_counts_by_type_severity_and_user():
    errors = [
        {"ts": "1", "user": "U1", "text": "a", "permalink": None,
         "error_type": "API 타임아웃", "severity": "high", "summary": "s1"},
        {"ts": "2", "user": "U1", "text": "b", "permalink": None,
         "error_type": "API 타임아웃", "severity": "medium", "summary": "s2"},
        {"ts": "3", "user": "U2", "text": "c", "permalink": None,
         "error_type": "", "severity": "", "summary": ""},
    ]

    stats = aggregate(errors)

    assert stats["total"] == 3
    assert stats["by_type"][0] == ("API 타임아웃", 2)
    assert ("미분류", 1) in stats["by_type"]
    assert ("미지정", 1) in stats["by_severity"]
    assert stats["top_users"][0] == ("U1", 2)


def test_aggregate_empty_list():
    stats = aggregate([])
    assert stats["total"] == 0
    assert stats["by_type"] == []
    assert stats["top_users"] == []


def test_compute_period_daily_is_previous_full_day():
    now = datetime(2026, 9, 22, 10, 30, tzinfo=KST)
    period = compute_period("daily", KST, now=now)

    assert period.start == datetime(2026, 9, 21, 0, 0, tzinfo=KST)
    assert period.end == datetime(2026, 9, 22, 0, 0, tzinfo=KST)
    assert period.label == "2026-09-21"


def test_compute_period_weekly_is_previous_monday_to_sunday():
    # 2026-09-22는 화요일
    now = datetime(2026, 9, 22, 10, 30, tzinfo=KST)
    period = compute_period("weekly", KST, now=now)

    assert period.start == datetime(2026, 9, 14, 0, 0, tzinfo=KST)  # 지난주 월요일
    assert period.end == datetime(2026, 9, 21, 0, 0, tzinfo=KST)  # 이번주 월요일
    assert period.label == "2026-09-14 ~ 2026-09-20"
