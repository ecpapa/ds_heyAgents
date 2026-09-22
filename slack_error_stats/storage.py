import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime


SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    ts TEXT PRIMARY KEY,
    channel TEXT NOT NULL,
    user TEXT,
    text TEXT NOT NULL,
    permalink TEXT,
    is_error INTEGER,
    error_type TEXT,
    severity TEXT,
    summary TEXT,
    classified_at TEXT
);

CREATE TABLE IF NOT EXISTS state (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


@dataclass
class SlackMessage:
    ts: str
    channel: str
    user: str | None
    text: str
    permalink: str | None


@dataclass
class Classification:
    is_error: bool
    error_type: str
    severity: str
    summary: str


class Storage:
    def __init__(self, db_path: str):
        self._conn = sqlite3.connect(db_path)
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    @contextmanager
    def _cursor(self):
        cur = self._conn.cursor()
        try:
            yield cur
            self._conn.commit()
        finally:
            cur.close()

    def get_state(self, key: str) -> str | None:
        row = self._conn.execute(
            "SELECT value FROM state WHERE key = ?", (key,)
        ).fetchone()
        return row[0] if row else None

    def set_state(self, key: str, value: str) -> None:
        with self._cursor() as cur:
            cur.execute(
                "INSERT INTO state (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )

    def message_exists(self, ts: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM messages WHERE ts = ?", (ts,)
        ).fetchone()
        return row is not None

    def save_classified_message(
        self, message: SlackMessage, classification: Classification
    ) -> None:
        with self._cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages
                    (ts, channel, user, text, permalink,
                     is_error, error_type, severity, summary, classified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ts) DO UPDATE SET
                    is_error = excluded.is_error,
                    error_type = excluded.error_type,
                    severity = excluded.severity,
                    summary = excluded.summary,
                    classified_at = excluded.classified_at
                """,
                (
                    message.ts,
                    message.channel,
                    message.user,
                    message.text,
                    message.permalink,
                    int(classification.is_error),
                    classification.error_type,
                    classification.severity,
                    classification.summary,
                    datetime.utcnow().isoformat(),
                ),
            )

    def fetch_errors_between(
        self, start_ts: float, end_ts: float
    ) -> list[dict]:
        rows = self._conn.execute(
            """
            SELECT ts, user, text, permalink, error_type, severity, summary
            FROM messages
            WHERE is_error = 1 AND CAST(ts AS REAL) >= ? AND CAST(ts AS REAL) < ?
            ORDER BY CAST(ts AS REAL) ASC
            """,
            (start_ts, end_ts),
        ).fetchall()
        columns = [
            "ts",
            "user",
            "text",
            "permalink",
            "error_type",
            "severity",
            "summary",
        ]
        return [dict(zip(columns, row)) for row in rows]
