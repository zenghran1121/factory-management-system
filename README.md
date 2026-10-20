# 小型工厂生产经营管理系统

一个基于 **Python + Tkinter + SQLite + pandas + Matplotlib** 的桌面工厂管理项目。项目从原有单文件原型逐步整理为按职责划分的 Python 包，保留基础数据、订单、BOM 组件需求、月计划、日排程、生产记录、库存、采购需求、结算、统计及 Excel 导入导出等原有界面功能。

> **项目状态：个人作品集 / 学习型项目。** 已完成结构拆分和核心数据库服务测试，但尚未经过真实工厂全流程验收。不要直接用于唯一的生产数据库。

## 功能模块

- 基础数据：物料、组件关系、客户、仓库/车间
- 订单与订单明细
- 生产计划、日排程、生产记录
- 库存余额与库存变动流水
- 采购需求、结算记录、统计图表
- Excel 导入导出

## 技术栈

- Python 3.10+（建议 3.11+）
- Tkinter / ttk：桌面 UI
- SQLite：本地关系型数据库
- pandas / openpyxl：Excel 数据处理
- Matplotlib：统计可视化
- unittest：自动化测试

## 快速开始

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

运行测试：

```bash
python -m unittest discover -s tests -v
```

数据库默认创建在 `data/factory_management_v4.db`。可通过环境变量 `FACTORY_DB_PATH` 指定其他路径。首次运行会创建表并执行轻量兼容迁移。若要迁移旧数据，请先备份旧数据库，再将数据库文件复制到 `data/` 目录或设置 `FACTORY_DB_PATH` 指向旧库。

## 项目结构

```text
factory-management-system/
├── main.py                         # 启动入口
├── factory_management/
│   ├── app.py                      # 应用启动流程
│   ├── db/                         # SQLite 连接、schema、数据库 mixin
│   ├── repositories/               # SQL 数据访问函数
│   ├── services/                   # 业务服务与汇总计算
│   └── ui/                         # 按业务模块拆分的 Tkinter UI mixins
├── tests/                          # 自动化测试
├── docs/                           # 架构、学习与作品集文档
├── reference/                      # 原版和改进前单文件参考
├── data/                           # 本地数据库（不提交真实业务数据）
└── backups/                        # 备份目录
```

## 当前架构说明

- UI 按基础数据、订单、计划、生产、库存、采购结算、报表等领域拆分，减少单个 Python 文件的体积。
- SQLite 连接统一配置，默认启用外键和 busy timeout。
- 数据库 schema 初始化单独维护，并包含 `stocked` 字段兼容迁移、常用索引和基础数据初始化。
- 排程汇总、订单金额重算抽为 service 函数。
- 生产入库流程通过 service/repository 处理：库存余额、库存流水、生产记录过账状态在调用方同一事务中完成；重复过账会被拒绝。

**诚实的技术边界：** 这是渐进式重构，不是所有 SQL 已完全从 UI 中移除。现有多个历史 CRUD 回调仍直接执行 SQL，后续可按领域逐步迁移到 repository/service。自动采购需求仍因缺少完整原材料 BOM 关系而不能视为可靠的 MRP 计算；组件计划目前也不等于完整多级 BOM。发货单、退货/冲销、权限和完整数据库迁移框架尚未实现。

## 作品集描述参考

> 独立开发小型工厂生产经营管理桌面系统，使用 Python、Tkinter、SQLite、pandas 与 Matplotlib，实现基础资料、订单、BOM 组件需求、生产计划与排程、生产记录、库存流水、采购需求、结算及统计报表等模块。针对原型中的数据一致性问题，设计并实现生产入库事务流程、重复过账保护、订单金额与排程汇总重算、SQLite 外键与备份机制；将单文件代码按业务模块拆分，并为核心数据库服务编写自动化测试。

请按你实际完成和理解的部分调整这段描述；面试时尤其要能解释事务、重复入库保护、数据库关系和测试覆盖范围。

## 安全提示

- 不要把真实客户信息、订单、联系方式或数据库文件上传到公开仓库。
- 运行前备份原数据库。
- `.db` 文件和备份默认不纳入 Git。
