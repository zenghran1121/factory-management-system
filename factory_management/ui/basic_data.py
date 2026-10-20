import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class BasicDataMixin:

    def create_basic_data_tab(self):
        # 标签页容器
        notebook = ttk.Notebook(self.tab_basic)

        # 产品/物料管理
        frame_materials = ttk.Frame(notebook)
        notebook.add(frame_materials, text='产品/物料管理')
        self.create_materials_subtab(frame_materials)

        # 产品-组件关联管理
        frame_components = ttk.Frame(notebook)
        notebook.add(frame_components, text='产品-组件关联')
        self.create_components_subtab(frame_components)

        # 客户管理
        frame_customers = ttk.Frame(notebook)
        notebook.add(frame_customers, text='客户管理')
        self.create_customers_subtab(frame_customers)

        # 仓库管理
        frame_warehouses = ttk.Frame(notebook)
        notebook.add(frame_warehouses, text='仓库管理')
        self.create_warehouses_subtab(frame_warehouses)

        notebook.pack(expand=1, fill='both')


    def create_materials_subtab(self, parent):
        # 表单区域
        form_frame = ttk.LabelFrame(parent, text="产品/物料信息")
        form_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        ttk.Label(form_frame, text="物料编码:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.material_code_entry = ttk.Entry(form_frame)
        self.material_code_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="物料名称:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.material_name_entry = ttk.Entry(form_frame)
        self.material_name_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="物料类型:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.material_type_combobox = ttk.Combobox(form_frame, state="readonly")
        self.material_type_combobox.grid(row=2, column=1, padx=5, pady=5)
        self.load_material_types()

        ttk.Label(form_frame, text="父级物料:").grid(row=3, column=0, padx=5, pady=5, sticky='w')
        self.parent_material_combobox = ttk.Combobox(form_frame, state="readonly")
        self.parent_material_combobox.grid(row=3, column=1, padx=5, pady=5)
        self.load_parent_materials()

        ttk.Label(form_frame, text="单位:").grid(row=4, column=0, padx=5, pady=5, sticky='w')
        self.material_unit_entry = ttk.Entry(form_frame)
        self.material_unit_entry.grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="重量(kg):").grid(row=5, column=0, padx=5, pady=5, sticky='w')
        self.material_weight_entry = ttk.Entry(form_frame)
        self.material_weight_entry.grid(row=5, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="规格型号:").grid(row=6, column=0, padx=5, pady=5, sticky='w')
        self.material_spec_entry = ttk.Entry(form_frame)
        self.material_spec_entry.grid(row=6, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="材质:").grid(row=7, column=0, padx=5, pady=5, sticky='w')
        self.material_material_entry = ttk.Entry(form_frame)
        self.material_material_entry.grid(row=7, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="尺寸规格:").grid(row=8, column=0, padx=5, pady=5, sticky='w')
        self.material_size_entry = ttk.Entry(form_frame)
        self.material_size_entry.grid(row=8, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="描述:").grid(row=9, column=0, padx=5, pady=5, sticky='nw')
        self.material_desc_text = tk.Text(form_frame, height=3, width=30)
        self.material_desc_text.grid(row=9, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=10, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="保存物料", command=self.save_material).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_material_form).grid(row=0, column=1, padx=5)

        # 列表区域
        list_frame = ttk.LabelFrame(parent, text="物料列表")
        list_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky='nsew')

        self.materials_tree = ttk.Treeview(list_frame, columns=('ID', '编码', '名称', '类型', '父级', '单位', '重量', '规格', '材质', '尺寸'), show='headings')
        self.materials_tree.heading('ID', text='ID')
        self.materials_tree.heading('编码', text='物料编码')
        self.materials_tree.heading('名称', text='物料名称')
        self.materials_tree.heading('类型', text='物料类型')
        self.materials_tree.heading('父级', text='父级物料')
        self.materials_tree.heading('单位', text='单位')
        self.materials_tree.heading('重量', text='重量(kg)')
        self.materials_tree.heading('规格', text='规格型号')
        self.materials_tree.heading('材质', text='材质')
        self.materials_tree.heading('尺寸', text='尺寸规格')
        self.materials_tree.column('ID', width=50)
        self.materials_tree.column('编码', width=120)
        self.materials_tree.column('名称', width=150)
        self.materials_tree.column('类型', width=80)
        self.materials_tree.column('父级', width=150)
        self.materials_tree.column('单位', width=60)
        self.materials_tree.column('重量', width=80)
        self.materials_tree.column('规格', width=120)
        self.materials_tree.column('材质', width=100)
        self.materials_tree.column('尺寸', width=120)
        self.materials_tree.bind('<<TreeviewSelect>>', self.on_material_select)
        self.materials_tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.materials_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.materials_tree.configure(yscrollcommand=scrollbar.set)

        # 导入按钮
        ttk.Button(parent, text="从Excel导入物料", command=self.import_materials_from_excel).grid(row=1, column=0, padx=10, pady=5, sticky='w')

        self.load_materials()


    def load_material_types(self):
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute("SELECT id, type_name FROM material_types")
        types = c.fetchall()
        self.material_types_dict = {name: id for id, name in types}
        self.material_type_combobox['values'] = list(self.material_types_dict.keys())
        if types:
            self.material_type_combobox.current(0)
        conn.close()


    def load_parent_materials(self):
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute("SELECT id, material_name FROM materials WHERE type_id IN (SELECT id FROM material_types WHERE type_name='成品' OR type_name='组件')")
        materials = c.fetchall()
        self.parent_materials_dict = {name: id for id, name in materials}
        self.parent_material_combobox['values'] = ['无'] + list(self.parent_materials_dict.keys())
        self.parent_material_combobox.current(0)
        conn.close()


    def save_material(self):
        code = self.material_code_entry.get().strip()
        name = self.material_name_entry.get().strip()
        type_name = self.material_type_combobox.get()
        parent_name = self.parent_material_combobox.get()
        unit = self.material_unit_entry.get().strip()
        weight = self.material_weight_entry.get().strip()
        spec = self.material_spec_entry.get().strip()
        material = self.material_material_entry.get().strip()
        size = self.material_size_entry.get().strip()
        desc = self.material_desc_text.get("1.0", tk.END).strip()

        if not code or not name or not type_name or not unit:
            messagebox.showwarning("警告", "物料编码、名称、类型、单位不能为空！")
            return

        type_id = self.material_types_dict[type_name]
        parent_id = self.parent_materials_dict.get(parent_name) if parent_name != '无' else None

        try:
            weight = float(weight) if weight else 0.0
        except ValueError:
            messagebox.showwarning("警告", "重量必须是数字！")
            return

        try:
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            # 检查是否已存在
            c.execute("SELECT id FROM materials WHERE material_code=?", (code,))
            existing_id = c.fetchone()
            if existing_id:
                # 更新
                c.execute('''UPDATE materials SET material_name=?, type_id=?, parent_id=?, unit=?, weight=?, spec=?, material=?, size=?, description=?
                             WHERE material_code=?''',
                          (name, type_id, parent_id, unit, weight, spec, material, size, desc, code))
                messagebox.showinfo("成功", "物料信息更新成功！")
            else:
                # 新增
                c.execute('''INSERT INTO materials (material_code, material_name, type_id, parent_id, unit, weight, spec, material, size, description)
                             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                          (code, name, type_id, parent_id, unit, weight, spec, material, size, desc))
                messagebox.showinfo("成功", "物料信息保存成功！")
            conn.commit()
            self.clear_material_form()
            self.load_materials()
            self.load_parent_materials()  # 刷新父级物料列表
            self.load_products_for_combobox()  # 刷新产品列表
            self.load_components_for_combobox()  # 刷新组件列表
        except Exception as e:
            messagebox.showerror("错误", f"保存物料失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def clear_material_form(self):
        self.material_code_entry.delete(0, tk.END)
        self.material_name_entry.delete(0, tk.END)
        self.material_type_combobox.current(0)
        self.parent_material_combobox.current(0)
        self.material_unit_entry.delete(0, tk.END)
        self.material_weight_entry.delete(0, tk.END)
        self.material_spec_entry.delete(0, tk.END)
        self.material_material_entry.delete(0, tk.END)
        self.material_size_entry.delete(0, tk.END)
        self.material_desc_text.delete("1.0", tk.END)
        self.materials_tree.selection_remove(self.materials_tree.selection())


    def on_material_select(self, event):
        selected = self.materials_tree.selection()
        if selected:
            item = self.materials_tree.item(selected)
            material_id, code, name, type_name, parent_name, unit, weight, spec, material, size = item['values']
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            c.execute('''SELECT m.description, t.type_name, p.material_name
                         FROM materials m
                         LEFT JOIN material_types t ON m.type_id = t.id
                         LEFT JOIN materials p ON m.parent_id = p.id
                         WHERE m.id=?''', (material_id,))
            result = c.fetchone()
            conn.close()
            if result:
                desc, type_name, parent_name = result
                self.material_code_entry.delete(0, tk.END)
                self.material_code_entry.insert(0, code)
                self.material_name_entry.delete(0, tk.END)
                self.material_name_entry.insert(0, name)
                self.material_type_combobox.set(type_name)
                self.parent_material_combobox.set(parent_name if parent_name else '无')
                self.material_unit_entry.delete(0, tk.END)
                self.material_unit_entry.insert(0, unit)
                self.material_weight_entry.delete(0, tk.END)
                self.material_weight_entry.insert(0, str(weight))
                self.material_spec_entry.delete(0, tk.END)
                self.material_spec_entry.insert(0, spec)
                self.material_material_entry.delete(0, tk.END)
                self.material_material_entry.insert(0, material)
                self.material_size_entry.delete(0, tk.END)
                self.material_size_entry.insert(0, size)
                self.material_desc_text.delete("1.0", tk.END)
                self.material_desc_text.insert("1.0", desc)


    def load_materials(self):
        for item in self.materials_tree.get_children():
            self.materials_tree.delete(item)
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT m.id, m.material_code, m.material_name, t.type_name, 
                         COALESCE(p.material_name, '无') as parent_name, m.unit,
                         m.weight, m.spec, m.material, m.size
                     FROM materials m
                     JOIN material_types t ON m.type_id = t.id
                     LEFT JOIN materials p ON m.parent_id = p.id
                     ORDER BY t.type_name, m.material_name''')
        for row in c.fetchall():
            self.materials_tree.insert('', 'end', values=row)
        conn.close()


    def import_materials_from_excel(self, file_path=None):
        if file_path is None:
            file_path = filedialog.askopenfilename(filetypes=[("Excel文件", "*.xlsx;*.xls")])
        if not file_path:
            return
        try:
            df = pd.read_excel(file_path)
            required_columns = ['物料编码', '物料名称', '物料类型', '单位']
            if not all(col in df.columns for col in required_columns):
                messagebox.showerror("错误", "Excel文件格式不正确，必须包含'物料编码'、'物料名称'、'物料类型'和'单位'列！")
                return

            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            success_count = 0
            error_count = 0
            for _, row in df.iterrows():
                code = str(row['物料编码']).strip()
                name = str(row['物料名称']).strip()
                type_name = str(row['物料类型']).strip()
                unit = str(row['单位']).strip()
                parent_name = str(row.get('父级物料', '无')).strip()
                weight = str(row.get('重量', '')).strip()
                spec = str(row.get('规格型号', '')).strip()
                material = str(row.get('材质', '')).strip()
                size = str(row.get('尺寸规格', '')).strip()
                desc = str(row.get('描述', '')).strip()

                if not code or not name or not type_name or not unit:
                    error_count += 1
                    continue

                # 检查物料类型是否存在
                c.execute("SELECT id FROM material_types WHERE type_name=?", (type_name,))
                type_id = c.fetchone()
                if not type_id:
                    c.execute("INSERT INTO material_types (type_name) VALUES (?)", (type_name,))
                    type_id = c.lastrowid
                else:
                    type_id = type_id[0]

                # 检查父级物料是否存在
                parent_id = None
                if parent_name != '无':
                    c.execute("SELECT id FROM materials WHERE material_name=?", (parent_name,))
                    parent_result = c.fetchone()
                    if parent_result:
                        parent_id = parent_result[0]

                try:
                    weight = float(weight) if weight else 0.0
                except ValueError:
                    weight = 0.0

                try:
                    c.execute('''INSERT INTO materials
                                 (material_code, material_name, type_id, parent_id, unit, weight, spec, material, size, description)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                 ON CONFLICT(material_code) DO UPDATE SET
                                   material_name=excluded.material_name, type_id=excluded.type_id,
                                   parent_id=excluded.parent_id, unit=excluded.unit, weight=excluded.weight,
                                   spec=excluded.spec, material=excluded.material, size=excluded.size,
                                   description=excluded.description''',
                              (code, name, type_id, parent_id, unit, weight, spec, material, size, desc))
                    success_count += 1
                except Exception as e:
                    error_count += 1
            conn.commit()
            messagebox.showinfo("导入结果", f"成功导入 {success_count} 条物料信息，{error_count} 条数据因格式错误或重复已跳过。")
            self.load_materials()
            self.load_parent_materials()
            self.load_products_for_combobox()
            self.load_components_for_combobox()
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def create_components_subtab(self, parent):
        # 表单区域
        form_frame = ttk.LabelFrame(parent, text="产品-组件关联")
        form_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        ttk.Label(form_frame, text="产品:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.product_combobox = ttk.Combobox(form_frame, state="readonly")
        self.product_combobox.grid(row=0, column=1, padx=5, pady=5)
        self.load_products_for_combobox()

        ttk.Label(form_frame, text="组件:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.component_combobox = ttk.Combobox(form_frame, state="readonly")
        self.component_combobox.grid(row=1, column=1, padx=5, pady=5)
        self.load_components_for_combobox()

        ttk.Label(form_frame, text="数量:").grid(row=2, column=0, padx=5, pady=5, sticky='w')
        self.component_quantity_entry = ttk.Entry(form_frame)
        self.component_quantity_entry.grid(row=2, column=1, padx=5, pady=5)
        self.component_quantity_entry.insert(0, "1")

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="保存关联", command=self.save_product_component).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_component_form).grid(row=0, column=1, padx=5)

        # 列表区域
        list_frame = ttk.LabelFrame(parent, text="产品-组件关联列表")
        list_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky='nsew')

        self.components_tree = ttk.Treeview(list_frame, columns=('ID', '产品', '组件', '数量'), show='headings')
        self.components_tree.heading('ID', text='ID')
        self.components_tree.heading('产品', text='产品名称')
        self.components_tree.heading('组件', text='组件名称')
        self.components_tree.heading('数量', text='每个产品需要的组件数量')
        self.components_tree.column('ID', width=50)
        self.components_tree.column('产品', width=200)
        self.components_tree.column('组件', width=200)
        self.components_tree.column('数量', width=150)
        self.components_tree.bind('<<TreeviewSelect>>', self.on_component_select)
        self.components_tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.components_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.components_tree.configure(yscrollcommand=scrollbar.set)

        self.load_product_components()


    def load_products_for_combobox(self):
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT m.id, m.material_name 
                     FROM materials m
                     JOIN material_types t ON m.type_id = t.id
                     WHERE t.type_name='成品'
                     ORDER BY m.material_name''')
        products = c.fetchall()
        self.products_dict = {name: id for id, name in products}
        self.product_combobox['values'] = list(self.products_dict.keys())
        conn.close()


    def load_components_for_combobox(self):
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT m.id, m.material_name 
                     FROM materials m
                     JOIN material_types t ON m.type_id = t.id
                     WHERE t.type_name='组件'
                     ORDER BY m.material_name''')
        components = c.fetchall()
        self.components_dict = {name: id for id, name in components}
        self.component_combobox['values'] = list(self.components_dict.keys())
        conn.close()


    def save_product_component(self):
        product_name = self.product_combobox.get()
        component_name = self.component_combobox.get()
        quantity_text = self.component_quantity_entry.get().strip()

        if not product_name or not component_name or not quantity_text:
            messagebox.showwarning("警告", "产品、组件和数量不能为空！")
            return

        try:
            quantity = int(quantity_text)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("警告", "数量必须是正整数！")
            return

        product_id = self.products_dict[product_name]
        component_id = self.components_dict[component_name]

        try:
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            # 检查是否已存在该关联
            c.execute("SELECT id FROM product_components WHERE product_id=? AND component_id=?", (product_id, component_id))
            existing_id = c.fetchone()
            if existing_id:
                # 更新
                c.execute('''UPDATE product_components SET quantity=?
                             WHERE id=?''',
                          (quantity, existing_id[0]))
                messagebox.showinfo("成功", "产品-组件关联更新成功！")
            else:
                # 新增
                c.execute('''INSERT INTO product_components (product_id, component_id, quantity)
                             VALUES (?, ?, ?)''',
                          (product_id, component_id, quantity))
                messagebox.showinfo("成功", "产品-组件关联保存成功！")
            conn.commit()
            self.load_product_components()
            self.clear_component_form()
        except Exception as e:
            messagebox.showerror("错误", f"保存关联失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def clear_component_form(self):
        self.product_combobox.set('')
        self.component_combobox.set('')
        self.component_quantity_entry.delete(0, tk.END)
        self.component_quantity_entry.insert(0, "1")
        self.components_tree.selection_remove(self.components_tree.selection())


    def on_component_select(self, event):
        selected = self.components_tree.selection()
        if selected:
            item = self.components_tree.item(selected)
            relation_id, product_name, component_name, quantity = item['values']
            self.product_combobox.set(product_name)
            self.component_combobox.set(component_name)
            self.component_quantity_entry.delete(0, tk.END)
            self.component_quantity_entry.insert(0, quantity)


    def load_product_components(self):
        for item in self.components_tree.get_children():
            self.components_tree.delete(item)
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute('''SELECT pc.id, p.material_name as product_name, c.material_name as component_name, pc.quantity
                     FROM product_components pc
                     JOIN materials p ON pc.product_id = p.id
                     JOIN materials c ON pc.component_id = c.id
                     ORDER BY p.material_name, c.material_name''')
        for row in c.fetchall():
            self.components_tree.insert('', 'end', values=row)
        conn.close()


    def create_customers_subtab(self, parent):
        # 表单区域
        form_frame = ttk.LabelFrame(parent, text="客户信息")
        form_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        ttk.Label(form_frame, text="客户名称:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.customer_name_entry = ttk.Entry(form_frame)
        self.customer_name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="联系方式:").grid(row=1, column=0, padx=5, pady=5, sticky='nw')
        self.customer_contact_text = tk.Text(form_frame, height=3, width=30)
        self.customer_contact_text.grid(row=1, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="保存客户", command=self.save_customer).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_customer_form).grid(row=0, column=1, padx=5)

        # 列表区域
        list_frame = ttk.LabelFrame(parent, text="客户列表")
        list_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky='nsew')

        self.customers_tree = ttk.Treeview(list_frame, columns=('ID', '名称', '联系方式'), show='headings')
        self.customers_tree.heading('ID', text='ID')
        self.customers_tree.heading('名称', text='客户名称')
        self.customers_tree.heading('联系方式', text='联系方式')
        self.customers_tree.column('ID', width=50)
        self.customers_tree.column('名称', width=200)
        self.customers_tree.column('联系方式', width=200)
        self.customers_tree.bind('<<TreeviewSelect>>', self.on_customer_select)
        self.customers_tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.customers_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.customers_tree.configure(yscrollcommand=scrollbar.set)

        # 导入按钮
        ttk.Button(parent, text="从Excel导入客户", command=self.import_customers_from_excel).grid(row=1, column=0, padx=10, pady=5, sticky='w')

        self.load_customers()


    def save_customer(self):
        name = self.customer_name_entry.get().strip()
        contact = self.customer_contact_text.get("1.0", tk.END).strip()

        if not name:
            messagebox.showwarning("警告", "客户名称不能为空！")
            return

        try:
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            # 检查是否已存在
            c.execute("SELECT id FROM customers WHERE customer_name=?", (name,))
            existing_id = c.fetchone()
            if existing_id:
                # 更新
                c.execute("UPDATE customers SET contact_info=? WHERE customer_name=?", (contact, name))
                messagebox.showinfo("成功", "客户信息更新成功！")
            else:
                # 新增
                c.execute("INSERT INTO customers (customer_name, contact_info) VALUES (?, ?)", (name, contact))
                messagebox.showinfo("成功", "客户信息保存成功！")
            conn.commit()
            self.clear_customer_form()
            self.load_customers()
            self.load_customers_for_combobox()  # 刷新订单管理中的客户列表
        except Exception as e:
            messagebox.showerror("错误", f"保存客户失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def clear_customer_form(self):
        self.customer_name_entry.delete(0, tk.END)
        self.customer_contact_text.delete("1.0", tk.END)
        self.customers_tree.selection_remove(self.customers_tree.selection())


    def on_customer_select(self, event):
        selected = self.customers_tree.selection()
        if selected:
            item = self.customers_tree.item(selected)
            customer_id, name, contact = item['values']
            self.customer_name_entry.delete(0, tk.END)
            self.customer_name_entry.insert(0, name)
            self.customer_contact_text.delete("1.0", tk.END)
            self.customer_contact_text.insert("1.0", contact)


    def load_customers(self):
        for item in self.customers_tree.get_children():
            self.customers_tree.delete(item)
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute("SELECT id, customer_name, contact_info FROM customers ORDER BY customer_name")
        for row in c.fetchall():
            self.customers_tree.insert('', 'end', values=row)
        conn.close()


    def import_customers_from_excel(self, file_path=None):
        if file_path is None:
            file_path = filedialog.askopenfilename(filetypes=[("Excel文件", "*.xlsx;*.xls")])
        if not file_path:
            return
        try:
            df = pd.read_excel(file_path)
            required_columns = ['客户名称']
            if not all(col in df.columns for col in required_columns):
                messagebox.showerror("错误", "Excel文件格式不正确，必须包含'客户名称'列！")
                return

            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            success_count = 0
            error_count = 0
            for _, row in df.iterrows():
                name = str(row['客户名称']).strip()
                contact = str(row.get('联系方式', '')).strip()

                if not name:
                    error_count += 1
                    continue

                try:
                    c.execute("""INSERT INTO customers (customer_name, contact_info) VALUES (?, ?)
                                 ON CONFLICT(customer_name) DO UPDATE SET contact_info=excluded.contact_info""", (name, contact))
                    success_count += 1
                except Exception as e:
                    error_count += 1
            conn.commit()
            messagebox.showinfo("导入结果", f"成功导入 {success_count} 条客户信息，{error_count} 条数据因格式错误或重复已跳过。")
            self.load_customers()
            self.load_customers_for_combobox()
        except Exception as e:
            messagebox.showerror("错误", f"导入失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def create_warehouses_subtab(self, parent):
        # 表单区域
        form_frame = ttk.LabelFrame(parent, text="仓库信息")
        form_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        ttk.Label(form_frame, text="仓库名称:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.warehouse_name_entry = ttk.Entry(form_frame)
        self.warehouse_name_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(form_frame, text="位置:").grid(row=1, column=0, padx=5, pady=5, sticky='w')
        self.warehouse_location_entry = ttk.Entry(form_frame)
        self.warehouse_location_entry.grid(row=1, column=1, padx=5, pady=5)

        btn_frame = ttk.Frame(form_frame)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=10)
        ttk.Button(btn_frame, text="保存仓库", command=self.save_warehouse).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="清空", command=self.clear_warehouse_form).grid(row=0, column=1, padx=5)

        # 列表区域
        list_frame = ttk.LabelFrame(parent, text="仓库列表")
        list_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky='nsew')

        self.warehouses_tree = ttk.Treeview(list_frame, columns=('ID', '名称', '位置'), show='headings')
        self.warehouses_tree.heading('ID', text='ID')
        self.warehouses_tree.heading('名称', text='仓库名称')
        self.warehouses_tree.heading('位置', text='位置')
        self.warehouses_tree.column('ID', width=50)
        self.warehouses_tree.column('名称', width=200)
        self.warehouses_tree.column('位置', width=200)
        self.warehouses_tree.bind('<<TreeviewSelect>>', self.on_warehouse_select)
        self.warehouses_tree.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.warehouses_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.warehouses_tree.configure(yscrollcommand=scrollbar.set)

        self.load_warehouses()


    def save_warehouse(self):
        name = self.warehouse_name_entry.get().strip()
        location = self.warehouse_location_entry.get().strip()

        if not name:
            messagebox.showwarning("警告", "仓库名称不能为空！")
            return

        try:
            conn = None
            conn = self.connect_db()
            c = conn.cursor()
            # 检查是否已存在
            c.execute("SELECT id FROM warehouses WHERE warehouse_name=?", (name,))
            existing_id = c.fetchone()
            if existing_id:
                # 更新
                c.execute("UPDATE warehouses SET location=? WHERE warehouse_name=?", (location, name))
                messagebox.showinfo("成功", "仓库信息更新成功！")
            else:
                # 新增
                c.execute("INSERT INTO warehouses (warehouse_name, location) VALUES (?, ?)", (name, location))
                messagebox.showinfo("成功", "仓库信息保存成功！")
            conn.commit()
            self.clear_warehouse_form()
            self.load_warehouses()
            self.load_warehouses_for_combobox()  # 刷新库存管理中的仓库列表
            self.load_warehouses_for_schedule_combobox()  # 刷新生产排程中的仓库列表
        except Exception as e:
            messagebox.showerror("错误", f"保存仓库失败：{str(e)}")
        finally:
            if conn is not None:
                conn.close()


    def clear_warehouse_form(self):
        self.warehouse_name_entry.delete(0, tk.END)
        self.warehouse_location_entry.delete(0, tk.END)
        self.warehouses_tree.selection_remove(self.warehouses_tree.selection())


    def on_warehouse_select(self, event):
        selected = self.warehouses_tree.selection()
        if selected:
            item = self.warehouses_tree.item(selected)
            warehouse_id, name, location = item['values']
            self.warehouse_name_entry.delete(0, tk.END)
            self.warehouse_name_entry.insert(0, name)
            self.warehouse_location_entry.delete(0, tk.END)
            self.warehouse_location_entry.insert(0, location)


    def load_warehouses(self):
        for item in self.warehouses_tree.get_children():
            self.warehouses_tree.delete(item)
        conn = None
        conn = self.connect_db()
        c = conn.cursor()
        c.execute("SELECT id, warehouse_name, location FROM warehouses ORDER BY warehouse_name")
        for row in c.fetchall():
            self.warehouses_tree.insert('', 'end', values=row)
        conn.close()

