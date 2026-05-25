import pandas as pd
import tkinter as tk
from tkinter import messagebox, filedialog, ttk, simpledialog
from datetime import datetime, timedelta
import os
import sys
import json

class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ALI SYS PRO 4")
        self.root.geometry("850x950")
        self.root.configure(bg="#f0f2f5")
        
        # إعداد مسار ملف حفظ الإعدادات
        user_docs = os.path.expanduser("~/Documents")
        self.db_file = os.path.join(user_docs, "ali_inventory_settings.json")
        
        try:
            icon_path = self.resource_path("logo.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
            
        self.master_df = None  
        self.stock_df = None   
        self.plants = []
        self.last_master_path = ""
        self.last_stock_path = ""
        
        # تحميل البيانات المحفوظة
        self.load_all_data()
        
        self.unit_options = ["AU", "BAG", "BOX", "CAR", "G", "KG", "M", "ML", "PAC", "PC"]
        self.order_options = {
            "500000 Customer Service": "500000", "500001 Fruit and vegetable": "500001",
            "500002 Deli section": "500002", "500003 General sections": "500003",
            "500004 Branch Office": "500004"
        }

        # ميزة الدخول المباشر
        if self.can_auto_enter():
            self.auto_load_and_start()
        else:
            self.init_load_screen()

    def can_auto_enter(self):
        return (self.last_master_path and os.path.exists(self.last_master_path) and 
                self.last_stock_path and os.path.exists(self.last_stock_path))

    def auto_load_and_start(self):
        try:
            self.process_master_logic(self.last_master_path, silent=True)
            self.process_stock_logic(self.last_stock_path, silent=True)
            if self.master_df is not None and self.stock_df is not None:
                self.build_main_ui()
                self.update_dashboards()
        except:
            self.init_load_screen()

    def save_all_data(self):
        data = {
            "purchase": self.scanned_purchase,
            "internal": self.scanned_internal,
            "damage": self.scanned_damage,
            "recipe": self.scanned_recipe,
            "master_path": self.last_master_path,
            "stock_path": self.last_stock_path
        }
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_all_data(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.scanned_purchase = data.get("purchase", [])
                    self.scanned_internal = data.get("internal", [])
                    self.scanned_damage = data.get("damage", [])
                    self.scanned_recipe = data.get("recipe", [])
                    self.last_master_path = data.get("master_path", "")
                    self.last_stock_path = data.get("stock_path", "")
            except:
                self.reset_lists()
        else:
            self.reset_lists()

    def reset_lists(self):
        self.scanned_purchase, self.scanned_internal = [], []
        self.scanned_damage, self.scanned_recipe = [], []

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def init_load_screen(self):
        self.load_frame = tk.Frame(self.root, bg="#f0f2f5")
        self.load_frame.place(relx=0.5, rely=0.4, anchor='center')
        
        tk.Label(self.load_frame, text="📦 ALI SYSTEM PRO", font=('Arial', 22, 'bold'), bg="#f0f2f5", fg="#001f3f").pack(pady=10)
        self.btn_master = tk.Button(self.load_frame, text="1️⃣ تحميل ملف الباركودات (EXPORT BARCODE)", font=('Arial', 11, 'bold'), 
                                   bg="#6c757d", fg="white", width=40, pady=12, command=self.load_master)
        self.btn_master.pack(pady=10)
        self.btn_stock = tk.Button(self.load_frame, text="2️⃣ تحميل ملف المخزون (Stock Status)", font=('Arial', 11, 'bold'), 
                                  bg="#6c757d", fg="white", width=40, pady=12, state="disabled", command=self.load_stock)
        self.btn_stock.pack(pady=10)

    def load_master(self, silent=False):
        f = filedialog.askopenfilename(title="اختر ملف EXPORT", filetypes=[("Excel Files", "*.xlsx *.xls *.csv")])
        if f: self.process_master_logic(f, silent)

    def process_master_logic(self, f, silent):
        try:
            self.master_df = pd.read_excel(f) if f.endswith('x') else pd.read_csv(f)
            self.master_df = self.master_df.astype(str).apply(lambda x: x.str.strip())
            self.last_master_path = f
            self.save_all_data()
            if not silent:
                self.btn_master.config(bg="#28a745", text="✅ تم تحميل ملف الباركودات")
                self.btn_stock.config(state="normal", bg="#007bff")
        except Exception as e: messagebox.showerror("خطأ", f"فشل تحميل ملف الباركودات: {e}")

    def load_stock(self, silent=False):
        f = filedialog.askopenfilename(title="اختر ملف Stock Status", filetypes=[("Excel Files", "*.xlsx *.xls *.csv")])
        if f: self.process_stock_logic(f, silent)

    def process_stock_logic(self, f, silent):
        try:
            self.stock_df = pd.read_excel(f, header=[0, 1], dtype=str) if f.endswith('x') else pd.read_csv(f, header=[0, 1], dtype=str)
            self.stock_df.iloc[:, 0] = self.stock_df.iloc[:, 0].str.strip().replace(r'\.0$', '', regex=True)
            self.plants = sorted(list(set([str(c[0]).strip() for c in self.stock_df.columns if str(c[0]).strip().isdigit()])))
            self.last_stock_path = f
            self.save_all_data()
            if not silent:
                if hasattr(self, 'load_frame'): self.load_frame.destroy()
                self.build_main_ui()
                self.update_dashboards()
        except Exception as e: messagebox.showerror("خطأ", f"فشل تحميل ملف المخزون:\n{e}")

    def build_main_ui(self):
        top_bar = tk.Frame(self.root, bg="#001f3f", pady=5)
        top_bar.pack(fill='x')
        tk.Button(top_bar, text="🔄 تحديث الباركودات", font=('Arial', 8), command=lambda: self.load_master(True)).pack(side='left', padx=10)
        tk.Button(top_bar, text="🔄 تحديث المخزون", font=('Arial', 8), command=lambda: self.load_stock(True)).pack(side='left')
        tk.Button(top_bar, text="🗑️ مسح القوائم", font=('Arial', 8), bg="#dc3545", fg="white", command=self.clear_saved_lists).pack(side='right', padx=10)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        self.tabs = {"purchase": tk.Frame(self.notebook), "internal": tk.Frame(self.notebook), "damage": tk.Frame(self.notebook), "recipe": tk.Frame(self.notebook)}
        self.notebook.add(self.tabs["purchase"], text=" Purchase Req ")
        self.notebook.add(self.tabs["internal"], text=" Internal Sale ")
        self.notebook.add(self.tabs["damage"], text=" Damage Issue ")
        self.notebook.add(self.tabs["recipe"], text=" Recipe Issue ")
        for m, frame in self.tabs.items(): self.setup_tab_content(frame, m)

    def setup_tab_content(self, parent, mode_type):
        dash_frame = tk.Frame(parent, pady=10)
        dash_frame.pack(fill='x', padx=10)
        parent.cards = {}
        card_configs = [("Items", "#007bff", "عدد الأصناف"), ("Orders", "#28a745", "TOTAL ORDER"), ("Vendors", "#fd7e14", "عدد الموردين")]
        for key, color, label in card_configs:
            f = tk.Frame(dash_frame, bg=color, width=150, height=65, padx=10, pady=5)
            f.pack(side='left', expand=True, fill='both', padx=5)
            f.pack_propagate(False)
            tk.Label(f, text=label, fg="white", bg=color, font=('Arial', 9, 'bold')).pack()
            lbl = tk.Label(f, text="0", fg="white", bg=color, font=('Arial', 16, 'bold'))
            lbl.pack(); parent.cards[key] = lbl

        top_f = tk.LabelFrame(parent, text=" الإعدادات ", padx=15, pady=10)
        top_f.pack(fill='x', padx=20, pady=5)
        p_combo = ttk.Combobox(top_f, values=self.plants, state="readonly", width=12)
        p_combo.pack(side='left', padx=5); p_combo.current(0) if self.plants else None
        
        parent.date_entry = None
        if mode_type == "internal":
            tk.Label(top_f, text="📅 التاريخ:", font=('Arial', 9)).pack(side='left', padx=(15, 2))
            parent.date_entry = tk.Entry(top_f, width=12, font=('Arial', 10), justify='center')
            parent.date_entry.insert(0, datetime.now().strftime('%d.%m.%Y'))
            parent.date_entry.pack(side='left', padx=5)

        s_mode = tk.StringVar(value="barcode")
        m_frame = tk.Frame(top_f); m_frame.pack(side='right')
        modes = [("Barcode", "barcode"), ("SAP", "sap"), ("Orion", "orion")]
        if mode_type == "damage": modes.insert(0, ("Short", "short"))
        for t, v in modes: tk.Radiobutton(m_frame, text=t, variable=s_mode, value=v).pack(side='left', padx=2)
        
        entry_box = tk.Entry(parent, font=('Arial', 18), bg="#e8f0fe", justify='center')
        entry_box.pack(fill='x', padx=30, pady=10)
        
        disp_f = tk.LabelFrame(parent, text=" تفاصيل الصنف "); disp_f.pack(fill='both', expand=True, padx=20, pady=5)
        res_labels = {}
        for key, txt in [('SAP', 'SAP Code:'), ('Name', 'Description:'), ('Supplier', 'Supplier Name:'), ('Factor', 'Factor:'), ('Stock', 'Live Stock:'), ('Avg', 'Average Sales:')]:
            tk.Label(disp_f, text=txt, fg="#666", font=('Arial', 9)).pack(anchor='w', padx=5)
            lbl = tk.Label(disp_f, text="-", font=('Arial', 11, 'bold'), bg="#fff", anchor='w', padx=10, relief='sunken')
            lbl.pack(fill='x', pady=2); res_labels[key] = lbl
        
        parent.months_frame = tk.Frame(disp_f, bg="#ffffff"); parent.months_frame.pack(fill='x', pady=5, padx=5)
        u_combo = ttk.Combobox(disp_f, values=self.unit_options, font=('Arial', 12)); u_combo.pack(fill='x', pady=5)
        qty_box = tk.Entry(disp_f, font=('Arial', 24, 'bold'), justify='center', bg="#fffef0"); qty_box.pack(fill='x', pady=5)
        
        o_cb = None
        if mode_type in ["internal", "damage", "recipe"]:
            o_cb = ttk.Combobox(disp_f, values=list(self.order_options.keys()), state="readonly")
            o_cb.pack(fill='x', pady=5); o_cb.current(0)
            
        btn_f = tk.Frame(parent); btn_f.pack(fill='x', padx=20, pady=10)
        tk.Button(btn_f, text="حفظ (Enter)", bg="#001f3f", fg="white", font=('Arial', 12, 'bold'), width=15, height=2,
                  command=lambda: self.add_item(mode_type, res_labels, u_combo, entry_box, qty_box, p_combo, o_cb, parent.date_entry)).pack(side='left', expand=True, fill='x', padx=5)
        
        tk.Button(btn_f, text="CLEAR", bg="#6c757d", fg="white", font=('Arial', 12, 'bold'), width=10,
                  command=lambda: self.clear_fields(entry_box, qty_box, u_combo, res_labels)).pack(side='left', padx=5)
        
        entry_box.bind('<Return>', lambda e: self.perform_search(entry_box, s_mode, p_combo, res_labels, u_combo, qty_box))
        qty_box.bind('<Return>', lambda e: self.add_item(mode_type, res_labels, u_combo, entry_box, qty_box, p_combo, o_cb, parent.date_entry))
        
        tk.Button(parent, text="🔎 Preview & Export List", bg="#28a745", fg="white", font=('Arial', 12, 'bold'), height=2,
                  command=lambda: self.show_preview(mode_type)).pack(fill='x', padx=20, pady=10)

    def perform_search(self, entry, s_mode, p_combo, labels, u_combo, next_f):
        val = entry.get().strip()
        mode, p_val = s_mode.get(), p_combo.get()
        current_tab = self.notebook.nametowidget(self.notebook.select())
        if mode == "short" and len(val) >= 6: val = val[2:6]
        try:
            sap_code = None
            if mode == "orion":
                col = next((col for col in self.stock_df.columns if 'Orion Item Code' in str(col).strip()), None)
                if col:
                    match_stock = self.stock_df[self.stock_df[col].astype(str).str.strip().replace(r'\.0$', '', regex=True) == val]
                    if not match_stock.empty: sap_code = str(match_stock.iloc[0, 0]).strip().replace('.0', '')
            else:
                search_col = 'Item Barcode' if mode in ["short", "barcode"] else 'Item Code'
                master_temp = self.master_df.copy()
                actual_col = next((c for c in master_temp.columns if search_col.lower() in str(c).lower()), search_col)
                master_temp[actual_col] = master_temp[actual_col].astype(str).str.strip().replace(r'\.0$', '', regex=True)
                match_master = master_temp[master_temp[actual_col] == val]
                if not match_master.empty: sap_code = str(match_master.iloc[0]['Item Code']).strip().replace('.0', '')

            if sap_code:
                row = self.master_df[self.master_df['Item Code'].astype(str).str.strip().replace(r'\.0$', '', regex=True) == sap_code].iloc[0]
                labels['SAP'].config(text=sap_code); labels['Name'].config(text=str(row['Item Name']))
                labels['Supplier'].config(text=str(row['Supplier Name'])); labels['Factor'].config(text=str(row['Factor']).split('.')[0])
                u_combo.set(str(row['UOM CODE'])); self.temp_supplier_id = str(row['Supplier']).split('.')[0]
                
                stock_match = self.stock_df[self.stock_df.iloc[:, 0].astype(str).str.strip().replace(r'\.0$', '', regex=True) == sap_code]
                for widget in current_tab.months_frame.winfo_children(): widget.destroy()
                if not stock_match.empty:
                    sales_cols = [c for c in self.stock_df.columns if "Total Sales" in str(c[0])]
                    v_list = []
                    for sc in sales_cols:
                        try:
                            num = float(stock_match.iloc[0][sc]); v_list.append(num)
                            card = tk.Frame(current_tab.months_frame, bg="#ffffff", bd=1, relief="ridge", highlightbackground="#28a745", highlightthickness=1)
                            card.pack(side='left', padx=4, expand=True, fill='both')
                            tk.Label(card, text=str(sc[1]).strip(), font=('Arial', 8, 'bold'), bg="#f8f9fa").pack(fill='x')
                            tk.Label(card, text=f"{num:g}", font=('Arial', 10, 'bold'), bg="#fff", fg="#28a745").pack(pady=2)
                        except: pass
                    avg_v = sum(v_list) / len(v_list) if v_list else 0
                    labels['Avg'].config(text=f"{avg_v:.3f}", fg="#28a745")
                    p_col = [c for c in self.stock_df.columns if str(c[0]).strip() == p_val]
                    if p_col:
                        s_val = str(stock_match.iloc[0][p_col[0]]).split('.')[0]
                        labels['Stock'].config(text=s_val)
                next_f.focus()
            else: messagebox.showwarning("تنبيه", "الصنف غير موجود")
        except Exception as e: print(f"Search Error: {e}")

    def add_item(self, mode, labels, u_combo, entry, qty_ent, p_combo, o_combo, date_ent=None):
        sap_code = labels['SAP'].cget("text")
        if sap_code == "-": return
        q_val = qty_ent.get().strip()
        if not q_val: return
        target_list = getattr(self, f"scanned_{mode}")
        
        for ex in target_list:
            if ex['SAP'] == sap_code:
                if messagebox.askyesno("صنف مكرر", f"الصنف {sap_code} موجود، دمج؟"):
                    ex['Qty'] = str(float(ex['Qty']) + float(q_val))
                    self.save_all_data(); self.clear_fields(entry, qty_ent, u_combo, labels); self.update_dashboards()
                return

        item = {"SAP": sap_code, "Unit": u_combo.get(), "Qty": q_val, "Plant": p_combo.get(), 
                "Supplier_ID": getattr(self, 'temp_supplier_id', ''), "Name": labels['Name'].cget("text")}
        if mode != "purchase": item["Order"] = self.order_options[o_combo.get()]
        if mode == "internal": item["Date"] = date_ent.get() if date_ent else datetime.now().strftime('%d.%m.%Y')
        
        target_list.append(item); self.save_all_data(); self.clear_fields(entry, qty_ent, u_combo, labels); self.update_dashboards()

    def clear_fields(self, entry, qty, u_combo, labels):
        entry.delete(0, 'end'); qty.delete(0, 'end'); entry.focus()
        for l in labels.values(): l.config(text="-", fg="black")
        try:
            current_tab = self.notebook.nametowidget(self.notebook.select())
            if hasattr(current_tab, 'months_frame'):
                for widget in current_tab.months_frame.winfo_children(): widget.destroy()
        except: pass

    def update_dashboards(self):
        for mode in ["purchase", "internal", "damage", "recipe"]:
            tab = self.tabs[mode]
            items = getattr(self, f"scanned_{mode}")
            tab.cards["Items"].config(text=str(len(items)))
            vendors = len(set([i.get('Supplier_ID', '') for i in items if i.get('Supplier_ID')]))
            if mode == "purchase":
                tab.cards["Orders"].config(text=str(vendors))
                tab.cards["Vendors"].config(text=str(vendors))
            else:
                tab.cards["Orders"].config(text=str(len(items)))
                tab.cards["Vendors"].config(text="-")

    def show_preview(self, mode):
        p_win = tk.Toplevel(self.root); p_win.title(f"Preview: {mode.upper()}")
        items = getattr(self, f"scanned_{mode}")
        if not items: 
            messagebox.showinfo("تنبيه", "القائمة فارغة"); p_win.destroy(); return
        tree = ttk.Treeview(p_win, columns=list(items[0].keys()), show='headings')
        for c in items[0].keys(): tree.heading(c, text=c); tree.column(c, width=100)
        tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        def refresh():
            for i in tree.get_children(): tree.delete(i)
            for it in items: tree.insert("", "end", values=list(it.values()))
        refresh()
        
        def on_edit(event):
            selected = tree.selection()
            if not selected: return
            idx = tree.index(selected[0])
            new_q = simpledialog.askstring("تعديل", f"كمية {items[idx]['Name']}:", initialvalue=items[idx]['Qty'])
            if new_q: items[idx]['Qty'] = new_q; self.save_all_data(); refresh()
        tree.bind("<Double-1>", on_edit)
        
        btn_f = tk.Frame(p_win); btn_f.pack(pady=10)
        tk.Button(btn_f, text="Excel تصدير", bg="#28a745", fg="white", command=lambda: self.export_final(mode, items, p_win, "xlsx")).pack(side='left', padx=5)
        tk.Button(btn_f, text="TXT تصدير", bg="#007bff", fg="white", command=lambda: self.export_final(mode, items, p_win, "txt")).pack(side='left', padx=5)
        tk.Button(btn_f, text="حذف المحدد", bg="#dc3545", fg="white", command=lambda: [items.pop(tree.index(tree.selection()[0])), self.save_all_data(), refresh(), self.update_dashboards()] if tree.selection() else None).pack(side='left', padx=5)

    def export_final(self, mode, items, win, file_type):
        ext = ".xlsx" if file_type == "xlsx" else ".txt"
        path = filedialog.asksaveasfilename(defaultextension=ext)
        if not path: return
        final_rows = []
        today = datetime.now()
        
        curr_idx = 0
        last_v = None
        
        for it in items:
            if mode == "internal":
                final_rows.append({
                    'SAP': it['SAP'], 'N1': '', 'N2': '', 'QUTY': it['Qty'], 'UNT': it['Unit'], 
                    'LOC': '1000', 'COST CNTER': it['Plant'], 'ORDER': it['Order'], 
                    'N3': '', 'N4': '', 'N5': '', 'N6': '', 'N7': '', 'MOV TYP': 'ZX1', 
                    'N9': '', 'N10': '', 'PLANT': it['Plant']
                })
            elif mode == "damage":
                final_rows.append({
                    'ITEM': it['SAP'], 'N1': '', 'N2': '', 'QUTY': it['Qty'], 'UON': it['Unit'], 
                    'LOC': '1000', 'PLANT_MAIN': it['Plant'], 'ORDER': it['Order'], 
                    'N3': '', 'N4': '', 'N5': '', 'N6': '', 'N7': '', 
                    'DAMAGE TYPE': 'Z51', 'N11': '', 'N12': '', 'PLANT': it['Plant']
                })
            elif mode == "recipe":
                final_rows.append({
                    'ITEM': it['SAP'], 'N1': '', 'N2': '', 'QUTY': it['Qty'], 'N3': '', 
                    'LOC': '1000', 'N4': '', 'N5': '', 'N6': '', 'MOV': '317', 
                    'N7': '', 'N8': '', 'PLANT': it['Plant']
                })
            elif mode == "purchase":
                if it['Supplier_ID'] != last_v: 
                    curr_idx += 1
                    last_v = it['Supplier_ID']
                
                try:
                    plant_num = int(it['Plant'])
                    p_grp_val = str(plant_num - 1000) if plant_num > 1000 else '104'
                except:
                    p_grp_val = '104'
                
                final_rows.append({
                    'Indicator': curr_idx, 
                    'Doc Type': 'ZLPO', 
                    'Vendor': it['Supplier_ID'], 
                    'P.Org': '1100', 
                    'P. Grp': p_grp_val, 
                    'Company Code': '1000', 
                    'Doc Date': today.strftime('%d.%m.%Y'), 
                    'Material': it['SAP'], 
                    'Quantity': it['Qty'], 
                    'UOM': it['Unit'], 
                    'Plant': it['Plant'], 
                    'Storage Location': '1000', 
                    'Delivery Date': (today + timedelta(days=2)).strftime('%d.%m.%Y'), 
                    'Return': ''
                })
        
        df = pd.DataFrame(final_rows)
        if file_type == "xlsx": df.to_excel(path, index=False)
        else: df.to_csv(path, sep='\t', index=False)
        items.clear(); self.save_all_data(); self.update_dashboards(); win.destroy(); messagebox.showinfo("نجاح", "تم التصدير بالهيكلية المطلوبة.")

    def clear_saved_lists(self):
        if messagebox.askyesno("تأكيد", "هل تريد مسح كافة القوائم؟"):
            self.reset_lists(); self.save_all_data(); self.update_dashboards()

if __name__ == "__main__":
    root = tk.Tk()
    app = InventoryApp(root)
    root.mainloop()