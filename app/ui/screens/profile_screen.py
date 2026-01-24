
import tkinter as tk
from datetime import datetime
from app.ui.rounded_button import RoundedButton

class ProfileScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        # Clear existing widgets to avoid duplication
        for w in self.parent.winfo_children(): w.destroy()
        
        user = self.app.auth_service.user_info
        if not user:
            tk.Label(self.parent, text="No User Info. Please Re-login.", bg="white").pack(expand=True)
            return
            
        pkg_data = user.get('activePackage', {}) or {}
        pkg = pkg_data.get('package', {}) or {}
        
        container = tk.Frame(self.parent, bg="white")
        container.pack(fill="both", expand=True)
        
        card = tk.LabelFrame(container, text="👤 Thông tin tài khoản", font=("Segoe UI", 12, "bold"), bg="white", padx=20, pady=20)
        card.place(relx=0.5, rely=0.3, anchor="center", width=500)
        
        # User Info
        grid_frame = tk.Frame(card, bg="white")
        grid_frame.pack(fill="x", pady=10)
        
        labels = [
            ("Tên:", user.get('name', 'N/A')),
            ("Email:", user.get('email', 'N/A')),
            ("Gói cước:", pkg.get('name', 'Không có gói')),
            ("Mô tả:", pkg.get('description', '')),
            ("Hết hạn:", self.format_date(pkg_data.get('endDate', 'N/A')))
        ]
        
        for i, (label, val) in enumerate(labels):
            tk.Label(grid_frame, text=label, font=("Segoe UI", 10, "bold"), bg="white", fg="#7f8c8d").grid(row=i, column=0, sticky="w", pady=5)
            tk.Label(grid_frame, text=str(val), font=("Segoe UI", 10), bg="white", fg="#2c3e50").grid(row=i, column=1, sticky="w", padx=10, pady=5)
            
        # Logout
        RoundedButton(card, text="Đăng xuất", command=self.do_logout, width=150, height=35, bg_color="white", fg_color="#e74c3c", hover_color="#c0392b").pack(pady=20)

    def format_date(self, date_str):
        if not date_str or date_str == 'N/A': return "N/A"
        try:
            # ISO '2027-01-24T...' -> '24/01/2027'
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%d/%m/%Y")
        except: return date_str

    def do_logout(self):
        self.app.auth_service.logout()
        self.app.show_login()
