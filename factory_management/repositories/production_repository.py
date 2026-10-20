"""SQL access for production and inventory posting."""
from __future__ import annotations
from datetime import datetime

def get_production_receipt_source(conn, record_id):
    return conn.execute(
        """SELECT m.id AS material_id, w.id AS warehouse_id, pr.qualified_quantity, pr.stocked
           FROM production_records pr
           JOIN daily_schedules ds ON pr.schedule_id = ds.id
           JOIN production_plans pp ON ds.plan_id = pp.id
           JOIN materials m ON pp.material_id = m.id
           JOIN warehouses w ON ds.warehouse_id = w.id
           WHERE pr.id = ?""", (record_id,)
    ).fetchone()

def apply_inventory_receipt(conn, *, record_id, material_id, warehouse_id, quantity, change_date=None):
    """Apply stock balance, movement ledger, and posted flag in caller's transaction."""
    if quantity <= 0:
        raise ValueError("入库数量必须大于 0")
    # Idempotency guard is enforced by the conditional state transition below.
    cursor = conn.execute(
        """UPDATE production_records SET stocked = 1 WHERE id = ? AND stocked = 0""",
        (record_id,)
    )
    if cursor.rowcount != 1:
        raise ValueError("生产记录不存在或已经入库")
    conn.execute(
        """INSERT INTO inventory(material_id, warehouse_id, quantity) VALUES (?, ?, ?)
           ON CONFLICT(material_id, warehouse_id) DO UPDATE
           SET quantity = inventory.quantity + excluded.quantity""",
        (material_id, warehouse_id, quantity)
    )
    conn.execute(
        """INSERT INTO inventory_changes
           (material_id, warehouse_id, change_type, quantity, change_date, related_production_id, remark)
           VALUES (?, ?, '入库', ?, ?, ?, ?)""",
        (material_id, warehouse_id, quantity, change_date or datetime.now().strftime("%Y-%m-%d"),
         record_id, "生产合格品入库")
    )
