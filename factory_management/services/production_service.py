"""Production workflows: business rules without Tkinter dependencies."""
from __future__ import annotations
from dataclasses import dataclass
from . import _service_marker  # package marker; intentionally no UI dependency
from ..repositories.production_repository import get_production_receipt_source, apply_inventory_receipt

@dataclass(frozen=True)
class ReceiptResult:
    material_id: int
    warehouse_id: int
    quantity: int

def post_production_receipt(conn, record_id: int) -> ReceiptResult:
    """Post a production record to inventory. Caller owns transaction/commit/rollback."""
    row = get_production_receipt_source(conn, record_id)
    if row is None:
        raise ValueError("未找到关联的物料或仓库信息")
    if row["stocked"]:
        raise ValueError("这条生产记录已经入库，系统未重复增加库存")
    quantity = int(row["qualified_quantity"] or 0)
    if quantity <= 0:
        raise ValueError("合格品数量为 0，无需执行入库操作")
    apply_inventory_receipt(conn, record_id=record_id, material_id=row["material_id"],
                             warehouse_id=row["warehouse_id"], quantity=quantity)
    return ReceiptResult(row["material_id"], row["warehouse_id"], quantity)
