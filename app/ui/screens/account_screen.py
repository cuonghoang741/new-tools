
import customtkinter as ctk
from tkinter import messagebox
import json
import threading
import webbrowser
from app.services.api_service import LabsApiService

class AccountScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        # Header Section
        header = ctk.CTkFrame(self.parent, fg_color="transparent", height=60)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header, 
            text="Quản lý Tài khoản", 
            font=("SF Pro Display", 22, "bold"),
            text_color="#ffffff"
        ).pack(side="left")
        
        # Action Buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(
            btn_frame,
            text="➕ Thêm",
            font=("SF Pro Display", 12, "bold"),
            width=100,
            height=38,
            corner_radius=10,
            fg_color="#22c55e",
            hover_color="#16a34a",
            command=self.add_new_account
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 Refresh",
            font=("SF Pro Display", 12),
            width=105,
            height=38,
            corner_radius=10,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self.refresh_ui
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="❓ Hướng dẫn",
            font=("SF Pro Display", 12),
            width=120,
            height=38,
            corner_radius=10,
            fg_color="#8b5cf6",
            hover_color="#7c3aed",
            command=self.app.show_setup_guide
        ).pack(side="left", padx=5)
        
        # Scrollable Account List
        self.scroll_frame = ctk.CTkScrollableFrame(
            self.parent, 
            fg_color="transparent",
            scrollbar_button_color="#3a3a5e",
            scrollbar_button_hover_color="#4a4a7e"
        )
        self.scroll_frame.pack(fill="both", expand=True)
        
        self.refresh_ui()

    def refresh_ui(self, check_live=True):
        for widget in self.scroll_frame.winfo_children():
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
            changed = self.app.account_manager.check_all_live()
            if changed:
                self.app.root.after(0, lambda: self.refresh_ui(check_live=False))
        finally:
            self._checking = False
    
    def create_empty_state(self):
        empty_frame = ctk.CTkFrame(self.scroll_frame, fg_color="#1a1a2e", corner_radius=20)
        empty_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        inner = ctk.CTkFrame(empty_frame, fg_color="transparent")
        inner.pack(expand=True, pady=60)
        
        ctk.CTkLabel(inner, text="🍪", font=("Segoe UI Emoji", 64)).pack(pady=(0, 15))
        ctk.CTkLabel(
            inner, 
            text="Chưa có tài khoản nào!", 
            font=("SF Pro Display", 20, "bold"),
            text_color="#ffffff"
        ).pack(pady=(0, 10))
        ctk.CTkLabel(
            inner, 
            text="Thêm cookie để bắt đầu sử dụng", 
            font=("SF Pro Display", 13),
            text_color="#6c7293"
        ).pack(pady=(0, 30))
        
        # Instructions Card
        instr_card = ctk.CTkFrame(inner, fg_color="#16213e", corner_radius=16)
        instr_card.pack(fill="x", padx=40, pady=10)
        
        instr_inner = ctk.CTkFrame(instr_card, fg_color="transparent")
        instr_inner.pack(fill="x", padx=25, pady=20)
        
        ctk.CTkLabel(
            instr_inner, 
            text="📌 Hướng dẫn nhanh:", 
            font=("SF Pro Display", 13, "bold"),
            text_color="#ffffff",
            anchor="w"
        ).pack(fill="x", pady=(0, 15))
        
        steps = [
            ("1. Tải Extension tại đây", "https://drive.google.com/file/d/1JgF9JO-Mdj7j7aqYsLp-Vwu4ShHpwr1u/view"),
            ("2. Bật 'Developer Mode' → Kéo thả file để cài", None),
            ("3. Vào labs.google và đăng nhập", "https://labs.google/fx/vi/tools/flow"),
            ("4. Mở Extension → Copy JSON → Dán vào App", None)
        ]
        
        for text, link in steps:
            step_frame = ctk.CTkFrame(instr_inner, fg_color="transparent")
            step_frame.pack(fill="x", pady=3)
            
            if link:
                lbl = ctk.CTkLabel(
                    step_frame, 
                    text=f"🔗 {text}", 
                    font=("SF Pro Display", 11),
                    text_color="#6366f1",
                    cursor="hand2"
                )
                lbl.pack(side="left")
                lbl.bind("<Button-1>", lambda e, url=link: webbrowser.open(url))
            else:
                ctk.CTkLabel(
                    step_frame, 
                    text=f"   {text}", 
                    font=("SF Pro Display", 11),
                    text_color="#a0a3bd"
                ).pack(side="left")

    def create_account_card(self, idx, acc):
        card = ctk.CTkFrame(
            self.scroll_frame, 
            fg_color="#1a1a2e", 
            corner_radius=16,
            border_width=1,
            border_color="#2a2a4e"
        )
        card.pack(fill="x", pady=6)
        
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=20, pady=15)
        
        # Left side - Info
        info_frame = ctk.CTkFrame(inner, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)
        
        # Name row
        name_row = ctk.CTkFrame(info_frame, fg_color="transparent")
        name_row.pack(fill="x")
        
        name = acc.get('name', f"Account {idx+1}")
        ctk.CTkLabel(
            name_row, 
            text=name, 
            font=("SF Pro Display", 14, "bold"),
            text_color="#ffffff"
        ).pack(side="left")
        
        # Status Badge
        status = acc.get('status', 'Unknown')
        if "Live" in status:
            badge_color = "#22c55e"
            badge_text = f"● {status}"
        elif "Die" in status:
            badge_color = "#ef4444"
            badge_text = f"● {status}"
        else:
            badge_color = "#6c7293"
            badge_text = f"● {status}"
        
        status_badge = ctk.CTkLabel(
            name_row,
            text=badge_text,
            font=("SF Pro Display", 11, "bold"),
            text_color=badge_color
        )
        status_badge.pack(side="left", padx=15)
        
        # Project ID
        if acc.get('project_id'):
            ctk.CTkLabel(
                info_frame, 
                text=f"Project: {acc['project_id'][:20]}...", 
                font=("SF Pro Display", 11),
                text_color="#6c7293"
            ).pack(anchor="w", pady=(5, 0))
        
        # Right side - Actions
        action_frame = ctk.CTkFrame(inner, fg_color="transparent")
        action_frame.pack(side="right")
        
        ctk.CTkButton(
            action_frame,
            text="🌐",
            width=40,
            height=35,
            corner_radius=8,
            fg_color="#374151",
            hover_color="#4b5563",
            font=("Segoe UI Emoji", 14),
            command=lambda: self.open_browser(idx)
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            action_frame,
            text="🔄",
            width=40,
            height=35,
            corner_radius=8,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            font=("Segoe UI Emoji", 14),
            command=lambda: self.check_cookie(idx)
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            action_frame,
            text="🗑️",
            width=40,
            height=35,
            corner_radius=8,
            fg_color="#ef4444",
            hover_color="#dc2626",
            font=("Segoe UI Emoji", 14),
            command=lambda: self.delete_account(idx)
        ).pack(side="left", padx=3)

    def add_new_account(self):
        win = ctk.CTkToplevel(self.app.root)
        win.title("Thêm Cookie")
        win.geometry("600x500")
        win.configure(fg_color="#0f0f23")
        win.transient(self.app.root)
        win.grab_set()
        
        # Center the window
        win.after(10, lambda: win.focus_force())
        
        container = ctk.CTkFrame(win, fg_color="#1a1a2e", corner_radius=20)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        
        inner = ctk.CTkFrame(container, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=25, pady=25)
        
        ctk.CTkLabel(
            inner, 
            text="🍪 Thêm Cookie mới", 
            font=("SF Pro Display", 18, "bold"),
            text_color="#ffffff"
        ).pack(anchor="w", pady=(0, 5))
        
        ctk.CTkLabel(
            inner, 
            text="Dán JSON Cookie từ Extension vào bên dưới", 
            font=("SF Pro Display", 12),
            text_color="#6c7293"
        ).pack(anchor="w", pady=(0, 15))
        
        self.txt_cookie = ctk.CTkTextbox(
            inner, 
            height=280,
            corner_radius=12,
            fg_color="#16213e",
            text_color="#ffffff",
            font=("Consolas", 11),
            border_width=1,
            border_color="#2a2a4e"
        )
        self.txt_cookie.pack(fill="both", expand=True, pady=(0, 15))
        
        btn_frame = ctk.CTkFrame(inner, fg_color="transparent")
        btn_frame.pack(fill="x")
        
        self.btn_save = ctk.CTkButton(
            btn_frame,
            text="💾 Lưu & Lấy Token",
            font=("SF Pro Display", 13, "bold"),
            height=45,
            corner_radius=10,
            fg_color="#22c55e",
            hover_color="#16a34a",
            command=lambda: self.save_cookie(win)
        )
        self.btn_save.pack(side="right")
        
        ctk.CTkButton(
            btn_frame,
            text="Hủy",
            font=("SF Pro Display", 13),
            height=45,
            corner_radius=10,
            fg_color="#374151",
            hover_color="#4b5563",
            command=win.destroy
        ).pack(side="right", padx=10)

    def save_cookie(self, win):
        raw = self.txt_cookie.get("1.0", "end").strip()
        if not raw: return
        
        self.btn_save.configure(text="⏳ Đang xử lý...", state="disabled", fg_color="#4a4a6a")
        
        def process():
            try:
                api = LabsApiService()
                api.set_credentials(raw)
                
                token = api.fetch_access_token()
                if not token: raise Exception("Không lấy được Access Token!")

                pid = api.create_project()
                if not pid: raise Exception("Không tạo được Project ID!")
                
                valid, msg = api.check_cookie()
                status = "Live" if valid else "Die"
                
                self.app.account_manager.add_account(raw, token, pid)
                
                with self.app.lock:
                    if self.app.account_manager.accounts:
                        self.app.account_manager.accounts[-1]['status'] = status
                        self.app.account_manager.save_accounts()
                        
                self.app.root.after(0, lambda: [self.refresh_ui(), win.destroy(), messagebox.showinfo("Success", "✅ Thêm tài khoản thành công!")])
                
            except Exception as e:
                def show_error():
                    messagebox.showerror("Error", str(e))
                    self.btn_save.configure(text="💾 Lưu & Lấy Token", state="normal", fg_color="#22c55e")
                self.app.root.after(0, show_error)
                
        threading.Thread(target=process, daemon=True).start()

    def delete_account(self, idx):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa tài khoản này?"):
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
