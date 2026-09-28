from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

from .models import DrawRecord, Game, ValidationStatus


SCHEMA = """
CREATE TABLE IF NOT EXISTS raw_sources (
    source_hash TEXT PRIMARY KEY,
    source_url TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    content BLOB NOT NULL
);

CREATE TABLE IF NOT EXISTS draws (
    game TEXT NOT NULL,
    draw_date TEXT NOT NULL,
    draw_id TEXT NOT NULL,
    main_numbers TEXT NOT NULL,
    bonus_or_powerball INTEGER,
    source_url TEXT NOT NULL,
    source_retrieved_at TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    PRIMARY KEY (game, draw_id),
    FOREIGN KEY (source_hash) REFERENCES raw_sources(source_hash)
);

CREATE TABLE IF NOT EXISTS quarantined_draws (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game TEXT NOT NULL,
    draw_id TEXT NOT NULL,
    payload TEXT NOT NULL,
    errors TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    quarantined_at TEXT NOT NULL
);
"""


class Store:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA)
        return conn

    def save_raw(
        self, source_hash: str, source_url: str, retrieved_at: str, content: bytes
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO raw_sources
                (source_hash, source_url, retrieved_at, content)
                VALUES (?, ?, ?, ?)
                """,
                (source_hash, source_url, retrieved_at, content),
            )

    def raw_matches_hash(self, source_hash: str) -> bool:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT content FROM raw_sources WHERE source_hash = ?",
                (source_hash,),
            ).fetchone()
        return row is not None and hashlib.sha256(row[0]).hexdigest() == source_hash

    def insert_draw(self, record: DrawRecord) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO draws (
                    game, draw_date, draw_id, main_numbers,
                    bonus_or_powerball, source_url, source_retrieved_at,
                    source_hash, rule_version, validation_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                record.as_db_tuple(),
            )

    def quarantine(
        self,
        game: str,
        draw_id: str,
        payload: str,
        errors: str,
        source_hash: str,
        quarantined_at: str,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO quarantined_draws
                (game, draw_id, payload, errors, source_hash, quarantined_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (game, draw_id, payload, errors, source_hash, quarantined_at),
            )

    def iter_draws(self, game: str) -> list[DrawRecord]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT game, draw_date, draw_id, main_numbers,
                       bonus_or_powerball, source_url, source_retrieved_at,
                       source_hash, rule_version, validation_status
                FROM draws
                WHERE game = ?
                ORDER BY draw_date, draw_id
                """,
                (game,),
            ).fetchall()

        return [
            DrawRecord(
                game=Game(row[0]),
                draw_date=__import__("datetime").date.fromisoformat(row[1]),
                draw_id=row[2],
                main_numbers=[int(x) for x in row[3].split(",") if x],
                bonus_or_powerball=row[4],
                source_url=row[5],
                source_retrieved_at=__import__("datetime").datetime.fromisoformat(row[6]),
                source_hash=row[7],
                rule_version=row[8],
                validation_status=ValidationStatus(row[9]),
            )
            for row in rows
        ]
