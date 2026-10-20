"""Derived totals are recomputed from source records to avoid cumulative drift."""
from __future__ import annotations
import sqlite3

def refresh_schedule_totals(conn: sqlite3.Connection, schedule_id: int) -> None:
    conn.execute(
        """UPDATE daily_schedules
           SET actual_quantity = COALESCE((SELECT SUM(quantity) FROM production_records WHERE schedule_id=?), 0),
               qualified_quantity = COALESCE((SELECT SUM(qualified_quantity) FROM production_records WHERE schedule_id=?), 0),
               defective_quantity = COALESCE((SELECT SUM(defective_quantity) FROM production_records WHERE schedule_id=?), 0),
               repair_quantity = COALESCE((SELECT SUM(repair_quantity) FROM production_records WHERE schedule_id=?), 0)
           WHERE id=?""",
        (schedule_id, schedule_id, schedule_id, schedule_id, schedule_id)
    )

def refresh_order_total(conn: sqlite3.Connection, order_id: int) -> None:
    conn.execute(
        """UPDATE orders SET total_amount = COALESCE(
             (SELECT SUM(order_quantity * unit_price) FROM order_items WHERE order_id = ?), 0)
           WHERE id = ?""", (order_id, order_id)
    )
