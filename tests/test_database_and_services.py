"""Isolated tests for schema, aggregation and production receipt posting."""
import tempfile
import unittest
from pathlib import Path
from factory_management.db.connection import get_connection
from factory_management.db.schema import initialize_database
from factory_management.services.aggregation_service import refresh_order_total, refresh_schedule_totals
from factory_management.services.production_service import post_production_receipt

class FactoryServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.tmp.name) / "test.db")
        self.conn_factory = lambda: get_connection(self.db_path)
        initialize_database(self.conn_factory)
        self.conn = self.conn_factory()

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def _make_material(self):
        type_id = self.conn.execute("SELECT id FROM material_types WHERE type_name='成品'").fetchone()[0]
        cur = self.conn.execute("INSERT INTO materials(material_code, material_name, type_id, unit) VALUES ('T-01','测试成品',?,'件')", (type_id,))
        return cur.lastrowid

    def _make_production_record(self, quantity=5, qualified=4):
        material_id = self._make_material()
        order_id = self.conn.execute("INSERT INTO orders(order_date) VALUES ('2026-01-01')").lastrowid
        plan_id = self.conn.execute("INSERT INTO production_plans(material_id, plan_month, planned_quantity, order_id) VALUES (?, '2026-01', 10, ?)", (material_id, order_id)).lastrowid
        warehouse_id = self.conn.execute("SELECT id FROM warehouses ORDER BY id LIMIT 1").fetchone()[0]
        schedule_id = self.conn.execute("INSERT INTO daily_schedules(plan_id, warehouse_id, schedule_date, planned_quantity) VALUES (?, ?, '2026-01-02', 10)", (plan_id, warehouse_id)).lastrowid
        record_id = self.conn.execute("INSERT INTO production_records(schedule_id, production_date, quantity, qualified_quantity, defective_quantity, repair_quantity) VALUES (?, '2026-01-02', ?, ?, ?, ?)", (schedule_id, quantity, qualified, quantity-qualified, 0)).lastrowid
        self.conn.commit()
        return record_id, schedule_id, material_id, warehouse_id, order_id

    def test_foreign_keys_enabled(self):
        self.assertEqual(self.conn.execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_order_total_recomputed(self):
        material_id = self._make_material()
        order_id = self.conn.execute("INSERT INTO orders(order_date) VALUES ('2026-01-01')").lastrowid
        self.conn.execute("INSERT INTO order_items(order_id, material_id, order_quantity, unit_price) VALUES (?, ?, 3, 12.5)", (order_id, material_id))
        refresh_order_total(self.conn, order_id)
        self.assertEqual(self.conn.execute("SELECT total_amount FROM orders WHERE id=?", (order_id,)).fetchone()[0], 37.5)

    def test_schedule_totals_recomputed_from_source_records(self):
        _, schedule_id, _, _, _ = self._make_production_record(5, 4)
        refresh_schedule_totals(self.conn, schedule_id)
        row = self.conn.execute("SELECT actual_quantity, qualified_quantity, defective_quantity, repair_quantity FROM daily_schedules WHERE id=?", (schedule_id,)).fetchone()
        self.assertEqual(tuple(row), (5, 4, 1, 0))

    def test_receipt_updates_inventory_and_ledger_once(self):
        record_id, _, material_id, warehouse_id, _ = self._make_production_record(5, 4)
        result = post_production_receipt(self.conn, record_id)
        self.conn.commit()
        self.assertEqual(result.quantity, 4)
        quantity = self.conn.execute("SELECT quantity FROM inventory WHERE material_id=? AND warehouse_id=?", (material_id, warehouse_id)).fetchone()[0]
        self.assertEqual(quantity, 4)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM inventory_changes WHERE related_production_id=?", (record_id,)).fetchone()[0], 1)
        with self.assertRaises(ValueError):
            post_production_receipt(self.conn, record_id)

    def test_failed_receipt_can_be_rolled_back(self):
        record_id, _, material_id, warehouse_id, _ = self._make_production_record(5, 4)
        post_production_receipt(self.conn, record_id)
        self.conn.rollback()
        self.assertIsNone(self.conn.execute("SELECT quantity FROM inventory WHERE material_id=? AND warehouse_id=?", (material_id, warehouse_id)).fetchone())
        stocked = self.conn.execute("SELECT stocked FROM production_records WHERE id=?", (record_id,)).fetchone()[0]
        self.assertEqual(stocked, 0)

    def test_database_integrity(self):
        self.assertEqual(self.conn.execute("PRAGMA integrity_check").fetchone()[0], "ok")

if __name__ == '__main__':
    unittest.main(verbosity=2)
