import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class OrdersMixin:

    def create_orders_tab(self):
        # 订单信息表单
        order_frame = ttk.LabelFrame(self.tab_orders, text="订单信息")
        order_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        ttk.Label(order_frame, text="客户:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.order_customer_combobox = ttk.Combobox(order_frame, state="readonly")
        self.order_customer_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.load_customers_for_combobox()

        ttk.Label(order_frame, text="订单日期:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.order_date_entry = ttk.Entry(order_frame)
        self.order_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.order_date_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(order_frame, text="交货日期:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.order_delivery_date_entry = ttk.Entry(order_frame)
        self.order_delivery_date_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(order_frame, text="订单类型:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.order_type_combobox = ttk.Combobox(order_frame, values=['订单', '备货'], state="readonly")
        self.order_type_combobox.grid(row=3, column=1, padx=5, pady=5)
        self.order_type_combobox.current(0)

        ttk.Label(order_frame, text="订单状态:").grid(row=4, column=0, padx=5, pady=5, sticky='w')
        self.order_status_combobox = ttk.Combobox(order_frame, values=['待生产', '生产中', '已完成', '已交货', '部分交货'], state="readonly")
        self.order_status_combobox.grid(row=4, column=1, padx=5, pady=5)
        self.order_status_combobox.current(0)

        ttk.Label(order_frame, text="备注:").grid(row=5, column=0, padx=5, pady=5, sticky='nw')
        self.order_remark_text = tk.Text(order_frame, height=3, width=30)
        self.order_remark_text.grid(row=5, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(order_frame)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="保存订单", command=self.save_order).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_order_form).grid(row=0, column=1, padx=5)

        # 订单明细
        items_frame = ttk.LabelFrame(self.tab_orders, text="订单明细")
        items_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')

        ttk.Label(items_frame, text="产品:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.order_item_material_combobox = ttk.Combobox(items_frame, state="readonly")
        self.order_item_material_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.load_finished_products_for_combobox()

        ttk.Label(items_frame, text="订单数量:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.order_item_quantity_entry = ttk.Entry(items_frame)
        self.order_item_quantity_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(items_frame, text="备货数量:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.order_item_prepared_entry = ttk.Entry(items_frame)
        self.order_item_prepared_entry.grid(row=2, column=1, padx=5, pady=5)
        self.order_item_prepared_entry.insert(0, "0")

        ttk.Label(items_frame, text="单价:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.order_item_price_entry = ttk.Entry(items_frame)
        self.order_item_price_entry.grid(row=3, column=1, padx=5, pady=5)
        self.order_item_price_entry.insert(0, "0")

        ttk.Button(items_frame, text="添加明细", command=self.add_order_item).grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(items_frame, text="自动生成组件需求", command=self.generate_component_requirements).grid(row=4, column=2, padx=5, pady=10)

        # 订单明细列表
        items_list_frame = ttk.LabelFrame(self.tab_orders, text="订单明细列表")
        items_list_frame.grid(row=2, column=0, padx=10, pady=10, sticky='nsew')

        self.order_items_tree = ttk.Treeview(items_list_frame, columns=('ID', '产品', '订单数量', '备货数量', '已交货数量', '单价'), show='headings')
        self.order_items_tree.heading('ID', text='ID')
        self.order_items_tree.heading('产品', text='产品名称')
        self.order_items_tree.heading('订单数量', text='订单数量')
        self.order_items_tree.heading('备货数量', text='备货数量')
        self.order_items_tree.heading('已交货数量', text='已交货数量')
        self.order_items_tree.heading('单价', text='单价')
        self.order_items_tree.column('ID', width=50)
        self.order_items_tree.column('产品', width=150)
        self.order_items_tree.column('订单数量', width=80)
        self.order_items_tree.column('备货数量', width=80)
        self.order_items_tree.column('已交货数量', width=100)
        self.order_items_tree.column('单价', width=80)
        self.order_items_tree.pack(side='left', fill='both', expand=True)

        scrollbar1 = ttk.Scrollbar(items_list_frame, orient='vertical', command=self.order_items_tree.yview)
        scrollbar1.pack(side='right', fill='y')
        self.order_items_tree.configure(yscrollcommand=scrollbar1.set)

        # 订单列表
        list_frame = ttk.LabelFrame(self.tab_orders, text="订单列表")
        list_frame.grid(row=0, column=1, rowspan=3, padx=10, pady=10, sticky='nsew')

        self.orders_tree = ttk.Treeview(list_frame, columns=('ID', '客户', '订单日期', '交货日期', '类型', '状态', '总金额'), show='headings')
        self.orders_tree.heading('ID', text='ID')
        self.orders_tree.heading('客户', text='客户名称')
        self.orders_tree.heading('订单日期', text='订单日期')
        self.orders_tree.heading('交货日期', text='交货日期')
        self.orders_tree.heading('类型', text='订单类型')
        self.orders_tree.heading('状态', text='订单状态')
        self.orders_tree.heading('总金额', text='总金额')
        self.orders_tree.column('ID', width=50)
        self.orders_tree.column('客户', width=150)
        self.orders_tree.column('订单日期', width=100)
        self.orders_tree.column('交货日期', width=100)
        self.orders_tree.column('类型', width=80)
        self.orders_tree.column('状态', width=100)
        self.orders_tree.column('总金额', width=100)
        self.orders_tree.bind('<<TreeviewSelect>>', self.on_order_select)
        self.orders_tree.pack(side='left', fill='both', expand=True)

        scrollbar2 = ttk.Scrollbar(list_frame, orient='vertical', command=self.orders_tree.yview)
        scrollbar2.pack(side='right', fill='y')
        self.orders_tree.configure(yscrollcommand=scrollbar2.set)

        # 导入按钮
        ttk.Button(self.tab_orders, text="从Excel导入订单", command=self.import_orders_from_excel).grid(row=3, column=0, padx=10, pady=5, sticky='w')

        self.current_order_id = None
        self.load_orders()


    def load_customers_for_combobox(self):
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute("SELECT id, customer_name FROM customers ORDER BY customer_name")
        customers = c.fetchall()
        self.customers_dict = {name: id for id, name in customers}
        self.order_customer_combobox['values'] = list(self.customers_dict.keys())
        conn.close()


    def load_finished_products_for_combobox(self):
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT m.id, m.material_name 
                     FROM materials m
                     JOIN material_types t ON m.type_id = t.id
                     WHERE t.type_name='成品'
                     ORDER BY m.material_name''')
        products = c.fetchall()
        self.finished_products_dict = {name: id for id, name in products}
        self.order_item_material_combobox['values'] = list(self.finished_products_dict.keys())
        conn.close()


    def save_order(self):
        customer_name = self.order_customer_combobox.get()
        order_date = self.order_date_entry.get().strip()
        delivery_date = self.order_delivery_date_entry.get().strip()
        order_type = self.order_type_combobox.get()
        status = self.order_status_combobox.get()
        remark = self.order_remark_text.get("1.0", tk.END).strip()

        if not customer_name or not order_date:
            messagebox.showwarning("警告", "客户和订单日期不能为空！")
            return

        customer_id = self.customers_dict[customer_name]

        try:
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            if self.current_order_id:
                # 更新订单
                c.execute('''UPDATE orders SET customer_id=?, order_date=?, delivery_date=?, order_type=?, status=?, remark=?
                             WHERE id=?''',
                          (customer_id, order_date, delivery_date, order_type, status, remark, self.current_order_id))
                messagebox.showinfo("成功", "订单信息更新成功！")
            else:
                # 新增订单
                c.execute('''INSERT INTO orders (customer_id, order_date, delivery_date, order_type, status, remark)
                             VALUES (?, ?, ?, ?, ?, ?)''',
                          (customer_id, order_date, delivery_date, order_type, status, remark))
                self.current_order_id = c.lastrowid
                messagebox.showinfo("成功", "订单信息保存成功！")
            self._refresh_order_total(conn, self.current_order_id)
            conn.commit()
            self.load_orders()
        except Exception as e:
            messagebox.showerror("错误", f"保存订单失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def clear_order_form(self):
        self.order_customer_combobox.set('')
        self.order_date_entry.delete(0, tk.END)
        self.order_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.order_delivery_date_entry.delete(0, tk.END)
        self.order_type_combobox.current(0)
        self.order_status_combobox.current(0)
        self.order_remark_text.delete("1.0", tk.END)
        self.current_order_id = None
        self.clear_order_items()


    def clear_order_items(self):
        self.order_item_material_combobox.set('')
        self.order_item_quantity_entry.delete(0, tk.END)
        self.order_item_prepared_entry.delete(0, tk.END)
        self.order_item_prepared_entry.insert(0, "0")
        self.order_item_price_entry.delete(0, tk.END)
        self.order_item_price_entry.insert(0, "0")
        for item in self.order_items_tree.get_children():
            self.order_items_tree.delete(item)


    def add_order_item(self):
        if not self.current_order_id:
            messagebox.showwarning("警告", "请先保存订单！")
            return

        material_name = self.order_item_material_combobox.get()
        quantity_text = self.order_item_quantity_entry.get().strip()
        prepared_text = self.order_item_prepared_entry.get().strip()
        price_text = self.order_item_price_entry.get().strip()

        if not material_name or not quantity_text:
            messagebox.showwarning("警告", "产品和订单数量不能为空！")
            return

        try:
            quantity = int(quantity_text)
            prepared = int(prepared_text) if prepared_text else 0
            price = float(price_text) if price_text else 0.0
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("警告", "数量必须是正整数，单价必须是数字！")
            return

        material_id = self.finished_products_dict[material_name]

        try:
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            # 检查是否已存在该产品的明细
            c.execute("SELECT id FROM order_items WHERE order_id=? AND material_id=?", (self.current_order_id, material_id))
            existing_id = c.fetchone()
            if existing_id:
                # 更新
                c.execute('''UPDATE order_items SET order_quantity=?, prepared_quantity=?, unit_price=?
                             WHERE id=?''',
                          (quantity, prepared, price, existing_id[0]))
                messagebox.showinfo("成功", "订单明细更新成功！")
            else:
                # 新增
                c.execute('''INSERT INTO order_items (order_id, material_id, order_quantity, prepared_quantity, unit_price)
                             VALUES (?, ?, ?, ?, ?)''',
                          (self.current_order_id, material_id, quantity, prepared, price))
                messagebox.showinfo("成功", "订单明细添加成功！")
            self._refresh_order_total(conn, self.current_order_id)
            conn.commit()
            self.load_order_items(self.current_order_id)
            self.clear_order_items_form()
        except Exception as e:
            messagebox.showerror("错误", f"添加订单明细失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def generate_component_requirements(self):
        # 根据订单明细自动生成组件需求
        if not self.current_order_id:
            messagebox.showwarning("警告", "请先保存订单！")
            return

        try:
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            # 获取订单明细
            c.execute('''SELECT oi.material_id, oi.order_quantity
                         FROM order_items oi
                         WHERE oi.order_id=?''', (self.current_order_id,))
            order_items = c.fetchall()

            if not order_items:
                messagebox.showinfo("提示", "订单中没有产品明细！")
                return

            success_count = 0
            for material_id, order_quantity in order_items:
                # 获取该产品的组件
                c.execute('''SELECT pc.component_id, pc.quantity
                             FROM product_components pc
                             WHERE pc.product_id=?''', (material_id,))
                components = c.fetchall()

                if not components:
                    continue

                # 获取当前月份
                current_month = datetime.now().strftime("%Y-%m")
                for component_id, component_quantity in components:
                    # 计算组件需求数量
                    required_quantity = order_quantity * component_quantity

                    # 检查组件是否已有生产计划
                    c.execute('''SELECT id FROM production_plans
                                 WHERE material_id=? AND plan_month=? AND order_id=?''',
                              (component_id, current_month, self.current_order_id))
                    existing_plan = c.fetchone()
                    if existing_plan:
                        # 更新计划数量
                        c.execute('''UPDATE production_plans SET planned_quantity=?
                                     WHERE id=?''',
                                  (required_quantity, existing_plan[0]))
                    else:
                        # 新增生产计划
                        c.execute('''INSERT INTO production_plans (material_id, plan_month, planned_quantity, order_id, status)
                                     VALUES (?, ?, ?, ?, '计划中')''',
                                  (component_id, current_month, required_quantity, self.current_order_id))
                    success_count += 1

            conn.commit()
            messagebox.showinfo("成功", f"已为 {success_count} 个组件自动生成生产计划！")
            # 刷新生产计划列表
            if hasattr(self, 'plan_tree'):
                self.load_monthly_plans()
        except Exception as e:
            messagebox.showerror("错误", f"生成组件需求失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def clear_order_items_form(self):
        self.order_item_material_combobox.set('')
        self.order_item_quantity_entry.delete(0, tk.END)
        self.order_item_prepared_entry.delete(0, tk.END)
        self.order_item_prepared_entry.insert(0, "0")
        self.order_item_price_entry.delete(0, tk.END)
        self.order_item_price_entry.insert(0, "0")


    def on_order_select(self, event):
        selected = self.orders_tree.selection()
        if selected:
            item = self.orders_tree.item(selected)
            order_id, customer_name, order_date, delivery_date, order_type, status, total_amount = item['values']
            self.current_order_id = order_id
            self.order_customer_combobox.set(customer_name)
            self.order_date_entry.delete(0, tk.END)
            self.order_date_entry.insert(0, order_date)
            self.order_delivery_date_entry.delete(0, tk.END)
            self.order_delivery_date_entry.insert(0, delivery_date)
            self.order_type_combobox.set(order_type)
            self.order_status_combobox.set(status)
            # 获取订单备注
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            c.execute("SELECT remark FROM orders WHERE id=?", (order_id,))
            remark = c.fetchone()[0]
            conn.close()
            self.order_remark_text.delete("1.0", tk.END)
            self.order_remark_text.insert("1.0", remark)
            # 加载订单明细
            self.load_order_items(order_id)
        else:
            self.clear_order_form()


    def load_orders(self):
        for item in self.orders_tree.get_children():
            self.orders_tree.delete(item)
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT o.id, c.customer_name, o.order_date, o.delivery_date, o.order_type, o.status,
                             COALESCE(SUM(oi.order_quantity * oi.unit_price), 0) as total_amount
                     FROM orders o
                     JOIN customers c ON o.customer_id = c.id
                     LEFT JOIN order_items oi ON o.id = oi.order_id
                     GROUP BY o.id, c.customer_name, o.order_date, o.delivery_date, o.order_type, o.status
                     ORDER BY o.order_date DESC''')
        for row in c.fetchall():
            self.orders_tree.insert('', 'end', values=row)
        conn.close()


    def load_order_items(self, order_id):
        for item in self.order_items_tree.get_children():
            self.order_items_tree.delete(item)
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT oi.id, m.material_name, oi.order_quantity, oi.prepared_quantity, oi.delivered_quantity, oi.unit_price
                     FROM order_items oi
                     JOIN materials m ON oi.material_id = m.id
                     WHERE oi.order_id=?''', (order_id,))
        for row in c.fetchall():
            self.order_items_tree.insert('', 'end', values=row)
        conn.close()


    def import_orders_from_excel(self, file_path=None):
        if file_path is None:
            file_path = filedialog.askopenfilename(filetypes=[("Excel文件", "*.xlsx;*.xls")])
        if not file_path:
            return
        try:
            df = pd.read_excel(file_path)
            required_columns = ['客户名称', '订单日期', '产品名称', '订单数量']
            if not all(col in df.columns for col in required_columns):
                messagebox.showerror("错误", "Excel文件格式不正确，必须包含'客户名称'、'订单日期'、'产品名称'和'订单数量'列！")
                return

            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            success_count = 0
            error_count = 0
            current_order_id = None
            current_customer = None
            current_order_date = None
            for _, row in df.iterrows():
                customer_name = str(row['客户名称']).strip()
                order_date = str(row['订单日期']).strip()
                product_name = str(row['产品名称']).strip()
                quantity_text = str(row['订单数量']).strip()
                prepared_text = str(row.get('备货数量', '0')).strip()
                price_text = str(row.get('单价', '0')).strip()
                delivery_date = str(row.get('交货日期', '')).strip()
                order_type = str(row.get('订单类型', '订单')).strip()
                remark = str(row.get('备注', '')).strip()

                if not customer_name or not order_date or not product_name or not quantity_text:
                    error_count += 1
                    continue

                try:
                    quantity = int(quantity_text)
                    prepared = int(prepared_text) if prepared_text else 0
                    price = float(price_text) if price_text else 0.0
                    if quantity <= 0:
                        raise ValueError
                except ValueError:
                    error_count += 1
                    continue

                # 检查客户是否存在
                c.execute("SELECT id FROM customers WHERE customer_name=?", (customer_name,))
                customer_id = c.fetchone()
                if not customer_id:
                    c.execute("INSERT INTO customers (customer_name) VALUES (?)", (customer_name,))
                    customer_id = c.lastrowid
                else:
                    customer_id = customer_id[0]

                # 检查产品是否存在
                c.execute("SELECT id FROM materials WHERE material_name=? AND type_id=(SELECT id FROM material_types WHERE type_name='成品')", (product_name,))
                product_id = c.fetchone()
                if not product_id:
                    error_count += 1
                    continue
                else:
                    product_id = product_id[0]

                # 检查是否是同一个订单
                if current_order_id is None or current_customer != customer_name or current_order_date != order_date:
                    # 新增订单
                    c.execute('''INSERT INTO orders (customer_id, order_date, delivery_date, order_type, remark)
                                 VALUES (?, ?, ?, ?, ?)''',
                              (customer_id, order_date, delivery_date, order_type, remark))
                    current_order_id = c.lastrowid
                    current_customer = customer_name
                    current_order_date = order_date
                    success_count += 1

                # 添加订单明细
                try:
                    c.execute('''INSERT INTO order_items (order_id, material_id, order_quantity, prepared_quantity, unit_price)
                                 VALUES (?, ?, ?, ?, ?)''',
                              (current_order_id, product_id, quantity, prepared, price))
                    success_count += 1
                except Exception as e:
                    error_count += 1
            # 导入可能插入多条订单明细，统一从明细重算所有订单金额。
            c.execute("""UPDATE orders SET total_amount = COALESCE((
                         SELECT SUM(order_quantity * unit_price) FROM order_items WHERE order_items.order_id = orders.id
                       ), 0)""")
            conn.commit()
            messagebox.showinfo("导入结果", f"成功导入 {success_count} 条订单及明细信息，{error_count} 条数据因格式错误或产品不存在已跳过。")
            self.load_orders()
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()

