# yjyjparkStudy
start git 2022
test1

## Slack 오류 통계 에이전트 (slack_error_stats)

Slack 모니터링 채널에 올라오는 메시지를 주기적으로 조회해서, Claude(Anthropic API)로
"오류/장애 보고"인지 분류하고 SQLite에 누적한 뒤, 일간/주간 통계를 이메일로 보내주는 도구입니다.

### 동작 방식

1. `run_collect.py` — Slack `conversations.history` API로 채널의 새 메시지를 가져와
   Claude로 오류 여부/유형/심각도를 분류하고 DB(`slack_error_stats.db`)에 저장합니다.
   마지막으로 처리한 메시지의 timestamp를 기억해서 중복 처리하지 않습니다.
2. `send_report.py` — 지정한 기간(일간/주간)의 오류 통계(유형별/심각도별/보고자별 건수,
   상세 목록)를 집계해서 HTML 이메일로 발송합니다.

두 스크립트는 서로 독립적이며 각각 cron 등으로 원하는 주기에 맞게 실행하면 됩니다.

### 설정

```bash
pip install -r requirements.txt
cp .env.example .env
# .env 파일을 열어 아래 값을 채워넣으세요
```

- `SLACK_BOT_TOKEN`: Slack App의 Bot Token (`xoxb-...`).
  App 생성 시 `channels:history`, `channels:read` (비공개 채널이면 `groups:history`,
  `groups:read`) 스코프를 추가하고, 모니터링할 채널에 봇을 초대해야 합니다.
- `SLACK_CHANNEL_ID`: 모니터링할 채널 ID (채널 정보에서 확인 가능).
- `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`: 오류 분류에 사용할 Claude API 키/모델.
- `SMTP_*`, `REPORT_EMAIL_TO`: 리포트 발송용 SMTP 계정 및 수신자(콤마로 여러 명 가능).
- `TIMEZONE`: 통계 기간 계산 기준 시간대 (기본 `Asia/Seoul`).

### 실행

```bash
# 새 메시지 수집 + 분류 (주기적으로, 예: 5분마다)
python run_collect.py

# 전날 통계 이메일 발송 (매일 아침에)
python send_report.py --period daily

# 지난주 통계 이메일 발송 (매주 월요일 아침에)
python send_report.py --period weekly

# 실제 발송 없이 리포트 내용만 확인
python send_report.py --period daily --dry-run
```

### cron 예시

```
*/5 * * * * cd /path/to/repo && .venv/bin/python run_collect.py >> collect.log 2>&1
0 9 * * *   cd /path/to/repo && .venv/bin/python send_report.py --period daily >> report.log 2>&1
0 9 * * 1   cd /path/to/repo && .venv/bin/python send_report.py --period weekly >> report.log 2>&1
```

### 테스트

```bash
python -m pytest tests/ -q
```
