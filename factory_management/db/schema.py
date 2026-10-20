"""Database schema initialization and lightweight compatibility migration."""
from __future__ import annotations
from collections.abc import Callable
import sqlite3

def initialize_database(connect_db: Callable[[], sqlite3.Connection]) -> None:
    """Create missing tables and apply compatibility updates atomically."""
    conn = connect_db()
    try:
        c = conn.cursor()

        # 1. 物料分类表 (区分成品/组件/原材料)
        c.execute('''CREATE TABLE IF NOT EXISTS material_types
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      type_name TEXT UNIQUE NOT NULL, -- 成品/组件/原材料
                      description TEXT)''')

        # 2. 产品/物料基础信息表 (支持层级关联)
        c.execute('''CREATE TABLE IF NOT EXISTS materials
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      material_code TEXT UNIQUE NOT NULL, -- 物料编码
                      material_name TEXT NOT NULL,        -- 物料名称
                      type_id INTEGER,                    -- 关联物料分类
                      parent_id INTEGER DEFAULT NULL,     -- 父级物料（组件所属的成品）
                      unit TEXT NOT NULL,                 -- 单位
                      weight REAL DEFAULT 0,              -- 重量
                      spec TEXT,                          -- 规格型号
                      material TEXT,                      -- 材质
                      size TEXT,                          -- 尺寸规格
                      description TEXT,
                      FOREIGN KEY (type_id) REFERENCES material_types (id),
                      FOREIGN KEY (parent_id) REFERENCES materials (id))''')

        # 3. 产品-组件关联表 (记录产品由哪些组件组成)
        c.execute('''CREATE TABLE IF NOT EXISTS product_components
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      product_id INTEGER,                 -- 成品ID
                      component_id INTEGER,               -- 组件ID
                      quantity INTEGER DEFAULT 1,         -- 每个成品需要的组件数量
                      FOREIGN KEY (product_id) REFERENCES materials (id),
                      FOREIGN KEY (component_id) REFERENCES materials (id),
                      UNIQUE(product_id, component_id))''')

        # 4. 客户表
        c.execute('''CREATE TABLE IF NOT EXISTS customers
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      customer_name TEXT UNIQUE NOT NULL,
                      contact_info TEXT)''')

        # 5. 仓库/车间表 (支持多仓库管理)
        c.execute('''CREATE TABLE IF NOT EXISTS warehouses
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      warehouse_name TEXT UNIQUE NOT NULL, -- 如：公司仓库、涂装车间、油箱车间
                      location TEXT)''')

        # 6. 订单表
        c.execute('''CREATE TABLE IF NOT EXISTS orders
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      customer_id INTEGER,
                      order_date TEXT,
                      delivery_date TEXT,
                      order_type TEXT DEFAULT '订单', -- 订单/备货
                      status TEXT DEFAULT '待生产', -- 待生产/生产中/已完成/已交货/部分交货
                      total_amount REAL DEFAULT 0,
                      remark TEXT,
                      FOREIGN KEY (customer_id) REFERENCES customers (id))''')

        # 7. 订单明细表
        c.execute('''CREATE TABLE IF NOT EXISTS order_items
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      order_id INTEGER,
                      material_id INTEGER,
                      order_quantity INTEGER,
                      prepared_quantity INTEGER DEFAULT 0, -- 备货数量
                      delivered_quantity INTEGER DEFAULT 0, -- 已交货数量
                      unit_price REAL DEFAULT 0,
                      FOREIGN KEY (order_id) REFERENCES orders (id),
                      FOREIGN KEY (material_id) REFERENCES materials (id))''')

        # 8. 库存表 (支持多仓库库存)
        c.execute('''CREATE TABLE IF NOT EXISTS inventory
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      material_id INTEGER,
                      warehouse_id INTEGER,
                      quantity INTEGER DEFAULT 0,
                      FOREIGN KEY (material_id) REFERENCES materials (id),
                      FOREIGN KEY (warehouse_id) REFERENCES warehouses (id),
                      UNIQUE(material_id, warehouse_id))''')

        # 9. 生产计划表 (支持成品和组件计划，关联订单)
        c.execute('''CREATE TABLE IF NOT EXISTS production_plans
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      material_id INTEGER,
                      plan_month TEXT, -- 格式：YYYY-MM
                      planned_quantity INTEGER DEFAULT 0,
                      order_id INTEGER DEFAULT NULL, -- 关联订单
                      status TEXT DEFAULT '计划中', -- 计划中/已排产/已完成
                      FOREIGN KEY (material_id) REFERENCES materials (id),
                      FOREIGN KEY (order_id) REFERENCES orders (id),
                      UNIQUE(material_id, plan_month, order_id))''')

        # 10. 生产排程表 (支持多车间排程)
        c.execute('''CREATE TABLE IF NOT EXISTS daily_schedules
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      plan_id INTEGER,
                      warehouse_id INTEGER, -- 生产车间
                      schedule_date TEXT, -- 格式：YYYY-MM-DD
                      planned_quantity INTEGER DEFAULT 0,
                      actual_quantity INTEGER DEFAULT 0, -- 当日实际完成数量
                      qualified_quantity INTEGER DEFAULT 0, -- 合格品数量
                      defective_quantity INTEGER DEFAULT 0, -- 次品数量
                      repair_quantity INTEGER DEFAULT 0, -- 待修品数量
                      FOREIGN KEY (plan_id) REFERENCES production_plans (id),
                      FOREIGN KEY (warehouse_id) REFERENCES warehouses (id),
                      UNIQUE(plan_id, schedule_date, warehouse_id))''')

        # 11. 生产记录表 (详细记录生产过程)
        c.execute('''CREATE TABLE IF NOT EXISTS production_records
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      schedule_id INTEGER,
                      production_date TEXT,
                      quantity INTEGER,
                      qualified_quantity INTEGER,
                      defective_quantity INTEGER,
                      repair_quantity INTEGER,
                      returned_quantity INTEGER DEFAULT 0, -- 退货数量
                      repaired_qualified INTEGER DEFAULT 0, -- 返修合格品数量
                      operator TEXT, -- 操作人员
                      remark TEXT,
                      FOREIGN KEY (schedule_id) REFERENCES daily_schedules (id))''')

        # 12. 采购需求表 (根据生产计划自动生成采购需求)
        c.execute('''CREATE TABLE IF NOT EXISTS purchase_requests
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      material_id INTEGER,
                      request_date TEXT,
                      required_quantity INTEGER,
                      planned_quantity INTEGER DEFAULT 0, -- 已计划采购数量
                      completed_quantity INTEGER DEFAULT 0, -- 已完成采购数量
                      status TEXT DEFAULT '待处理', -- 待处理/已采购/已入库
                      FOREIGN KEY (material_id) REFERENCES materials (id))''')

        # 13. 结算记录表
        c.execute('''CREATE TABLE IF NOT EXISTS settlement_records
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      order_id INTEGER,
                      settlement_date TEXT,
                      settlement_amount REAL,
                      paid_amount REAL DEFAULT 0,
                      invoice_number TEXT,
                      status TEXT DEFAULT '未结算', -- 未结算/部分结算/已结算
                      overdue_amount REAL DEFAULT 0, -- 逾期货款
                      remark TEXT,
                      FOREIGN KEY (order_id) REFERENCES orders (id))''')

        # 14. 库存变动记录表 (记录库存的每一次变动)
        c.execute('''CREATE TABLE IF NOT EXISTS inventory_changes
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      material_id INTEGER,
                      warehouse_id INTEGER,
                      change_type TEXT, -- 入库/出库/退库
                      quantity INTEGER,
                      change_date TEXT,
                      related_order_id INTEGER DEFAULT NULL,
                      related_production_id INTEGER DEFAULT NULL,
                      remark TEXT,
                      FOREIGN KEY (material_id) REFERENCES materials (id),
                      FOREIGN KEY (warehouse_id) REFERENCES warehouses (id),
                      FOREIGN KEY (related_order_id) REFERENCES orders (id),
                      FOREIGN KEY (related_production_id) REFERENCES production_records (id))''')

        # 轻量数据库迁移：为旧数据库补充生产记录入库标记。
        # CREATE TABLE IF NOT EXISTS 不会给既有表增加新列，因此需要检查表结构。
        c.execute("PRAGMA table_info(production_records)")
        production_columns = {row[1] for row in c.fetchall()}
        if 'stocked' not in production_columns:
            c.execute("ALTER TABLE production_records ADD COLUMN stocked INTEGER NOT NULL DEFAULT 0")
        # 兼容旧版本：已有生产入库流水的记录应标记为已过账，避免升级后再次入库。
        c.execute("""UPDATE production_records SET stocked=1
                     WHERE EXISTS (
                       SELECT 1 FROM inventory_changes ic
                       WHERE ic.related_production_id=production_records.id AND ic.change_type='入库'
                     )""")

        # 订单总额是明细金额的汇总，启动时同步一次，修复旧版本中长期为 0 的值。
        c.execute("""UPDATE orders SET total_amount = COALESCE((
                     SELECT SUM(order_quantity * unit_price) FROM order_items WHERE order_items.order_id=orders.id
                   ), 0)""")

        # 常用关联查询索引。索引应围绕真实查询条件添加，不建议无差别地给每列建索引。
        c.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_inventory_material_warehouse ON inventory(material_id, warehouse_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_production_records_schedule_id ON production_records(schedule_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_production_plans_month ON production_plans(plan_month)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_settlement_records_order_id ON settlement_records(order_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_inventory_changes_production ON inventory_changes(related_production_id)")

        # 初始化基础数据
        # 初始化物料分类
        c.execute("INSERT OR IGNORE INTO material_types (type_name) VALUES ('成品')")
        c.execute("INSERT OR IGNORE INTO material_types (type_name) VALUES ('组件')")
        c.execute("INSERT OR IGNORE INTO material_types (type_name) VALUES ('原材料')")
        # 初始化仓库
        c.execute("INSERT OR IGNORE INTO warehouses (warehouse_name) VALUES ('公司仓库')")
        c.execute("INSERT OR IGNORE INTO warehouses (warehouse_name) VALUES ('涂装车间')")
        c.execute("INSERT OR IGNORE INTO warehouses (warehouse_name) VALUES ('油箱车间')")

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
