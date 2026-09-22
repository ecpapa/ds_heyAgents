"""집계된 오류 통계를 이메일로 발송한다.

사용법:
    python send_report.py --period daily
    python send_report.py --period weekly
    python send_report.py --period daily --dry-run   # 발송 없이 내용만 출력

cron 예시 (매일 오전 9시에 전날 통계 발송):
    0 9 * * * cd /path/to/repo && .venv/bin/python send_report.py --period daily
"""

import argparse

from slack_error_stats.config import Config
from slack_error_stats.mailer import send_html_email
from slack_error_stats.report import aggregate, compute_period, render_email_html
from slack_error_stats.storage import Storage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", choices=["daily", "weekly"], default="daily")
    parser.add_argument("--dry-run", action="store_true", help="발송하지 않고 내용만 출력")
    args = parser.parse_args()

    config = Config.load()
    storage = Storage(config.db_path)

    try:
        period = compute_period(args.period, config.timezone)
        errors = storage.fetch_errors_between(period.start_ts, period.end_ts)
        stats = aggregate(errors)
        html = render_email_html(period, stats)
        subject = f"[Slack 오류 리포트] {period.label} - 총 {stats['total']}건"

        if args.dry_run:
            print(subject)
            print(html)
            return

        send_html_email(
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port,
            smtp_user=config.smtp_user,
            smtp_password=config.smtp_password,
            from_addr=config.smtp_from,
            to_addrs=config.report_email_to,
            subject=subject,
            html_body=html,
        )
        print(f"[send_report] 리포트 발송 완료: {subject} -> {config.report_email_to}")
    finally:
        storage.close()


if __name__ == "__main__":
    main()
