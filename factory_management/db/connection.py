"""SQLite connection configuration. One connection per unit of work."""
from __future__ import annotations
import os
import sqlite3
from pathlib import Path

def default_database_path() -> str:
    """Return a stable database path; FACTORY_DB_PATH can override it."""
    override = os.environ.get("FACTORY_DB_PATH")
    if override:
        return str(Path(override).expanduser().resolve())
    project_root = Path(__file__).resolve().parents[2]
    return str(project_root / "data" / "factory_management_v4.db")

def get_connection(db_path: str | os.PathLike | None = None) -> sqlite3.Connection:
    path = Path(db_path or default_database_path()).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn
