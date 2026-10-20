# 学习指南：用这个项目学会分层与数据库

## 1. 先从哪里开始

1. `main.py`：程序从哪里启动。
2. `factory_management/app.py`：创建 Tkinter 根窗口并启动事件循环。
3. `factory_management/ui/main_window.py`：主窗口组合各业务 UI mixin。
4. `factory_management/db/connection.py`：统一连接配置和外键设置。
5. `factory_management/services/production_service.py`：生产入库业务规则。
6. `factory_management/repositories/production_repository.py`：具体 SQL。
7. `tests/test_database_and_services.py`：用自动化测试验证行为。

## 2. 四个常见概念

- **UI 层**：负责显示和用户交互。
- **Service 层**：负责业务规则，例如已入库记录不能再次入库。
- **Repository/DB 层**：负责 SQL、连接、事务和数据读写。
- **数据库**：真正保存数据的 SQLite 文件及其表、索引、约束。

这和客户端/服务器不是同一概念。客户端/服务器通常划分不同运行实体与通信边界；UI/service/DB 是同一应用内部的职责边界。一个桌面应用可以在一个进程中同时具有这几层。

## 3. 生产入库的核心流程

阅读 `ProductionMixin.update_inventory_from_production`，再进入 `post_production_receipt`，最后查看 `apply_inventory_receipt`。注意三个关键点：

1. `?` 参数占位符：把数据作为参数传给 SQL，而不是拼接 SQL 字符串。
2. `UPDATE ... WHERE stocked = 0`：通过条件更新保护状态转换，不能只靠 UI 按钮禁用来防重复。
3. `commit` / `rollback`：库存余额、流水和过账状态必须作为一个整体成功或失败。

## 4. 为什么要从源数据重算汇总

排程实际完成量是生产记录的汇总值。若每次编辑都直接 `actual_quantity += 新数量`，重复保存会让数字漂移。`refresh_schedule_totals` 重新执行 `SUM(...)`，以生产记录作为事实来源重建汇总。代价是查询稍多；在当前规模下，正确性通常更重要。

## 5. 怎样运行测试

```bash
python -m unittest discover -s tests -v
```

测试使用临时目录中的数据库，不会改动日常使用的数据库。尝试把重复入库测试中的 `assertRaises` 去掉，或故意删掉 repository 中的 `stocked=0` 条件，观察测试怎样捕捉错误。

## 6. 练习路线

- 初级：给订单日期增加格式校验，并为校验写测试。
- 初级：增加“库存记录不存在”的测试。
- 中级：把库存手工调整逻辑从 UI 移到 `inventory_service.py`。
- 中级：给采购单部分到货写一个事务型服务和测试。
- 进阶：设计原材料 BOM 与多级需求展开，处理循环 BOM、损耗率、现有可用库存、冻结库存和在途采购。

## 7. 重要边界

这个项目是渐进式重构。并非所有旧 SQL 已迁出 UI，也未实现完整的 MRP、发货/退货/冲销、权限或全面数据库版本迁移。学习时应把“已实现的功能”和“下一步设计任务”分开。
