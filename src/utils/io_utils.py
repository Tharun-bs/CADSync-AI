from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import DB_PATH


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def init_db() -> None:
    ensure_dir(DB_PATH.parent)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_id TEXT NOT NULL,
                revision TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                valid INTEGER NOT NULL,
                anomaly_score REAL NOT NULL,
                manufacturability_risk INTEGER NOT NULL,
                estimated_cost REAL NOT NULL,
                output_dir TEXT NOT NULL
            )
            """
        )


def log_run(
    part_id: str,
    revision: str,
    valid: bool,
    anomaly_score: float,
    manufacturability_risk: int,
    estimated_cost: float,
    output_dir: Path,
) -> None:
    init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO runs (
                part_id, revision, timestamp, valid,
                anomaly_score, manufacturability_risk,
                estimated_cost, output_dir
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                part_id,
                revision,
                datetime.now(UTC).isoformat(),
                int(valid),
                anomaly_score,
                manufacturability_risk,
                estimated_cost,
                str(output_dir),
            ),
        )
