import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class InventoryMixin:

    def create_inventory_tab(self):
        # 库存查询区域
        query_frame = ttk.LabelFrame(self.tab_inventory, text="库存查询")
        query_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        ttk.Label(query_frame, text="物料:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.inventory_material_combobox = ttk.Combobox(query_frame, state="readonly")
        self.inventory_material_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.load_materials_for_combobox()

        ttk.Label(query_frame, text="仓库:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.inventory_warehouse_combobox = ttk.Combobox(query_frame, state="readonly")
        self.inventory_warehouse_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.load_warehouses_for_combobox()

        ttk.Button(query_frame, text="查询库存", command=self.query_inventory).grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(query_frame, text="显示所有库存", command=self.load_inventory).grid(row=3, column=0, columnspan=2, pady=5)

        # 库存变动区域
        change_frame = ttk.LabelFrame(self.tab_inventory, text="库存变动")
        change_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')

        ttk.Label(change_frame, text="变动类型:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.change_type_combobox = ttk.Combobox(change_frame, values=['入库', '出库', '退库'], state="readonly")
        self.change_type_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.change_type_combobox.current(0)

        ttk.Label(change_frame, text="变动数量:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.change_quantity_entry = ttk.Entry(change_frame)
        self.change_quantity_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(change_frame, text="关联订单:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.change_order_combobox = ttk.Combobox(change_frame, state="readonly")
        self.change_order_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.load_orders_for_combobox()

        ttk.Label(change_frame, text="备注:").grid(row=3, column=0, padx=5, pady=5, sticky='nw')
        self.change_remark_text = tk.Text(change_frame, height=3, width=30)
        self.change_remark_text.grid(row=3, column=1, padx=5, pady=5)

        ttk.Button(change_frame, text="确认变动", command=self.confirm_inventory_change).grid(row=4, column=0, columnspan=2, pady=10)

        # 库存列表
        list_frame = ttk.LabelFrame(self.tab_inventory, text="库存列表")
        list_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky='nsew')

        self.inventory_tree = ttk.Treeview(list_frame, columns=('ID', '物料', '仓库', '数量', '单位'), show='headings')
        self.inventory_tree.heading('ID', text='ID')
        self.inventory_tree.heading('物料', text='物料名称')
        self.inventory_tree.heading('仓库', text='仓库名称')
        self.inventory_tree.heading('数量', text='库存数量')
        self.inventory_tree.heading('单位', text='单位')
        self.inventory_tree.column('ID', width=50)
        self.inventory_tree.column('物料', width=150)
        self.inventory_tree.column('仓库', width=150)
        self.inventory_tree.column('数量', width=100)
        self.inventory_tree.column('单位', width=80)
        self.inventory_tree.bind('<<TreeviewSelect>>', self.on_inventory_select)
        self.inventory_tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.inventory_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.inventory_tree.configure(yscrollcommand=scrollbar.set)

        # 库存变动记录
        change_list_frame = ttk.LabelFrame(self.tab_inventory, text="库存变动记录")
        change_list_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

        self.inventory_change_tree = ttk.Treeview(change_list_frame, columns=('ID', '物料', '仓库', '类型', '数量', '日期', '备注'), show='headings')
        self.inventory_change_tree.heading('ID', text='ID')
        self.inventory_change_tree.heading('物料', text='物料名称')
        self.inventory_change_tree.heading('仓库', text='仓库名称')
        self.inventory_change_tree.heading('类型', text='变动类型')
        self.inventory_change_tree.heading('数量', text='变动数量')
        self.inventory_change_tree.heading('日期', text='变动日期')
        self.inventory_change_tree.heading('备注', text='备注')
        self.inventory_change_tree.column('ID', width=50)
        self.inventory_change_tree.column('物料', width=120)
        self.inventory_change_tree.column('仓库', width=120)
        self.inventory_change_tree.column('类型', width=80)
        self.inventory_change_tree.column('数量', width=80)
        self.inventory_change_tree.column('日期', width=100)
        self.inventory_change_tree.column('备注', width=200)
        self.inventory_change_tree.pack(side='left', fill='both', expand=True)

        scrollbar2 = ttk.Scrollbar(change_list_frame, orient='vertical', command=self.inventory_change_tree.yview)
        scrollbar2.pack(side='right', fill='y')
        self.inventory_change_tree.configure(yscrollcommand=scrollbar2.set)

        self.current_inventory_id = None
        self.load_inventory()
        self.load_inventory_changes()


    def load_warehouses_for_combobox(self):
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute("SELECT id, warehouse_name FROM warehouses ORDER BY warehouse_name")
        warehouses = c.fetchall()
        self.inventory_warehouses_dict = {name: id for id, name in warehouses}
        self.inventory_warehouse_combobox['values'] = list(self.inventory_warehouses_dict.keys())
        conn.close()


    def query_inventory(self):
        material_name = self.inventory_material_combobox.get()
        warehouse_name = self.inventory_warehouse_combobox.get()

        if not material_name or not warehouse_name:
            messagebox.showwarning("警告", "请选择物料和仓库！")
            return

        material_id = self.materials_combobox_dict[material_name]
        warehouse_id = self.inventory_warehouses_dict[warehouse_name]

        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT i.id, m.material_name, w.warehouse_name, i.quantity, m.unit
                     FROM inventory i
                     JOIN materials m ON i.material_id = m.id
                     JOIN warehouses w ON i.warehouse_id = w.id
                     WHERE i.material_id=? AND i.warehouse_id=?''', (material_id, warehouse_id))
        result = c.fetchone()
        if result:
            self.inventory_tree.insert('', 'end', values=result)
        else:
            messagebox.showinfo("提示", "该物料在该仓库暂无库存！")
        conn.close()


    def load_inventory(self):
        for item in self.inventory_tree.get_children():
            self.inventory_tree.delete(item)
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT i.id, m.material_name, w.warehouse_name, i.quantity, m.unit
                     FROM inventory i
                     JOIN materials m ON i.material_id = m.id
                     JOIN warehouses w ON i.warehouse_id = w.id
                     ORDER BY m.material_name, w.warehouse_name''')
        for row in c.fetchall():
            self.inventory_tree.insert('', 'end', values=row)
        conn.close()


    def on_inventory_select(self, event):
        selected = self.inventory_tree.selection()
        if selected:
            item = self.inventory_tree.item(selected)
            inventory_id, material_name, warehouse_name, quantity, unit = item['values']
            self.current_inventory_id = inventory_id
            self.inventory_material_combobox.set(material_name)
            self.inventory_warehouse_combobox.set(warehouse_name)
        else:
            self.current_inventory_id = None


    def confirm_inventory_change(self):
        if not self.current_inventory_id:
            messagebox.showwarning("警告", "请先选择一条库存记录！")
            return

        change_type = self.change_type_combobox.get()
        quantity_text = self.change_quantity_entry.get().strip()
        order_label = self.change_order_combobox.get()
        remark = self.change_remark_text.get("1.0", tk.END).strip()

        if not quantity_text:
            messagebox.showwarning("警告", "变动数量不能为空！")
            return

        try:
            quantity = int(quantity_text)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("警告", "变动数量必须是正整数！")
            return

        order_id = self.orders_combobox_dict.get(order_label) if order_label != '无' else None

        try:
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            # 获取当前库存信息
            c.execute('''SELECT i.material_id, i.warehouse_id, i.quantity
                         FROM inventory i
                         WHERE i.id=?''', (self.current_inventory_id,))
            inventory = c.fetchone()
            if not inventory:
                messagebox.showwarning("警告", "库存记录不存在！")
                return

            material_id, warehouse_id, current_quantity = inventory
            new_quantity = current_quantity

            # 根据变动类型计算新库存
            if change_type == '入库':
                new_quantity += quantity
            elif change_type == '出库':
                if current_quantity < quantity:
                    messagebox.showwarning("警告", "库存不足，无法出库！")
                    return
                new_quantity -= quantity
            elif change_type == '退库':
                new_quantity += quantity

            # 更新库存
            c.execute("UPDATE inventory SET quantity=? WHERE id=?", (new_quantity, self.current_inventory_id))

            # 记录库存变动
            c.execute('''INSERT INTO inventory_changes (material_id, warehouse_id, change_type, quantity,
                         change_date, related_order_id, remark)
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (material_id, warehouse_id, change_type, quantity, datetime.now().strftime("%Y-%m-%d"),
                       order_id, remark))

            conn.commit()
            messagebox.showinfo("成功", "库存变动已确认！")
            self.load_inventory()
            self.load_inventory_changes()
            self.clear_inventory_change_form()
        except Exception as e:
            messagebox.showerror("错误", f"确认库存变动失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def clear_inventory_change_form(self):
        self.change_type_combobox.current(0)
        self.change_quantity_entry.delete(0, tk.END)
        self.change_order_combobox.current(0)
        self.change_remark_text.delete("1.0", tk.END)


    def load_inventory_changes(self):
        for item in self.inventory_change_tree.get_children():
            self.inventory_change_tree.delete(item)
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT ic.id, m.material_name, w.warehouse_name, ic.change_type,
                             ic.quantity, ic.change_date, ic.remark
                     FROM inventory_changes ic
                     JOIN materials m ON ic.material_id = m.id
                     JOIN warehouses w ON ic.warehouse_id = w.id
                     ORDER BY ic.change_date DESC
                     LIMIT 100''')
        for row in c.fetchall():
            self.inventory_change_tree.insert('', 'end', values=row)
        conn.close()

