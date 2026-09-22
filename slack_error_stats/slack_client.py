from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .storage import SlackMessage


class SlackHistoryClient:
    def __init__(self, token: str, channel_id: str):
        self._client = WebClient(token=token)
        self._channel_id = channel_id

    def fetch_new_messages(self, oldest_ts: str | None) -> list[SlackMessage]:
        """channel의 oldest_ts 이후 메시지를 시간순으로 전부 가져온다."""
        messages: list[SlackMessage] = []
        cursor: str | None = None

        while True:
            try:
                response = self._client.conversations_history(
                    channel=self._channel_id,
                    oldest=oldest_ts,
                    cursor=cursor,
                    limit=200,
                )
            except SlackApiError as exc:
                raise RuntimeError(f"Slack 메시지 조회 실패: {exc.response['error']}") from exc

            for raw in response.get("messages", []):
                # 봇 자신의 메시지나 채널 시스템 메시지(join/leave 등)는 제외
                if raw.get("subtype") in {
                    "channel_join",
                    "channel_leave",
                    "bot_message",
                }:
                    continue
                text = raw.get("text", "").strip()
                if not text:
                    continue
                messages.append(
                    SlackMessage(
                        ts=raw["ts"],
                        channel=self._channel_id,
                        user=raw.get("user"),
                        text=text,
                        permalink=self._safe_permalink(raw["ts"]),
                    )
                )

            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break

        messages.sort(key=lambda m: float(m.ts))
        return messages

    def _safe_permalink(self, ts: str) -> str | None:
        try:
            resp = self._client.chat_getPermalink(
                channel=self._channel_id, message_ts=ts
            )
            return resp.get("permalink")
        except SlackApiError:
            return None
