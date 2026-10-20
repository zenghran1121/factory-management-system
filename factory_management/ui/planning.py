import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class PlanningMixin:

    def create_planning_tab(self):
        # 月度计划区域
        plan_frame = ttk.LabelFrame(self.tab_planning, text="月度生产计划")
        plan_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        ttk.Label(plan_frame, text="产品/组件:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.plan_material_combobox = ttk.Combobox(plan_frame, state="readonly")
        self.plan_material_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.load_materials_for_combobox()

        ttk.Label(plan_frame, text="计划月份:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.plan_month_entry = ttk.Entry(plan_frame)
        self.plan_month_entry.insert(0, datetime.now().strftime("%Y-%m"))
        self.plan_month_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(plan_frame, text="计划数量:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.plan_quantity_entry = ttk.Entry(plan_frame)
        self.plan_quantity_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(plan_frame, text="关联订单:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.plan_order_combobox = ttk.Combobox(plan_frame, state="readonly")
        self.plan_order_combobox.grid(row=3, column=1, padx=5, pady=5)
        self.load_orders_for_combobox()

        ttk.Label(plan_frame, text="计划状态:").grid(row=4, column=0, padx=5, pady=5, sticky='w')
        self.plan_status_combobox = ttk.Combobox(plan_frame, values=['计划中', '已排产', '已完成'], state="readonly")
        self.plan_status_combobox.grid(row=4, column=1, padx=5, pady=5)
        self.plan_status_combobox.current(0)

        btn_frame = ttk.Frame(plan_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="保存月度计划", command=self.save_monthly_plan).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="自动生成组件计划", command=self.generate_component_plans).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_plan_form).grid(row=0, column=2, padx=5)

        # 月度计划列表
        plan_list_frame = ttk.LabelFrame(self.tab_planning, text="月度计划列表")
        plan_list_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

        self.plan_tree = ttk.Treeview(plan_list_frame, columns=('ID', '物料', '月份', '计划数量', '关联订单', '状态'), show='headings')
        self.plan_tree.heading('ID', text='ID')
        self.plan_tree.heading('物料', text='物料名称')
        self.plan_tree.heading('月份', text='计划月份')
        self.plan_tree.heading('计划数量', text='计划数量')
        self.plan_tree.heading('关联订单', text='关联订单')
        self.plan_tree.heading('状态', text='计划状态')
        self.plan_tree.column('ID', width=50)
        self.plan_tree.column('物料', width=150)
        self.plan_tree.column('月份', width=100)
        self.plan_tree.column('计划数量', width=100)
        self.plan_tree.column('关联订单', width=100)
        self.plan_tree.column('状态', width=100)
        self.plan_tree.bind('<<TreeviewSelect>>', self.on_plan_select)
        self.plan_tree.pack(side='left', fill='both', expand=True)

        scrollbar1 = ttk.Scrollbar(plan_list_frame, orient='vertical', command=self.plan_tree.yview)
        scrollbar1.pack(side='right', fill='y')
        self.plan_tree.configure(yscrollcommand=scrollbar1.set)

        # 日度排程区域
        schedule_frame = ttk.LabelFrame(self.tab_planning, text="日度生产排程")
        schedule_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')

        ttk.Label(schedule_frame, text="生产车间:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.schedule_warehouse_combobox = ttk.Combobox(schedule_frame, state="readonly")
        self.schedule_warehouse_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.load_warehouses_for_schedule_combobox()

        ttk.Label(schedule_frame, text="排程日期:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.schedule_date_entry = ttk.Entry(schedule_frame)
        self.schedule_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.schedule_date_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(schedule_frame, text="排程数量:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.schedule_quantity_entry = ttk.Entry(schedule_frame)
        self.schedule_quantity_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(schedule_frame, text="添加排程", command=self.add_daily_schedule).grid(row=3, column=0, columnspan=2, pady=10)

        # 日度排程列表
        schedule_list_frame = ttk.LabelFrame(self.tab_planning, text="日度排程列表")
        schedule_list_frame.grid(row=1, column=1, padx=10, pady=10, sticky='nsew')

        self.schedule_tree = ttk.Treeview(schedule_list_frame, columns=('ID', '物料', '月份', '车间', '日期', '计划数量', '实际完成', '合格品', '次品', '待修品'), show='headings')
        self.schedule_tree.heading('ID', text='ID')
        self.schedule_tree.heading('物料', text='物料名称')
        self.schedule_tree.heading('月份', text='计划月份')
        self.schedule_tree.heading('车间', text='生产车间')
        self.schedule_tree.heading('日期', text='排程日期')
        self.schedule_tree.heading('计划数量', text='计划数量')
        self.schedule_tree.heading('实际完成', text='实际完成数量')
        self.schedule_tree.heading('合格品', text='合格品数量')
        self.schedule_tree.heading('次品', text='次品数量')
        self.schedule_tree.heading('待修品', text='待修品数量')
        self.schedule_tree.column('ID', width=50)
        self.schedule_tree.column('物料', width=120)
        self.schedule_tree.column('月份', width=80)
        self.schedule_tree.column('车间', width=100)
        self.schedule_tree.column('日期', width=100)
        self.schedule_tree.column('计划数量', width=100)
        self.schedule_tree.column('实际完成', width=100)
        self.schedule_tree.column('合格品', width=80)
        self.schedule_tree.column('次品', width=80)
        self.schedule_tree.column('待修品', width=80)
        self.schedule_tree.pack(side='left', fill='both', expand=True)

        scrollbar2 = ttk.Scrollbar(schedule_list_frame, orient='vertical', command=self.schedule_tree.yview)
        scrollbar2.pack(side='right', fill='y')
        self.schedule_tree.configure(yscrollcommand=scrollbar2.set)

        self.current_plan_id = None
        self.load_monthly_plans()


    def load_materials_for_combobox(self):
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute("SELECT id, material_name FROM materials ORDER BY material_name")
        materials = c.fetchall()
        self.materials_combobox_dict = {name: id for id, name in materials}
        self.plan_material_combobox['values'] = list(self.materials_combobox_dict.keys())
        conn.close()


    def load_orders_for_combobox(self):
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute("SELECT id, '订单' || id as order_label FROM orders ORDER BY id DESC")
        orders = c.fetchall()
        self.orders_combobox_dict = {label: id for id, label in orders}
        self.plan_order_combobox['values'] = ['无'] + list(self.orders_combobox_dict.keys())
        self.plan_order_combobox.current(0)
        conn.close()


    def load_warehouses_for_schedule_combobox(self):
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute("SELECT id, warehouse_name FROM warehouses ORDER BY warehouse_name")
        warehouses = c.fetchall()
        self.warehouses_combobox_dict = {name: id for id, name in warehouses}
        self.schedule_warehouse_combobox['values'] = list(self.warehouses_combobox_dict.keys())
        if warehouses:
            self.schedule_warehouse_combobox.current(0)
        conn.close()


    def save_monthly_plan(self):
        material_name = self.plan_material_combobox.get()
        plan_month = self.plan_month_entry.get().strip()
        quantity_text = self.plan_quantity_entry.get().strip()
        order_label = self.plan_order_combobox.get()
        status = self.plan_status_combobox.get()

        if not material_name or not plan_month or not quantity_text:
            messagebox.showwarning("警告", "产品/组件、计划月份和计划数量不能为空！")
            return

        try:
            # 验证月份格式
            datetime.strptime(plan_month, "%Y-%m")
            quantity = int(quantity_text)
            if quantity < 0:
                raise ValueError
        except (ValueError, TypeError):
            messagebox.showwarning("警告", "月份格式应为YYYY-MM，数量必须是非负整数！")
            return

        material_id = self.materials_combobox_dict[material_name]
        order_id = self.orders_combobox_dict.get(order_label) if order_label != '无' else None

        try:
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            # 检查是否已存在
            c.execute("SELECT id FROM production_plans WHERE material_id=? AND plan_month=? AND order_id=?", (material_id, plan_month, order_id))
            existing_id = c.fetchone()
            if existing_id:
                # 更新
                c.execute('''UPDATE production_plans SET planned_quantity=?, status=?
                             WHERE id=?''',
                          (quantity, status, existing_id[0]))
                self.current_plan_id = existing_id[0]
                messagebox.showinfo("成功", "月度计划更新成功！")
            else:
                # 新增
                c.execute('''INSERT INTO production_plans (material_id, plan_month, planned_quantity, order_id, status)
                             VALUES (?, ?, ?, ?, ?)''',
                          (material_id, plan_month, quantity, order_id, status))
                self.current_plan_id = c.lastrowid
                messagebox.showinfo("成功", "月度计划保存成功！")
            conn.commit()
            self.load_monthly_plans()
        except Exception as e:
            messagebox.showerror("错误", f"保存月度计划失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def generate_component_plans(self):
        """按 BOM 用量生成直接下一级组件计划（当前版本仍非递归多级展开）。"""
        if not self.current_plan_id:
            messagebox.showwarning("警告", "请先选择一个成品计划！")
            return

        conn = None
        try:
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            c.execute("SELECT material_id, planned_quantity, plan_month, order_id FROM production_plans WHERE id=?",
                      (self.current_plan_id,))
            plan = c.fetchone()
            if not plan:
                raise ValueError("所选生产计划不存在，请刷新列表后重试。")
            material_id, planned_quantity, plan_month, order_id = plan

            c.execute("SELECT component_id, quantity FROM product_components WHERE product_id=?", (material_id,))
            components = c.fetchall()
            # 兼容旧数据：若旧版只维护 materials.parent_id，则暂按每个父件用 1 个子件处理。
            if not components:
                c.execute("SELECT id, 1 FROM materials WHERE parent_id=?", (material_id,))
                components = c.fetchall()
            if not components:
                messagebox.showinfo("提示", "该物料没有关联组件；请先维护 BOM。")
                return

            for component_id, component_quantity in components:
                required_quantity = int(planned_quantity) * int(component_quantity or 1)
                c.execute("SELECT id, status FROM production_plans WHERE material_id=? AND plan_month=? AND order_id IS ?",
                          (component_id, plan_month, order_id))
                existing = c.fetchone()
                if existing:
                    existing_id, existing_status = existing
                    if existing_status != '计划中':
                        raise ValueError("组件已有非‘计划中’的生产计划。为避免覆盖已执行计划，本次操作已取消。")
                    c.execute("UPDATE production_plans SET planned_quantity=? WHERE id=?",
                              (required_quantity, existing_id))
                else:
                    c.execute("""INSERT INTO production_plans
                                 (material_id, plan_month, planned_quantity, order_id, status)
                                 VALUES (?, ?, ?, ?, '计划中')""",
                              (component_id, plan_month, required_quantity, order_id))
            conn.commit()
            messagebox.showinfo("成功", f"已根据 BOM 为 {len(components)} 个直接组件生成计划。")
            self.load_monthly_plans()
        except Exception as e:
            if conn is not None:
                conn.rollback()
            messagebox.showerror("错误", f"生成组件计划失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def clear_plan_form(self):
        self.plan_material_combobox.set('')
        self.plan_month_entry.delete(0, tk.END)
        self.plan_month_entry.insert(0, datetime.now().strftime("%Y-%m"))
        self.plan_quantity_entry.delete(0, tk.END)
        self.plan_order_combobox.current(0)
        self.plan_status_combobox.current(0)
        self.current_plan_id = None
        self.clear_schedule_form()


    def clear_schedule_form(self):
        self.schedule_warehouse_combobox.set('')
        self.schedule_date_entry.delete(0, tk.END)
        self.schedule_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.schedule_quantity_entry.delete(0, tk.END)


    def load_monthly_plans(self):
        for item in self.plan_tree.get_children():
            self.plan_tree.delete(item)
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT ds.id, m.material_name || '-' || ds.schedule_date || '-' || w.warehouse_name as schedule_label
                     FROM daily_schedules ds
                     JOIN production_plans pp ON ds.plan_id = pp.id
                     JOIN materials m ON pp.material_id = m.id
                     JOIN warehouses w ON ds.warehouse_id = w.id
                     ORDER BY ds.schedule_date DESC''')
        for row in c.fetchall():
            self.plan_tree.insert('', 'end', values=row)
        conn.close()


    def on_plan_select(self, event):
        selected = self.plan_tree.selection()
        if selected:
            item = self.plan_tree.item(selected)
            plan_id, material_name, plan_month, planned_quantity, order_label, status = item['values']
            self.current_plan_id = plan_id
            self.plan_material_combobox.set(material_name)
            self.plan_month_entry.delete(0, tk.END)
            self.plan_month_entry.insert(0, plan_month)
            self.plan_quantity_entry.delete(0, tk.END)
            self.plan_quantity_entry.insert(0, planned_quantity)
            self.plan_order_combobox.set(order_label)
            self.plan_status_combobox.set(status)
            # 加载该计划的日度排程
            self.load_daily_schedules(plan_id)
        else:
            self.clear_plan_form()


    def load_daily_schedules(self, plan_id):
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT ds.id, m.material_name, pp.plan_month, w.warehouse_name,
                             ds.schedule_date, ds.planned_quantity, ds.actual_quantity,
                             ds.qualified_quantity, ds.defective_quantity, ds.repair_quantity
                     FROM daily_schedules ds
                     JOIN production_plans pp ON ds.plan_id = pp.id
                     JOIN materials m ON pp.material_id = m.id
                     JOIN warehouses w ON ds.warehouse_id = w.id
                     WHERE ds.plan_id=?
                     ORDER BY ds.schedule_date''', (plan_id,))
        for row in c.fetchall():
            self.schedule_tree.insert('', 'end', values=row)
        conn.close()


    def add_daily_schedule(self):
        if not self.current_plan_id:
            messagebox.showwarning("警告", "请先选择一个月度计划！")
            return

        warehouse_name = self.schedule_warehouse_combobox.get()
        schedule_date = self.schedule_date_entry.get().strip()
        quantity_text = self.schedule_quantity_entry.get().strip()

        if not warehouse_name or not schedule_date or not quantity_text:
            messagebox.showwarning("警告", "生产车间、排程日期和排程数量不能为空！")
            return

        try:
            # 验证日期格式
            datetime.strptime(schedule_date, "%Y-%m-%d")
            quantity = int(quantity_text)
            if quantity < 0:
                raise ValueError
        except (ValueError, TypeError):
            messagebox.showwarning("警告", "日期格式应为YYYY-MM-DD，数量必须是非负整数！")
            return

        warehouse_id = self.warehouses_combobox_dict[warehouse_name]

        try:
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            # 检查是否已存在该排程
            c.execute("SELECT id FROM daily_schedules WHERE plan_id=? AND schedule_date=? AND warehouse_id=?", 
                      (self.current_plan_id, schedule_date, warehouse_id))
            existing_id = c.fetchone()
            if existing_id:
                # 更新
                c.execute('''UPDATE daily_schedules SET planned_quantity=?
                             WHERE id=?''',
                          (quantity, existing_id[0]))
                messagebox.showinfo("成功", "日度排程更新成功！")
            else:
                # 新增
                c.execute('''INSERT INTO daily_schedules (plan_id, warehouse_id, schedule_date, planned_quantity)
                             VALUES (?, ?, ?, ?)''',
                          (self.current_plan_id, warehouse_id, schedule_date, quantity))
                messagebox.showinfo("成功", "日度排程添加成功！")
            conn.commit()
            self.load_daily_schedules(self.current_plan_id)
            self.clear_schedule_form()
        except Exception as e:
            messagebox.showerror("错误", f"添加日度排程失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()

