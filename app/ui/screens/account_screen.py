
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
import threading
from app.ui.rounded_button import RoundedButton
from app.services.api_service import LabsApiService

class AccountScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        toolbar = tk.Frame(self.parent, bg="#ecf0f1", pady=15)
        toolbar.pack(fill="x")
        
        RoundedButton(toolbar, text="➕ Thêm Cookie", command=self.add_new_account, width=120, height=35, bg_color="#ecf0f1", fg_color="#27ae60", hover_color="#2ecc71").pack(side="left", padx=15)
        RoundedButton(toolbar, text="🔃 Refresh", command=self.refresh_ui, width=100, height=35, bg_color="#ecf0f1", fg_color="#3498db", hover_color="#5dade2").pack(side="left", padx=5)
        RoundedButton(toolbar, text="ℹ Hướng dẫn", command=self.app.show_setup_guide, width=110, height=35, bg_color="#ecf0f1", fg_color="#9b59b6", hover_color="#8e44ad").pack(side="left", padx=5)

        self.canvas = tk.Canvas(self.parent, bg="white", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.parent, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="white")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self.scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        self.refresh_ui()

    def refresh_ui(self, check_live=True):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        accounts = self.app.account_manager.accounts
        
        if not accounts:
            self.create_empty_state()
            return
        
        for idx, acc in enumerate(accounts):
            self.create_account_card(idx, acc)
            
        if check_live:
            threading.Thread(target=self.run_auto_check, daemon=True).start()

    def run_auto_check(self):
        if getattr(self, '_checking', False): return
        self._checking = True
        
        try:
            # Delegate to AccountManager
            changed = self.app.account_manager.check_all_live()
            
            if changed:
                self.app.root.after(0, lambda: self.refresh_ui(check_live=False))
                
        finally:
            self._checking = False
    
    def create_empty_state(self):
        empty_frame = tk.Frame(self.scrollable_frame, bg="white", padx=30, pady=40)
        empty_frame.pack(fill="both", expand=True)
        
        tk.Label(empty_frame, text="🍪", font=("Segoe UI", 48), bg="white").pack(pady=(20, 10))
        tk.Label(empty_frame, text="Chưa có tài khoản nào!", font=("Segoe UI", 16, "bold"), bg="white", fg="#2c3e50").pack(pady=(0, 20))
        
        instr_card = tk.Frame(empty_frame, bg="#f8f9fa", padx=25, pady=20, highlightbackground="#e0e0e0", highlightthickness=1)
        instr_card.pack(fill="x", pady=10)
        
        tk.Label(instr_card, text="📌 Hướng dẫn thêm tài khoản:", font=("Segoe UI", 12, "bold"), bg="#f8f9fa", fg="#2c3e50").pack(anchor="w", pady=(0, 15))
        
        steps = [
            "1. Mở trình duyệt, đăng nhập vào labs.google",
            "2. Cài đặt extension 'EditThisCookie'",
            "3. Mở extension -> Click biểu tượng 'Export' (⬆)",
            "4. Quay lại app này, bấm nút '➕ Thêm Cookie' và dán vào"
        ]
        
        for step in steps:
            tk.Label(instr_card, text=step, font=("Segoe UI", 10), bg="#f8f9fa", fg="#34495e").pack(anchor="w", pady=2)

    def create_account_card(self, idx, acc):
        card = tk.Frame(self.scrollable_frame, bg="#fdfdfd", bd=1, relief="solid", padx=15, pady=10)
        card.pack(fill="x", pady=5)
        
        # Header: Name + Status
        header = tk.Frame(card, bg="#fdfdfd")
        header.pack(fill="x")
        
        name = acc.get('name', f"Account {idx+1}")
        tk.Label(header, text=name, font=("Segoe UI", 11, "bold"), bg="#fdfdfd", fg="#2c3e50").pack(side="left")
        
        status = acc.get('status', 'Unknown')
        color = "#27ae60" if "Live" in status else "#e74c3c" if "Die" in status else "#95a5a6"
        tk.Label(header, text=f"• {status}", font=("Segoe UI", 10, "bold"), bg="#fdfdfd", fg=color).pack(side="right")
        
        # Info
        if acc.get('project_id'):
            tk.Label(card, text=f"Project ID: {acc['project_id']}", fg="#7f8c8d", bg="#fdfdfd", font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 0))
        
        action_frame = tk.Frame(card, bg="#fdfdfd")
        action_frame.pack(fill="x", pady=(15, 0))
        
        RoundedButton(action_frame, text="Browser", command=lambda: self.open_browser(idx), width=80, height=30, bg_color="#fdfdfd", fg_color="#34495e", hover_color="#5D6D7E").pack(side="left", padx=2)
        RoundedButton(action_frame, text="Check", command=lambda: self.check_cookie(idx), width=80, height=30, bg_color="#fdfdfd", fg_color="#3498db", hover_color="#2980b9").pack(side="left", padx=2)
        RoundedButton(action_frame, text="Delete", command=lambda: self.delete_account(idx), width=60, height=30, bg_color="#fdfdfd", fg_color="#e74c3c", hover_color="#c0392b").pack(side="right", padx=2)

    def add_new_account(self):
        win = tk.Toplevel(self.app.root)
        win.title("Thêm Cookie")
        win.geometry("600x450")
        win.configure(bg="white")
        
        tk.Label(win, text="Dán JSON Cookie vào bên dưới:", bg="white", font=("Segoe UI", 10)).pack(pady=10, padx=20, anchor="w")
        txt = scrolledtext.ScrolledText(win, font=("Consolas", 9))
        txt.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        def save():
            raw = txt.get("1.0", tk.END).strip()
            if not raw: return
            
            def process():
                try:
                    api = LabsApiService()
                    api.set_credentials(raw)
                    
                    token = api.fetch_access_token()
                    if not token: raise Exception("Không lấy được Access Token!")

                    pid = api.create_project()
                    if not pid: raise Exception("Không tạo được Project ID!")
                    
                    # Check Live immediately
                    valid, msg = api.check_cookie()
                    status = "Live" if valid else "Die"
                    
                    self.app.account_manager.add_account(raw, token, pid)
                    
                    # Update status manually
                    with self.app.lock:
                        if self.app.account_manager.accounts:
                            self.app.account_manager.accounts[-1]['status'] = status
                            self.app.account_manager.save_accounts()
                            
                    self.app.root.after(0, lambda: [self.refresh_ui(), win.destroy(), messagebox.showinfo("Success", "Thêm tài khoản thành công!")])
                    
                except Exception as e:
                    self.app.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                    
            threading.Thread(target=process, daemon=True).start()
            
        RoundedButton(win, text="Lưu & Lấy Token", command=save, width=150, height=40, bg_color="white", fg_color="#27ae60").pack(pady=10)

    def delete_account(self, idx):
        if messagebox.askyesno("Confirm", "Delete this account?"):
            self.app.account_manager.delete_account(idx)
            self.refresh_ui()

    def open_browser(self, idx):
        acc = self.app.account_manager.get_account(idx)
        threading.Thread(target=lambda: self.app.browser_service.launch_browser(json.dumps(acc['cookies'])), daemon=True).start()

    def check_cookie(self, idx):
        acc = self.app.account_manager.get_account(idx)
        def run():
            try:
                api = LabsApiService()
                api.set_credentials(json.dumps(acc['cookies']), acc.get('access_token'))
                if not api.auth_token:
                    t = api.fetch_access_token()
                    if t: acc['access_token'] = t
                
                if not acc.get('project_id'):
                     pid = api.create_project()
                     if pid: acc['project_id'] = pid

                valid, msg = api.check_cookie()
                acc['status'] = "Live" if valid else "Die"
                if valid and "Credits" in msg: acc['status'] += f" ({msg.split('Credits: ')[1][:-1]})"
                
                self.app.account_manager.save_accounts()
                self.app.root.after(0, self.refresh_ui)
            except: pass
        threading.Thread(target=run, daemon=True).start()
