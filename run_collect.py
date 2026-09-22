"""Slack 모니터링 채널의 새 메시지를 가져와 오류 여부를 분류하고 DB에 저장한다.

cron 등으로 주기적으로 실행한다 (예: 5분마다).
    */5 * * * * cd /path/to/repo && .venv/bin/python run_collect.py
"""

from slack_error_stats.classifier import ErrorClassifier
from slack_error_stats.config import Config
from slack_error_stats.slack_client import SlackHistoryClient
from slack_error_stats.storage import Storage

_LAST_TS_KEY = "last_processed_ts"


def main() -> None:
    config = Config.load()
    storage = Storage(config.db_path)
    slack = SlackHistoryClient(config.slack_bot_token, config.slack_channel_id)
    classifier = ErrorClassifier(config.anthropic_api_key, config.anthropic_model)

    try:
        oldest_ts = storage.get_state(_LAST_TS_KEY)
        messages = slack.fetch_new_messages(oldest_ts)
        print(f"[run_collect] 새 메시지 {len(messages)}건 조회됨")

        classified = 0
        for message in messages:
            if storage.message_exists(message.ts):
                continue
            classification = classifier.classify(message.text)
            storage.save_classified_message(message, classification)
            classified += 1
            if classification.is_error:
                print(f"  - [오류] {message.ts} ({classification.severity}) {classification.summary}")

        if messages:
            storage.set_state(_LAST_TS_KEY, messages[-1].ts)

        print(f"[run_collect] 분류 완료: {classified}건")
    finally:
        storage.close()


if __name__ == "__main__":
    main()
