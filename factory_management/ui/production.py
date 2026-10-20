import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ProductionMixin:

    def create_production_tab(self):
        # 生产记录表单
        record_frame = ttk.LabelFrame(self.tab_production, text="生产记录录入")
        record_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        ttk.Label(record_frame, text="排程:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.production_schedule_combobox = ttk.Combobox(record_frame, state="readonly")
        self.production_schedule_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.load_schedules_for_production_combobox()

        ttk.Label(record_frame, text="生产日期:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.production_date_entry = ttk.Entry(record_frame)
        self.production_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.production_date_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(record_frame, text="生产数量:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.production_quantity_entry = ttk.Entry(record_frame)
        self.production_quantity_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(record_frame, text="合格品数量:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.qualified_quantity_entry = ttk.Entry(record_frame)
        self.qualified_quantity_entry.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(record_frame, text="次品数量:").grid(row=4, column=0, padx=5, pady=5, sticky='w')
        self.defective_quantity_entry = ttk.Entry(record_frame)
        self.defective_quantity_entry.grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(record_frame, text="待修品数量:").grid(row=5, column=0, padx=5, pady=5, sticky='w')
        self.repair_quantity_entry = ttk.Entry(record_frame)
        self.repair_quantity_entry.grid(row=5, column=1, padx=5, pady=5)

        ttk.Label(record_frame, text="操作人员:").grid(row=6, column=0, padx=5, pady=5, sticky='w')
        self.operator_entry = ttk.Entry(record_frame)
        self.operator_entry.grid(row=6, column=1, padx=5, pady=5)

        ttk.Label(record_frame, text="备注:").grid(row=7, column=0, padx=5, pady=5, sticky='nw')
        self.production_remark_text = tk.Text(record_frame, height=3, width=30)
        self.production_remark_text.grid(row=7, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(record_frame)
        btn_frame.grid(row=8, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="保存生产记录", command=self.save_production_record).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="更新库存", command=self.update_inventory_from_production).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_production_form).grid(row=0, column=2, padx=5)

        # 生产记录列表
        list_frame = ttk.LabelFrame(self.tab_production, text="生产记录列表")
        list_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky='nsew')

        self.production_tree = ttk.Treeview(list_frame, columns=('ID', '物料', '日期', '数量', '合格品', '次品', '待修品', '操作人员'), show='headings')
        self.production_tree.heading('ID', text='ID')
        self.production_tree.heading('物料', text='物料名称')
        self.production_tree.heading('日期', text='生产日期')
        self.production_tree.heading('数量', text='生产数量')
        self.production_tree.heading('合格品', text='合格品数量')
        self.production_tree.heading('次品', text='次品数量')
        self.production_tree.heading('待修品', text='待修品数量')
        self.production_tree.heading('操作人员', text='操作人员')
        self.production_tree.column('ID', width=50)
        self.production_tree.column('物料', width=150)
        self.production_tree.column('日期', width=100)
        self.production_tree.column('数量', width=80)
        self.production_tree.column('合格品', width=80)
        self.production_tree.column('次品', width=80)
        self.production_tree.column('待修品', width=80)
        self.production_tree.column('操作人员', width=100)
        self.production_tree.bind('<<TreeviewSelect>>', self.on_production_select)
        self.production_tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.production_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.production_tree.configure(yscrollcommand=scrollbar.set)

        self.current_schedule_id = None
        self.current_production_id = None
        self.load_production_records()


    def load_schedules_for_production_combobox(self):
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT ds.id, m.material_name || '-' || ds.schedule_date || '-' || w.warehouse_name as schedule_label
                     FROM daily_schedules ds
                     JOIN production_plans pp ON ds.plan_id = pp.id
                     JOIN materials m ON pp.material_id = m.id
                     JOIN warehouses w ON ds.warehouse_id = w.id
                     ORDER BY ds.schedule_date DESC''')
        schedules = c.fetchall()
        self.schedules_combobox_dict = {label: id for id, label in schedules}
        self.production_schedule_combobox['values'] = list(self.schedules_combobox_dict.keys())
        conn.close()


    def save_production_record(self):
        """保存生产记录，并用“旧值差额”维护排程汇总。

        已入库记录禁止直接编辑，避免生产记录与库存流水出现不一致；
        如需更正，先设计正式的库存冲销/调整流程。
        """
        schedule_label = self.production_schedule_combobox.get()
        production_date = self.production_date_entry.get().strip()
        quantity_text = self.production_quantity_entry.get().strip()
        qualified_text = self.qualified_quantity_entry.get().strip()
        defective_text = self.defective_quantity_entry.get().strip()
        repair_text = self.repair_quantity_entry.get().strip()
        operator = self.operator_entry.get().strip()
        remark = self.production_remark_text.get("1.0", tk.END).strip()

        if not schedule_label or not production_date or not quantity_text or not qualified_text or not defective_text or not repair_text:
            messagebox.showwarning("警告", "排程、生产日期、生产数量、合格品/次品/待修品数量不能为空！")
            return

        try:
            datetime.strptime(production_date, "%Y-%m-%d")
            quantity = int(quantity_text)
            qualified = int(qualified_text)
            defective = int(defective_text)
            repair = int(repair_text)
            if min(quantity, qualified, defective, repair) < 0:
                raise ValueError("数量不能为负数")
            if qualified + defective + repair > quantity:
                messagebox.showwarning("警告", "合格品+次品+待修品数量不能超过生产总数！")
                return
        except (ValueError, TypeError):
            messagebox.showwarning("警告", "日期格式应为YYYY-MM-DD，数量必须是非负整数！")
            return

        schedule_id = self.schedules_combobox_dict.get(schedule_label)
        if schedule_id is None:
            messagebox.showwarning("警告", "请选择有效的生产排程！")
            return

        conn = None
        try:
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            if self.current_production_id:
                c.execute("SELECT schedule_id, quantity, qualified_quantity, defective_quantity, repair_quantity, stocked "
                          "FROM production_records WHERE id=?", (self.current_production_id,))
                old = c.fetchone()
                if not old:
                    raise ValueError("要修改的生产记录已不存在，请刷新列表后重试。")
                old_schedule_id, old_qty, old_qualified, old_defective, old_repair, stocked = old
                if stocked:
                    messagebox.showwarning("不能直接修改", "该生产记录已经入库。请先建立库存冲销/调整流程，再更正已过账记录。")
                    return

                c.execute("""UPDATE production_records
                             SET schedule_id=?, production_date=?, quantity=?, qualified_quantity=?,
                                 defective_quantity=?, repair_quantity=?, operator=?, remark=?
                             WHERE id=?""",
                          (schedule_id, production_date, quantity, qualified, defective, repair, operator, remark,
                           self.current_production_id))
                # 直接从明细重算，既避免重复累加，也能修复旧版本留下的汇总偏差。
                self._refresh_schedule_totals(conn, old_schedule_id)
                if schedule_id != old_schedule_id:
                    self._refresh_schedule_totals(conn, schedule_id)
                message = "生产记录更新成功！"
            else:
                c.execute("""INSERT INTO production_records
                             (schedule_id, production_date, quantity, qualified_quantity, defective_quantity,
                              repair_quantity, operator, remark)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                          (schedule_id, production_date, quantity, qualified, defective, repair, operator, remark))
                self.current_production_id = c.lastrowid
                self._refresh_schedule_totals(conn, schedule_id)
                message = "生产记录保存成功！"
            conn.commit()
            messagebox.showinfo("成功", message)
            self.load_production_records()
        except Exception as e:
            if conn is not None:
                conn.rollback()
            messagebox.showerror("错误", f"保存生产记录失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def update_inventory_from_production(self):
        """UI adapter: delegate the posting rules to the production service."""
        if not self.current_production_id:
            messagebox.showwarning("警告", "请先选择一条生产记录！")
            return
        conn = None
        try:
            from ..services.production_service import post_production_receipt
            conn = self.connect_db()
            result = post_production_receipt(conn, self.current_production_id)
            conn.commit()
            messagebox.showinfo("成功", f"已将 {result.quantity} 件合格品入库。")
            if hasattr(self, "inventory_tree"):
                self.load_inventory()
            self.load_production_records()
        except ValueError as exc:
            if conn is not None:
                conn.rollback()
            messagebox.showwarning("无法入库", str(exc))
        except Exception as exc:
            if conn is not None:
                conn.rollback()
            messagebox.showerror("错误", f"更新库存失败：{exc}")
        finally:
            if conn is not None:
                conn.close()

    def clear_production_form(self):
        self.production_schedule_combobox.set('')
        self.production_date_entry.delete(0, tk.END)
        self.production_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.production_quantity_entry.delete(0, tk.END)
        self.qualified_quantity_entry.delete(0, tk.END)
        self.defective_quantity_entry.delete(0, tk.END)
        self.repair_quantity_entry.delete(0, tk.END)
        self.operator_entry.delete(0, tk.END)
        self.production_remark_text.delete("1.0", tk.END)
        self.current_production_id = None


    def on_production_select(self, event):
        selected = self.production_tree.selection()
        if selected:
            item = self.production_tree.item(selected)
            production_id, material_name, production_date, quantity, qualified, defective, repair, operator = item['values']
            self.current_production_id = production_id
            # 获取该记录的排程信息
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            c.execute('''SELECT pr.schedule_id, pr.remark
                         FROM production_records pr
                         WHERE pr.id=?''', (production_id,))
            result = c.fetchone()
            conn.close()
            if result:
                schedule_id, remark = result
                # 设置表单值
                self.production_date_entry.delete(0, tk.END)
                self.production_date_entry.insert(0, production_date)
                self.production_quantity_entry.delete(0, tk.END)
                self.production_quantity_entry.insert(0, quantity)
                self.qualified_quantity_entry.delete(0, tk.END)
                self.qualified_quantity_entry.insert(0, qualified)
                self.defective_quantity_entry.delete(0, tk.END)
                self.defective_quantity_entry.insert(0, defective)
                self.repair_quantity_entry.delete(0, tk.END)
                self.repair_quantity_entry.insert(0, repair)
                self.operator_entry.delete(0, tk.END)
                self.operator_entry.insert(0, operator)
                self.production_remark_text.delete("1.0", tk.END)
                self.production_remark_text.insert("1.0", remark)
        else:
            self.clear_production_form()


    def load_production_records(self):
        for item in self.production_tree.get_children():
            self.production_tree.delete(item)
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT pr.id, m.material_name, pr.production_date, pr.quantity, pr.qualified_quantity,
                             pr.defective_quantity, pr.repair_quantity, pr.operator
                     FROM production_records pr
                     JOIN daily_schedules ds ON pr.schedule_id = ds.id
                     JOIN production_plans pp ON ds.plan_id = pp.id
                     JOIN materials m ON pp.material_id = m.id
                     ORDER BY pr.production_date DESC''')
        for row in c.fetchall():
            self.production_tree.insert('', 'end', values=row)
        conn.close()

