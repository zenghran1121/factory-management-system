import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class PurchasingSettlementMixin:

    def create_purchase_tab(self):
        # 采购需求表单
        request_frame = ttk.LabelFrame(self.tab_purchase, text="采购需求")
        request_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        ttk.Label(request_frame, text="物料:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.purchase_material_combobox = ttk.Combobox(request_frame, state="readonly")
        self.purchase_material_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.load_materials_for_combobox()

        ttk.Label(request_frame, text="需求日期:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.purchase_request_date_entry = ttk.Entry(request_frame)
        self.purchase_request_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.purchase_request_date_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(request_frame, text="需求数量:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.purchase_required_quantity_entry = ttk.Entry(request_frame)
        self.purchase_required_quantity_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(request_frame, text="状态:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.purchase_status_combobox = ttk.Combobox(request_frame, values=['待处理', '已采购', '已入库'], state="readonly")
        self.purchase_status_combobox.grid(row=3, column=1, padx=5, pady=5)
        self.purchase_status_combobox.current(0)

        btn_frame = ttk.Frame(request_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="保存采购需求", command=self.save_purchase_request).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="自动生成采购需求", command=self.auto_generate_purchase_requests).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_purchase_form).grid(row=0, column=2, padx=5)

        # 采购需求列表
        list_frame = ttk.LabelFrame(self.tab_purchase, text="采购需求列表")
        list_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

        self.purchase_tree = ttk.Treeview(list_frame, columns=('ID', '物料', '需求日期', '需求数量', '已采购数量', '已入库数量', '状态'), show='headings')
        self.purchase_tree.heading('ID', text='ID')
        self.purchase_tree.heading('物料', text='物料名称')
        self.purchase_tree.heading('需求日期', text='需求日期')
        self.purchase_tree.heading('需求数量', text='需求数量')
        self.purchase_tree.heading('已采购数量', text='已采购数量')
        self.purchase_tree.heading('已入库数量', text='已入库数量')
        self.purchase_tree.heading('状态', text='状态')
        self.purchase_tree.column('ID', width=50)
        self.purchase_tree.column('物料', width=150)
        self.purchase_tree.column('需求日期', width=100)
        self.purchase_tree.column('需求数量', width=100)
        self.purchase_tree.column('已采购数量', width=100)
        self.purchase_tree.column('已入库数量', width=100)
        self.purchase_tree.column('状态', width=100)
        self.purchase_tree.bind('<<TreeviewSelect>>', self.on_purchase_select)
        self.purchase_tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.purchase_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.purchase_tree.configure(yscrollcommand=scrollbar.set)

        self.current_purchase_id = None
        self.load_purchase_requests()


    def save_purchase_request(self):
        material_name = self.purchase_material_combobox.get()
        request_date = self.purchase_request_date_entry.get().strip()
        required_quantity_text = self.purchase_required_quantity_entry.get().strip()
        status = self.purchase_status_combobox.get()

        if not material_name or not request_date or not required_quantity_text:
            messagebox.showwarning("警告", "物料、需求日期和需求数量不能为空！")
            return

        try:
            datetime.strptime(request_date, "%Y-%m-%d")
            required_quantity = int(required_quantity_text)
            if required_quantity <= 0:
                raise ValueError
        except (ValueError, TypeError):
            messagebox.showwarning("警告", "日期格式应为YYYY-MM-DD，需求数量必须是正整数！")
            return

        material_id = self.materials_combobox_dict[material_name]

        try:
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            if self.current_purchase_id:
                # 更新
                c.execute('''UPDATE purchase_requests SET required_quantity=?, status=?
                             WHERE id=?''',
                          (required_quantity, status, self.current_purchase_id))
                messagebox.showinfo("成功", "采购需求更新成功！")
            else:
                # 新增
                c.execute('''INSERT INTO purchase_requests (material_id, request_date, required_quantity, status)
                             VALUES (?, ?, ?, ?)''',
                          (material_id, request_date, required_quantity, status))
                self.current_purchase_id = c.lastrowid
                messagebox.showinfo("成功", "采购需求保存成功！")
            conn.commit()
            self.load_purchase_requests()
        except Exception as e:
            messagebox.showerror("错误", f"保存采购需求失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def auto_generate_purchase_requests(self):
        """安全提示：当前数据模型没有完整的组件/原材料用量 BOM，不能可靠自动算原料采购量。

        旧逻辑把“原材料生产计划量 - 库存”当采购缺口，会产生看似合理但业务依据错误的结果。
        在增加并维护原材料用量 BOM 后，再实现真正的净需求计算。
        """
        messagebox.showwarning(
            "暂不可自动计算",
            "当前版本尚未保存‘每个组件需要多少原材料’的用量关系。\n\n"
            "旧算法直接用原材料生产计划量减库存，可能生成错误采购需求，因此已停止自动写入。\n\n"
            "下一步应补充原材料 BOM（父物料、原材料、单位用量、损耗率），再扣除可用库存和有效在途采购量。"
        )


    def clear_purchase_form(self):
        self.purchase_material_combobox.set('')
        self.purchase_request_date_entry.delete(0, tk.END)
        self.purchase_request_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.purchase_required_quantity_entry.delete(0, tk.END)
        self.purchase_status_combobox.current(0)
        self.current_purchase_id = None


    def on_purchase_select(self, event):
        selected = self.purchase_tree.selection()
        if selected:
            item = self.purchase_tree.item(selected)
            purchase_id, material_name, request_date, required_quantity, planned_quantity, completed_quantity, status = item['values']
            self.current_purchase_id = purchase_id
            self.purchase_material_combobox.set(material_name)
            self.purchase_request_date_entry.delete(0, tk.END)
            self.purchase_request_date_entry.insert(0, request_date)
            self.purchase_required_quantity_entry.delete(0, tk.END)
            self.purchase_required_quantity_entry.insert(0, required_quantity)
            self.purchase_status_combobox.set(status)
        else:
            self.clear_purchase_form()


    def load_purchase_requests(self):
        for item in self.purchase_tree.get_children():
            self.purchase_tree.delete(item)
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT pr.id, m.material_name, pr.request_date, pr.required_quantity,
                             pr.planned_quantity, pr.completed_quantity, pr.status
                     FROM purchase_requests pr
                     JOIN materials m ON pr.material_id = m.id
                     ORDER BY pr.request_date DESC''')
        for row in c.fetchall():
            self.purchase_tree.insert('', 'end', values=row)
        conn.close()


    def create_settlement_tab(self):
        # 结算表单
        settlement_frame = ttk.LabelFrame(self.tab_settlement, text="结算信息")
        settlement_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        ttk.Label(settlement_frame, text="订单:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.settlement_order_combobox = ttk.Combobox(settlement_frame, state="readonly")
        self.settlement_order_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.load_orders_for_combobox()

        ttk.Label(settlement_frame, text="结算日期:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.settlement_date_entry = ttk.Entry(settlement_frame)
        self.settlement_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.settlement_date_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(settlement_frame, text="结算金额:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.settlement_amount_entry = ttk.Entry(settlement_frame)
        self.settlement_amount_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(settlement_frame, text="已付金额:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.settlement_paid_entry = ttk.Entry(settlement_frame)
        self.settlement_paid_entry.grid(row=3, column=1, padx=5, pady=5)
        self.settlement_paid_entry.insert(0, "0")

        ttk.Label(settlement_frame, text="发票编号:").grid(row=4, column=0, padx=5, pady=5, sticky='w')
        self.settlement_invoice_entry = ttk.Entry(settlement_frame)
        self.settlement_invoice_entry.grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(settlement_frame, text="结算状态:").grid(row=5, column=0, padx=5, pady=5, sticky='w')
        self.settlement_status_combobox = ttk.Combobox(settlement_frame, values=['未结算', '部分结算', '已结算'], state="readonly")
        self.settlement_status_combobox.grid(row=5, column=1, padx=5, pady=5)
        self.settlement_status_combobox.current(0)

        ttk.Label(settlement_frame, text="备注:").grid(row=6, column=0, padx=5, pady=5, sticky='nw')
        self.settlement_remark_text = tk.Text(settlement_frame, height=3, width=30)
        self.settlement_remark_text.grid(row=6, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(settlement_frame)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="保存结算记录", command=self.save_settlement).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_settlement_form).grid(row=0, column=1, padx=5)

        # 结算列表
        list_frame = ttk.LabelFrame(self.tab_settlement, text="结算记录列表")
        list_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')

        self.settlement_tree = ttk.Treeview(list_frame, columns=('ID', '订单', '客户', '结算日期', '结算金额', '已付金额', '状态'), show='headings')
        self.settlement_tree.heading('ID', text='ID')
        self.settlement_tree.heading('订单', text='订单编号')
        self.settlement_tree.heading('客户', text='客户名称')
        self.settlement_tree.heading('结算日期', text='结算日期')
        self.settlement_tree.heading('结算金额', text='结算金额')
        self.settlement_tree.heading('已付金额', text='已付金额')
        self.settlement_tree.heading('状态', text='结算状态')
        self.settlement_tree.column('ID', width=50)
        self.settlement_tree.column('订单', width=100)
        self.settlement_tree.column('客户', width=150)
        self.settlement_tree.column('结算日期', width=100)
        self.settlement_tree.column('结算金额', width=100)
        self.settlement_tree.column('已付金额', width=100)
        self.settlement_tree.column('状态', width=100)
        self.settlement_tree.bind('<<TreeviewSelect>>', self.on_settlement_select)
        self.settlement_tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.settlement_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.settlement_tree.configure(yscrollcommand=scrollbar.set)

        self.current_settlement_id = None
        self.load_settlements()


    def save_settlement(self):
        order_label = self.settlement_order_combobox.get()
        settlement_date = self.settlement_date_entry.get().strip()
        amount_text = self.settlement_amount_entry.get().strip()
        paid_text = self.settlement_paid_entry.get().strip()
        invoice_number = self.settlement_invoice_entry.get().strip()
        # 状态根据金额自动计算，避免用户手选状态与实际付款不一致。
        status = self.settlement_status_combobox.get()
        remark = self.settlement_remark_text.get("1.0", tk.END).strip()

        if not order_label or not settlement_date or not amount_text:
            messagebox.showwarning("警告", "订单、结算日期和结算金额不能为空！")
            return

        try:
            datetime.strptime(settlement_date, "%Y-%m-%d")
            amount = float(amount_text)
            paid = float(paid_text) if paid_text else 0.0
            if amount <= 0 or paid < 0:
                raise ValueError
            if paid > amount:
                messagebox.showwarning("金额不合理", "已付金额不能超过本条结算金额；如需处理预收款，请先明确预收款业务规则。")
                return
        except (ValueError, TypeError):
            messagebox.showwarning("警告", "日期格式应为YYYY-MM-DD，结算金额必须大于 0，已付金额必须为非负数字！")
            return

        if paid <= 0:
            status = '未结算'
        elif paid < amount:
            status = '部分结算'
        else:
            status = '已结算'

        order_id = self.orders_combobox_dict.get(order_label) if order_label != '无' else None

        try:
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            if self.current_settlement_id:
                # 更新
                c.execute('''UPDATE settlement_records SET settlement_date=?, settlement_amount=?, paid_amount=?,
                             invoice_number=?, status=?, remark=?
                             WHERE id=?''',
                          (settlement_date, amount, paid, invoice_number, status, remark, self.current_settlement_id))
                messagebox.showinfo("成功", "结算记录更新成功！")
            else:
                # 新增
                c.execute('''INSERT INTO settlement_records (order_id, settlement_date, settlement_amount, paid_amount,
                             invoice_number, status, remark)
                             VALUES (?, ?, ?, ?, ?, ?, ?)''',
                          (order_id, settlement_date, amount, paid, invoice_number, status, remark))
                self.current_settlement_id = c.lastrowid
                messagebox.showinfo("成功", "结算记录保存成功！")
            conn.commit()
            self.load_settlements()
        except Exception as e:
            messagebox.showerror("错误", f"保存结算记录失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def clear_settlement_form(self):
        self.settlement_order_combobox.set('')
        self.settlement_date_entry.delete(0, tk.END)
        self.settlement_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.settlement_amount_entry.delete(0, tk.END)
        self.settlement_paid_entry.delete(0, tk.END)
        self.settlement_paid_entry.insert(0, "0")
        self.settlement_invoice_entry.delete(0, tk.END)
        self.settlement_status_combobox.current(0)
        self.settlement_remark_text.delete("1.0", tk.END)
        self.current_settlement_id = None


    def on_settlement_select(self, event):
        selected = self.settlement_tree.selection()
        if selected:
            item = self.settlement_tree.item(selected)
            settlement_id, order_id, customer_name, settlement_date, amount, paid, status = item['values']
            self.current_settlement_id = settlement_id
            self.settlement_order_combobox.set(f"订单{order_id}")
            self.settlement_date_entry.delete(0, tk.END)
            self.settlement_date_entry.insert(0, settlement_date)
            self.settlement_amount_entry.delete(0, tk.END)
            self.settlement_amount_entry.insert(0, amount)
            self.settlement_paid_entry.delete(0, tk.END)
            self.settlement_paid_entry.insert(0, paid)
            # 获取发票编号和备注
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            c.execute('''SELECT sr.invoice_number, sr.remark
                         FROM settlement_records sr
                         WHERE sr.id=?''', (settlement_id,))
            result = c.fetchone()
            conn.close()
            if result:
                invoice_number, remark = result
                self.settlement_invoice_entry.delete(0, tk.END)
                self.settlement_invoice_entry.insert(0, invoice_number)
                self.settlement_remark_text.delete("1.0", tk.END)
                self.settlement_remark_text.insert("1.0", remark)
            self.settlement_status_combobox.set(status)
        else:
            self.clear_settlement_form()


    def load_settlements(self):
        for item in self.settlement_tree.get_children():
            self.settlement_tree.delete(item)
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT sr.id, o.id as order_id, c.customer_name, sr.settlement_date,
                             sr.settlement_amount, sr.paid_amount, sr.status
                     FROM settlement_records sr
                     JOIN orders o ON sr.order_id = o.id
                     JOIN customers c ON o.customer_id = c.id
                     ORDER BY sr.settlement_date DESC''')
        for row in c.fetchall():
            self.settlement_tree.insert('', 'end', values=row)
        conn.close()

