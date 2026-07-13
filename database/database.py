import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "forenvision.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_number TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            status TEXT NOT NULL,
            summary TEXT,
            evidence_path TEXT,
            fingerprint_score REAL,
            sketch_profile TEXT,
            report_path TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_case(case_data: Dict[str, Any]) -> int:
    init_db()
    conn = get_connection()
    case_number = case_data.get("case_number") or f"FV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    title = case_data.get("title", "Unnamed case")
    category = case_data.get("category", "General")
    status = case_data.get("status", "Active")
    summary = case_data.get("summary", "")
    evidence_path = case_data.get("evidence_path")
    fingerprint_score = case_data.get("fingerprint_score")
    sketch_profile = case_data.get("sketch_profile")
    report_path = case_data.get("report_path")
    created_at = case_data.get("created_at") or datetime.utcnow().isoformat()

    cursor = conn.execute(
        """
        INSERT INTO cases (
            case_number, title, category, status, summary, evidence_path,
            fingerprint_score, sketch_profile, report_path, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            case_number,
            title,
            category,
            status,
            summary,
            evidence_path,
            fingerprint_score,
            json.dumps(sketch_profile) if sketch_profile else None,
            report_path,
            created_at,
        ),
    )
    conn.commit()
    case_id = cursor.lastrowid
    conn.close()
    return case_id


def get_cases(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    init_db()
    conn = get_connection()
    query = "SELECT * FROM cases ORDER BY created_at DESC"
    if limit:
        query += f" LIMIT {limit}"
    rows = conn.execute(query).fetchall()
    conn.close()
    return [row_to_dict(row) for row in rows]


def get_case(case_id: int) -> Optional[Dict[str, Any]]:
    init_db()
    conn = get_connection()
    row = conn.execute("SELECT * FROM cases WHERE id = ?", (case_id,)).fetchone()
    conn.close()
    return row_to_dict(row) if row else None


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    data = dict(row)
    if data.get("sketch_profile"):
        try:
            data["sketch_profile"] = json.loads(data["sketch_profile"])
        except json.JSONDecodeError:
            data["sketch_profile"] = {}
    return data
