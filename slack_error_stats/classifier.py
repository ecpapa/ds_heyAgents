import json

from anthropic import Anthropic

from .storage import Classification

_SYSTEM_PROMPT = """\
너는 Slack 모니터링 채널에 올라오는 메시지를 검토해서 '오류(장애/에러) 보고'인지 아닌지 \
판별하는 분류기다. 아래 JSON 스키마로만 응답하고, 다른 설명은 절대 붙이지 마라.

{
  "is_error": boolean,   // 이 메시지가 오류/장애/실패 보고이면 true
  "error_type": string,  // 오류 유형을 짧게 (예: "API 타임아웃", "배포 실패", "DB 연결 오류"). 오류가 아니면 ""
  "severity": string,    // "critical" | "high" | "medium" | "low" 중 하나. 오류가 아니면 ""
  "summary": string      // 오류 내용을 한국어 한 문장으로 요약. 오류가 아니면 ""
}
"""


class ErrorClassifier:
    def __init__(self, api_key: str, model: str):
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def classify(self, text: str) -> Classification:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=300,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text}],
        )
        raw = "".join(
            block.text for block in response.content if block.type == "text"
        ).strip()
        data = self._parse_json(raw)
        return Classification(
            is_error=bool(data.get("is_error", False)),
            error_type=str(data.get("error_type", "")),
            severity=str(data.get("severity", "")),
            summary=str(data.get("summary", "")),
        )

    @staticmethod
    def _parse_json(raw: str) -> dict:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # 모델이 코드블록(```json ... ```)으로 감싸서 응답한 경우 대비
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(raw[start : end + 1])
                except json.JSONDecodeError:
                    pass
            return {"is_error": False, "error_type": "", "severity": "", "summary": ""}
