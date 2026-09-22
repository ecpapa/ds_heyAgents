import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"환경 변수 {name}이(가) 설정되지 않았습니다. .env 파일을 확인하세요.")
    return value


@dataclass(frozen=True)
class Config:
    slack_bot_token: str
    slack_channel_id: str
    anthropic_api_key: str
    anthropic_model: str
    smtp_host: str | None
    smtp_port: int
    smtp_user: str | None
    smtp_password: str | None
    smtp_from: str | None
    report_email_to: list[str]
    timezone: ZoneInfo
    db_path: str

    @staticmethod
    def load() -> "Config":
        smtp_user = os.environ.get("SMTP_USER")
        return Config(
            slack_bot_token=_require("SLACK_BOT_TOKEN"),
            slack_channel_id=_require("SLACK_CHANNEL_ID"),
            anthropic_api_key=_require("ANTHROPIC_API_KEY"),
            anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
            smtp_host=os.environ.get("SMTP_HOST"),
            smtp_port=int(os.environ.get("SMTP_PORT", "587")),
            smtp_user=smtp_user,
            smtp_password=os.environ.get("SMTP_PASSWORD"),
            smtp_from=os.environ.get("SMTP_FROM") or smtp_user,
            report_email_to=[
                addr.strip()
                for addr in os.environ.get("REPORT_EMAIL_TO", "").split(",")
                if addr.strip()
            ],
            timezone=ZoneInfo(os.environ.get("TIMEZONE", "Asia/Seoul")),
            db_path=os.environ.get("DB_PATH", "slack_error_stats.db"),
        )

    def require_smtp(self) -> None:
        """이메일을 실제로 발송하기 전에 SMTP 설정이 채워져 있는지 확인한다."""
        missing = [
            name
            for name, value in {
                "SMTP_HOST": self.smtp_host,
                "SMTP_USER": self.smtp_user,
                "SMTP_PASSWORD": self.smtp_password,
            }.items()
            if not value
        ]
        if not self.report_email_to:
            missing.append("REPORT_EMAIL_TO")
        if missing:
            raise RuntimeError(
                f"이메일 발송에 필요한 환경 변수가 없습니다: {', '.join(missing)}. "
                "--dry-run으로 먼저 확인하거나 .env에 값을 채워주세요."
            )
