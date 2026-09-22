from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


@dataclass
class ReportPeriod:
    start: datetime
    end: datetime
    label: str

    @property
    def start_ts(self) -> float:
        return self.start.timestamp()

    @property
    def end_ts(self) -> float:
        return self.end.timestamp()


def compute_period(period_name: str, tz: ZoneInfo, now: datetime | None = None) -> ReportPeriod:
    """'daily' 또는 'weekly' 리포트 기간을 계산한다 (오늘/이번주는 제외, 직전 기간 기준)."""
    now = (now or datetime.now(tz)).astimezone(tz)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period_name == "daily":
        end = today
        start = end - timedelta(days=1)
        label = start.strftime("%Y-%m-%d")
    elif period_name == "weekly":
        end = today - timedelta(days=today.weekday())  # 이번 주 월요일 0시
        start = end - timedelta(days=7)
        label = f"{start.strftime('%Y-%m-%d')} ~ {(end - timedelta(days=1)).strftime('%Y-%m-%d')}"
    else:
        raise ValueError(f"알 수 없는 period: {period_name}")

    return ReportPeriod(start=start, end=end, label=label)


def aggregate(errors: list[dict]) -> dict:
    """오류 레코드 리스트를 받아 통계 요약을 만든다."""
    total = len(errors)
    by_type = Counter(e["error_type"] or "미분류" for e in errors)
    by_severity = Counter(e["severity"] or "미지정" for e in errors)
    by_user = Counter(e["user"] or "unknown" for e in errors)

    return {
        "total": total,
        "by_type": by_type.most_common(),
        "by_severity": by_severity.most_common(),
        "top_users": by_user.most_common(5),
        "errors": errors,
    }


def render_email_html(period: ReportPeriod, stats: dict) -> str:
    def rows(counter_items: list[tuple[str, int]]) -> str:
        if not counter_items:
            return "<tr><td colspan='2'>없음</td></tr>"
        return "".join(
            f"<tr><td>{name}</td><td>{count}</td></tr>" for name, count in counter_items
        )

    error_rows = "".join(
        f"<tr><td>{e['error_type'] or '미분류'}</td>"
        f"<td>{e['severity'] or '-'}</td>"
        f"<td>{e['summary'] or e['text'][:80]}</td>"
        f"<td><a href='{e['permalink']}'>링크</a></td></tr>"
        for e in stats["errors"]
    ) or "<tr><td colspan='4'>해당 기간 오류 없음</td></tr>"

    return f"""
    <html>
    <body style="font-family: sans-serif;">
      <h2>Slack 오류 모니터링 리포트 ({period.label})</h2>
      <p>총 오류 건수: <b>{stats['total']}</b>건</p>

      <h3>유형별</h3>
      <table border="1" cellpadding="6" cellspacing="0">{rows(stats['by_type'])}</table>

      <h3>심각도별</h3>
      <table border="1" cellpadding="6" cellspacing="0">{rows(stats['by_severity'])}</table>

      <h3>보고자 Top 5</h3>
      <table border="1" cellpadding="6" cellspacing="0">{rows(stats['top_users'])}</table>

      <h3>상세 목록</h3>
      <table border="1" cellpadding="6" cellspacing="0">
        <tr><th>유형</th><th>심각도</th><th>요약</th><th>원문</th></tr>
        {error_rows}
      </table>
    </body>
    </html>
    """
