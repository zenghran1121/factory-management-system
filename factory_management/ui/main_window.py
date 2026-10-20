"""Tkinter main window assembled from domain-specific UI mixins."""
from __future__ import annotations
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path
from ..db.connection import default_database_path
from ..db.mixin import DatabaseMixin
from .basic_data import BasicDataMixin
from .orders import OrdersMixin
from .planning import PlanningMixin
from .production import ProductionMixin
from .inventory import InventoryMixin
from .purchasing_settlement import PurchasingSettlementMixin
from .reports_io import ReportsIOMixin

# Cross-platform font fallback list; unavailable fonts are ignored by Matplotlib.
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'PingFang SC', 'Noto Sans CJK SC', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class FactoryManagementSystem(DatabaseMixin, BasicDataMixin, OrdersMixin, PlanningMixin, ProductionMixin, InventoryMixin, PurchasingSettlementMixin, ReportsIOMixin):

    def __init__(self, root):
        self.root = root
        self.db_path = os.environ.get("FACTORY_DB_PATH", default_database_path())
        self.root.title("小型工厂生产经营管理系统 V5.0（改进版）")
        self.root.geometry("1600x1000")

        # 初始化数据库
        self.init_db()

        # 创建GUI
        self.create_gui()


    def create_gui(self):
        # ========== 新增：整个窗口的外层滚动容器 ==========
        # 创建主画布（承载滚动内容）
        main_canvas = tk.Canvas(self.root)
        # 垂直滚动条
        scroll_y = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        # 水平滚动条
        scroll_x = ttk.Scrollbar(self.root, orient="horizontal", command=main_canvas.xview)
        # 滚动内容的容器
        scrollable_frame = ttk.Frame(main_canvas)

        # 绑定滚动区域更新（内容变化时自动调整滚动范围）
        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        )

        # 将滚动容器放到画布中
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        # 关联滚动条和画布
        main_canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        # 布局外层滚动容器（占满整个窗口）
        main_canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")

        # ========== 原有 Notebook 放到滚动容器内 ==========
        self.notebook = ttk.Notebook(scrollable_frame)
        self.notebook.pack(fill='both', expand=True)

        # ========== 创建各个标签页（原有代码不变，只是缩进保持一致） ==========
        # 基础数据管理
        self.tab_basic = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_basic, text='基础数据管理')
        self.create_basic_data_tab()

        # 订单管理
        self.tab_orders = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_orders, text='订单管理')
        self.create_orders_tab()

        # 生产计划管理
        self.tab_planning = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_planning, text='生产计划管理')
        self.create_planning_tab()

        # 生产执行
        self.tab_production = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_production, text='生产执行')
        self.create_production_tab()

        # 库存管理
        self.tab_inventory = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_inventory, text='库存管理')
        self.create_inventory_tab()

        # 采购管理
        self.tab_purchase = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_purchase, text='采购管理')
        self.create_purchase_tab()

        # 结算管理
        self.tab_settlement = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_settlement, text='结算管理')
        self.create_settlement_tab()

        # 数据统计
        self.tab_statistics = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_statistics, text='数据统计')
        self.create_statistics_tab()

        # 数据导入导出
        self.tab_import_export = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_import_export, text='数据导入导出')
        self.create_import_export_tab()

        # ========== 全局鼠标滚轮支持 ==========
        def on_main_scroll(event):
            main_canvas.yview_scroll(-int(event.delta/120), "units")
        self.root.bind("<MouseWheel>", on_main_scroll)

