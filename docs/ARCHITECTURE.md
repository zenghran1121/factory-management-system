# 架构说明

## 分层

- **UI (`factory_management/ui/`)**：Tkinter 控件、表单验证、用户提示和刷新列表。为保留原型功能，各业务界面按 mixin 文件拆分。
- **Service (`factory_management/services/`)**：业务规则和跨表操作。例如 `post_production_receipt` 负责判断生产记录能否入库，并协调库存与流水更新。
- **Repository (`factory_management/repositories/`)**：封装具体 SQL 查询与写入。当前主要用于生产入库核心路径；其余旧 CRUD 会逐步迁移。
- **DB (`factory_management/db/`)**：连接配置、外键设置、schema 初始化和兼容迁移。
- **Database file**：SQLite 实际保存的表、索引和记录，与 DB 层 Python 代码不同。

## 生产入库调用链

```text
用户点击入库
    ↓
ProductionMixin.update_inventory_from_production (UI adapter)
    ↓
production_service.post_production_receipt (业务规则)
    ↓
production_repository (SQL 查询/写入)
    ↓
SQLite transaction: inventory + inventory_changes + stocked
    ↓
commit 成功 / rollback 失败
    ↓
UI 刷新库存与生产记录列表
```

## 为什么需要事务

库存余额、库存流水和生产记录的 `stocked` 状态表达的是同一个业务事件。如果只成功更新其中一部分，数据就会互相矛盾。调用方在同一连接中执行这些语句，全部成功才 `commit()`，异常时 `rollback()`。

## 当前限制与下一步

1. 将订单 CRUD SQL 迁移到 `order_repository` / `order_service`。
2. 将库存手工调整、采购和结算操作迁移为事务型 service。
3. 引入 `PRAGMA user_version` 和可重复执行的版本迁移脚本。
4. 为生产记录更正实现冲销/调整单，不直接修改已过账记录。
5. 完成原材料 BOM、发货单与结算闭环。
