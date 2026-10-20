"""Database methods used by the Tkinter application."""
from __future__ import annotations
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from .connection import default_database_path, get_connection
from .schema import initialize_database
from ..services.aggregation_service import refresh_order_total, refresh_schedule_totals

class DatabaseMixin:
    def connect_db(self):
        """Open a configured SQLite connection with foreign keys enabled."""
        return get_connection(getattr(self, "db_path", None) or default_database_path())

    def backup_database(self, backup_dir=None):
        """Create a consistent SQLite backup using SQLite's backup API."""
        db_path = Path(getattr(self, "db_path", None) or default_database_path())
        backup_dir = Path(backup_dir) if backup_dir else db_path.parent / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"factory_management_{stamp}.db"
        source = self.connect_db()
        target = None
        try:
            target = sqlite3.connect(str(backup_path))
            source.backup(target)
            target.commit()
        except Exception:
            if target is not None:
                target.close()
            try:
                backup_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        finally:
            source.close()
            if target is not None:
                target.close()
        return str(backup_path)

    def init_db(self):
        initialize_database(self.connect_db)

    def _refresh_schedule_totals(self, conn, schedule_id):
        refresh_schedule_totals(conn, schedule_id)

    def _refresh_order_total(self, conn, order_id):
        refresh_order_total(conn, order_id)
