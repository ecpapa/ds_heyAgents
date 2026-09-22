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
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from: str
    report_email_to: list[str]
    timezone: ZoneInfo
    db_path: str

    @staticmethod
    def load() -> "Config":
        return Config(
            slack_bot_token=_require("SLACK_BOT_TOKEN"),
            slack_channel_id=_require("SLACK_CHANNEL_ID"),
            anthropic_api_key=_require("ANTHROPIC_API_KEY"),
            anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5"),
            smtp_host=_require("SMTP_HOST"),
            smtp_port=int(os.environ.get("SMTP_PORT", "587")),
            smtp_user=_require("SMTP_USER"),
            smtp_password=_require("SMTP_PASSWORD"),
            smtp_from=os.environ.get("SMTP_FROM") or os.environ["SMTP_USER"],
            report_email_to=[
                addr.strip()
                for addr in _require("REPORT_EMAIL_TO").split(",")
                if addr.strip()
            ],
            timezone=ZoneInfo(os.environ.get("TIMEZONE", "Asia/Seoul")),
            db_path=os.environ.get("DB_PATH", "slack_error_stats.db"),
        )
