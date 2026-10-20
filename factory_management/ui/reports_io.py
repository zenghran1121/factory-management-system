import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ReportsIOMixin:

    def create_statistics_tab(self):
        # 统计选项
        option_frame = ttk.LabelFrame(self.tab_statistics, text="统计选项")
        option_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        ttk.Label(option_frame, text="统计类型:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.stat_type_combobox = ttk.Combobox(option_frame, values=['订单统计', '生产统计', '库存统计', '结算统计'], state="readonly")
        self.stat_type_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.stat_type_combobox.current(0)

        ttk.Label(option_frame, text="统计月份:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.stat_month_entry = ttk.Entry(option_frame)
        self.stat_month_entry.insert(0, datetime.now().strftime("%Y-%m"))
        self.stat_month_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(option_frame, text="生成统计图表", command=self.generate_statistics).grid(row=2, column=0, columnspan=2, pady=10)

        # 图表区域（优化尺寸，适配滚动）
        chart_frame = ttk.LabelFrame(self.tab_statistics, text="统计图表")
        chart_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

        # 缩小图表默认尺寸，适配小窗口
        self.figure = plt.Figure(figsize=(8, 5), dpi=90)
        self.canvas = FigureCanvasTkAgg(self.figure, chart_frame)
        canvas_widget = self.canvas.get_tk_widget()
        canvas_widget.pack(fill='both', expand=True)
        
        # 图表鼠标滚轮缩放
        def on_mouse_wheel(event):
            scale = 1.1 if event.delta > 0 else 0.9
            canvas_widget.configure(width=int(canvas_widget.winfo_width()*scale), 
                                    height=int(canvas_widget.winfo_height()*scale))
        canvas_widget.bind("<MouseWheel>", on_mouse_wheel)

        # 数据表格（带独立滚动）
        table_frame = ttk.LabelFrame(self.tab_statistics, text="统计数据")
        table_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

        # 表格滚动容器
        table_canvas = tk.Canvas(table_frame)
        table_scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=table_canvas.yview)
        table_scroll_x = ttk.Scrollbar(table_frame, orient="horizontal", command=table_canvas.xview)
        table_scrollable_frame = ttk.Frame(table_canvas)

        table_scrollable_frame.bind(
            "<Configure>",
            lambda e: table_canvas.configure(scrollregion=table_canvas.bbox("all"))
        )

        table_canvas.create_window((0, 0), window=table_scrollable_frame, anchor="nw")
        table_canvas.configure(yscrollcommand=table_scroll_y.set, xscrollcommand=table_scroll_x.set)

        # 布局表格滚动
        table_canvas.grid(row=0, column=0, sticky="nsew")
        table_scroll_y.grid(row=0, column=1, sticky="ns")
        table_scroll_x.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # 统计表格
        self.stat_tree = ttk.Treeview(table_scrollable_frame)
        self.stat_tree.pack(fill='both', expand=True)


    def generate_statistics(self):
        stat_type = self.stat_type_combobox.get()
        stat_month = self.stat_month_entry.get().strip()

        try:
            datetime.strptime(stat_month, "%Y-%m")
        except ValueError:
            messagebox.showwarning("警告", "月份格式应为YYYY-MM！")
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        conn = None
        conn = self.connect_db()
        if stat_type == '订单统计':
            # 订单统计：按客户统计订单金额
            c = conn.cursor()
            c.execute('''SELECT c.customer_name, COALESCE(SUM(oi.order_quantity * oi.unit_price), 0) as total_amount
                         FROM customers c
                         LEFT JOIN orders o ON c.id = o.customer_id
                         LEFT JOIN order_items oi ON o.id = oi.order_id
                         WHERE o.order_date LIKE ?
                         GROUP BY c.customer_name
                         ORDER BY total_amount DESC''', (f"{stat_month}%",))
            data = c.fetchall()
            if data:
                customers = [row[0] for row in data]
                amounts = [row[1] for row in data]
                ax.bar(customers, amounts)
                ax.set_title(f'{stat_month} 订单金额统计')
                ax.set_xlabel('客户')
                ax.set_ylabel('订单金额')
                ax.tick_params(axis='x', rotation=45)
                # 更新表格
                self.update_stat_table(['客户', '订单金额'], data)
            else:
                ax.text(0.5, 0.5, '暂无数据', ha='center', va='center')
                self.update_stat_table([], [])
        elif stat_type == '生产统计':
            # 生产统计：按物料统计生产数量
            c = conn.cursor()
            c.execute('''SELECT m.material_name, COALESCE(SUM(pr.quantity), 0) as total_production
                         FROM materials m
                         LEFT JOIN production_plans pp ON m.id = pp.material_id
                         LEFT JOIN daily_schedules ds ON pp.id = ds.plan_id
                         LEFT JOIN production_records pr ON ds.id = pr.schedule_id
                         WHERE pr.production_date LIKE ?
                         GROUP BY m.material_name
                         ORDER BY total_production DESC''', (f"{stat_month}%",))
            data = c.fetchall()
            if data:
                materials = [row[0] for row in data]
                quantities = [row[1] for row in data]
                ax.bar(materials, quantities)
                ax.set_title(f'{stat_month} 生产数量统计')
                ax.set_xlabel('物料')
                ax.set_ylabel('生产数量')
                ax.tick_params(axis='x', rotation=45)
                self.update_stat_table(['物料', '生产数量'], data)
            else:
                ax.text(0.5, 0.5, '暂无数据', ha='center', va='center')
                self.update_stat_table([], [])
        elif stat_type == '库存统计':
            # 库存统计：按仓库统计库存总量
            c = conn.cursor()
            c.execute('''SELECT w.warehouse_name, COALESCE(SUM(i.quantity), 0) as total_quantity
                         FROM warehouses w
                         LEFT JOIN inventory i ON w.id = i.warehouse_id
                         GROUP BY w.warehouse_name
                         ORDER BY total_quantity DESC''')
            data = c.fetchall()
            if data:
                warehouses = [row[0] for row in data]
                quantities = [row[1] for row in data]
                ax.pie(quantities, labels=warehouses, autopct='%1.1f%%')
                ax.set_title(f'{stat_month} 库存分布统计')
                self.update_stat_table(['仓库', '库存总量'], data)
            else:
                ax.text(0.5, 0.5, '暂无数据', ha='center', va='center')
                self.update_stat_table([], [])
        elif stat_type == '结算统计':
            # 结算统计：按客户统计结算金额
            c = conn.cursor()
            c.execute('''SELECT c.customer_name, COALESCE(SUM(sr.settlement_amount), 0) as total_settlement
                         FROM customers c
                         LEFT JOIN orders o ON c.id = o.customer_id
                         LEFT JOIN settlement_records sr ON o.id = sr.order_id
                         WHERE sr.settlement_date LIKE ?
                         GROUP BY c.customer_name
                         ORDER BY total_settlement DESC''', (f"{stat_month}%",))
            data = c.fetchall()
            if data:
                customers = [row[0] for row in data]
                settlements = [row[1] for row in data]
                ax.bar(customers, settlements)
                ax.set_title(f'{stat_month} 结算金额统计')
                ax.set_xlabel('客户')
                ax.set_ylabel('结算金额')
                ax.tick_params(axis='x', rotation=45)
                self.update_stat_table(['客户', '结算金额'], data)
            else:
                ax.text(0.5, 0.5, '暂无数据', ha='center', va='center')
                self.update_stat_table([], [])

        conn.close()
        self.canvas.draw()


    def update_stat_table(self, columns, data):
        # 清空表格
        for item in self.stat_tree.get_children():
            self.stat_tree.delete(item)
        # 设置列
        self.stat_tree['columns'] = columns
        self.stat_tree['show'] = 'headings'
        for col in columns:
            self.stat_tree.heading(col, text=col)
        # 添加数据
        for row in data:
            self.stat_tree.insert('', 'end', values=row)


    def create_import_export_tab(self):
        # 导出区域
        export_frame = ttk.LabelFrame(self.tab_import_export, text="数据导出")
        export_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        ttk.Label(export_frame, text="导出数据类型:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.export_type_combobox = ttk.Combobox(export_frame, values=['物料数据', '客户数据', '订单数据', '库存数据', '生产数据'], state="readonly")
        self.export_type_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.export_type_combobox.current(0)

        ttk.Button(export_frame, text="导出到Excel", command=self.export_to_excel).grid(row=1, column=0, columnspan=2, pady=10)

        # 导入区域
        import_frame = ttk.LabelFrame(self.tab_import_export, text="数据导入")
        import_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

        ttk.Label(import_frame, text="导入数据类型:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.import_type_combobox = ttk.Combobox(import_frame, values=['物料数据', '客户数据', '订单数据'], state="readonly")
        self.import_type_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.import_type_combobox.current(0)

        ttk.Button(import_frame, text="从Excel导入", command=self.import_from_excel).grid(row=1, column=0, columnspan=2, pady=10)


    def export_to_excel(self):
        export_type = self.export_type_combobox.get()
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel文件", "*.xlsx")])
        if not file_path:
            return

        try:
            conn = None
            conn = self.connect_db()
            if export_type == '物料数据':
                df = pd.read_sql_query('''SELECT m.material_code, m.material_name, t.type_name as 物料类型,
                                                  COALESCE(p.material_name, '无') as 父级物料, m.unit, m.weight,
                                                  m.spec as 规格型号, m.material as 材质, m.size as 尺寸规格, m.description as 描述
                                           FROM materials m
                                           JOIN material_types t ON m.type_id = t.id
                                           LEFT JOIN materials p ON m.parent_id = p.id''', conn)
            elif export_type == '客户数据':
                df = pd.read_sql_query('SELECT customer_name as 客户名称, contact_info as 联系方式 FROM customers', conn)
            elif export_type == '订单数据':
                df = pd.read_sql_query('''SELECT o.id as 订单编号, c.customer_name as 客户名称, o.order_date as 订单日期,
                                                  o.delivery_date as 交货日期, o.order_type as 订单类型, o.status as 订单状态,
                                                  m.material_name as 产品名称, oi.order_quantity as 订单数量, oi.unit_price as 单价,
                                                  (oi.order_quantity * oi.unit_price) as 金额
                                           FROM orders o
                                           JOIN customers c ON o.customer_id = c.id
                                           LEFT JOIN order_items oi ON o.id = oi.order_id
                                           LEFT JOIN materials m ON oi.material_id = m.id''', conn)
            elif export_type == '库存数据':
                df = pd.read_sql_query('''SELECT m.material_name as 物料名称, w.warehouse_name as 仓库名称,
                                                  i.quantity as 库存数量, m.unit as 单位
                                           FROM inventory i
                                           JOIN materials m ON i.material_id = m.id
                                           JOIN warehouses w ON i.warehouse_id = w.id''', conn)
            elif export_type == '生产数据':
                df = pd.read_sql_query('''SELECT m.material_name as 物料名称, pr.production_date as 生产日期,
                                                  pr.quantity as 生产数量, pr.qualified_quantity as 合格品数量,
                                                  pr.defective_quantity as 次品数量, pr.repair_quantity as 待修品数量,
                                                  pr.operator as 操作人员
                                           FROM production_records pr
                                           JOIN daily_schedules ds ON pr.schedule_id = ds.id
                                           JOIN production_plans pp ON ds.plan_id = pp.id
                                           JOIN materials m ON pp.material_id = m.id''', conn)
            else:
                messagebox.showwarning("警告", "不支持的导出类型！")
                return

            df.to_excel(file_path, index=False)
            messagebox.showinfo("成功", f"{export_type}已成功导出到Excel文件！")
        except Exception as e:
            messagebox.showerror("错误", f"导出失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def import_from_excel(self):
        import_type = self.import_type_combobox.get()
        file_path = filedialog.askopenfilename(filetypes=[("Excel文件", "*.xlsx;*.xls")])
        if not file_path:
            return

        try:
            if import_type == '物料数据':
                self.import_materials_from_excel_custom(file_path)
            elif import_type == '客户数据':
                self.import_customers_from_excel_custom(file_path)
            elif import_type == '订单数据':
                self.import_orders_from_excel_custom(file_path)
            else:
                messagebox.showwarning("警告", "不支持的导入类型！")
                return
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：{str(e)}")


    def import_materials_from_excel_custom(self, file_path):
        self.import_materials_from_excel(file_path)


    def import_customers_from_excel_custom(self, file_path):
        self.import_customers_from_excel(file_path)


    def import_orders_from_excel_custom(self, file_path):
        self.import_orders_from_excel(file_path)

