
import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox

class ProfileScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        # Clear existing widgets
        for w in self.parent.winfo_children(): w.destroy()
        
        user = self.app.auth_service.user_info
        if not user:
            # Error state
            error_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
            error_frame.pack(expand=True)
            ctk.CTkLabel(
                error_frame, 
                text="⚠️", 
                font=("Segoe UI Emoji", 48)
            ).pack(pady=(0, 15))
            ctk.CTkLabel(
                error_frame, 
                text="Không có thông tin người dùng", 
                font=("SF Pro Display", 16, "bold"),
                text_color="#ffffff"
            ).pack()
            ctk.CTkButton(
                error_frame,
                text="Đăng nhập lại",
                font=("SF Pro Display", 13),
                height=40,
                corner_radius=10,
                fg_color="#6366f1",
                hover_color="#5855eb",
                command=self.do_logout
            ).pack(pady=20)
            return
            
        pkg_data = user.get('activePackage', {}) or {}
        pkg = pkg_data.get('package', {}) or {}
        
        # Header
        header = ctk.CTkFrame(self.parent, fg_color="transparent", height=60)
        header.pack(fill="x", pady=(0, 20))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header, 
            text="⚙️ Cài đặt & Hồ sơ", 
            font=("SF Pro Display", 22, "bold"),
            text_color="#ffffff"
        ).pack(side="left")
        
        # Main content
        content = ctk.CTkFrame(self.parent, fg_color="transparent")
        content.pack(fill="both", expand=True)
        
        # Profile Card
        profile_card = ctk.CTkFrame(
            content, 
            fg_color="#1a1a2e", 
            corner_radius=20,
            border_width=1,
            border_color="#2a2a4e"
        )
        profile_card.pack(fill="x", pady=10)
        
        card_inner = ctk.CTkFrame(profile_card, fg_color="transparent")
        card_inner.pack(fill="x", padx=30, pady=25)
        
        # Avatar and name section
        avatar_section = ctk.CTkFrame(card_inner, fg_color="transparent")
        avatar_section.pack(fill="x", pady=(0, 20))
        
        # Avatar placeholder
        avatar = ctk.CTkFrame(
            avatar_section, 
            width=80, 
            height=80, 
            corner_radius=40,
            fg_color="#6366f1"
        )
        avatar.pack(side="left")
        avatar.pack_propagate(False)
        
        initial = user.get('name', 'U')[0].upper()
        ctk.CTkLabel(
            avatar, 
            text=initial, 
            font=("SF Pro Display", 32, "bold"),
            text_color="#ffffff"
        ).pack(expand=True)
        
        # Name and email
        info_section = ctk.CTkFrame(avatar_section, fg_color="transparent")
        info_section.pack(side="left", padx=20, fill="x", expand=True)
        
        ctk.CTkLabel(
            info_section, 
            text=user.get('name', 'N/A'), 
            font=("SF Pro Display", 18, "bold"),
            text_color="#ffffff",
            anchor="w"
        ).pack(fill="x")
        
        ctk.CTkLabel(
            info_section, 
            text=user.get('email', 'N/A'), 
            font=("SF Pro Display", 13),
            text_color="#6c7293",
            anchor="w"
        ).pack(fill="x", pady=(3, 0))
        
        # Divider
        ctk.CTkFrame(card_inner, height=1, fg_color="#2a2a4e").pack(fill="x", pady=15)
        
        # Package info
        package_section = ctk.CTkFrame(card_inner, fg_color="transparent")
        package_section.pack(fill="x")
        
        # Package name with badge
        pkg_row = ctk.CTkFrame(package_section, fg_color="transparent")
        pkg_row.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            pkg_row, 
            text="📦 Gói cước:", 
            font=("SF Pro Display", 13),
            text_color="#a0a3bd"
        ).pack(side="left")
        
        pkg_name = pkg.get('name', 'Không có gói')
        pkg_badge = ctk.CTkLabel(
            pkg_row,
            text=f"  {pkg_name}  ",
            font=("SF Pro Display", 12, "bold"),
            text_color="#ffffff",
            fg_color="#6366f1",
            corner_radius=6
        )
        pkg_badge.pack(side="left", padx=10)
        
        # Description
        if pkg.get('description'):
            desc_row = ctk.CTkFrame(package_section, fg_color="transparent")
            desc_row.pack(fill="x", pady=5)
            
            ctk.CTkLabel(
                desc_row, 
                text="📝 Mô tả:", 
                font=("SF Pro Display", 13),
                text_color="#a0a3bd"
            ).pack(side="left")
            
            ctk.CTkLabel(
                desc_row, 
                text=pkg.get('description', ''), 
                font=("SF Pro Display", 13),
                text_color="#ffffff"
            ).pack(side="left", padx=10)
        
        # Expiry
        exp_row = ctk.CTkFrame(package_section, fg_color="transparent")
        exp_row.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            exp_row, 
            text="⏰ Hết hạn:", 
            font=("SF Pro Display", 13),
            text_color="#a0a3bd"
        ).pack(side="left")
        
        exp_date = self.format_date(pkg_data.get('endDate', 'N/A'))
        exp_color = "#22c55e" if exp_date != "N/A" else "#ef4444"
        ctk.CTkLabel(
            exp_row, 
            text=exp_date, 
            font=("SF Pro Display", 13, "bold"),
            text_color=exp_color
        ).pack(side="left", padx=10)
        
        # Logout button
        logout_section = ctk.CTkFrame(card_inner, fg_color="transparent")
        logout_section.pack(fill="x", pady=(25, 0))
        
        ctk.CTkButton(
            logout_section,
            text="Đăng xuất",
            font=("SF Pro Display", 13, "bold"),
            height=45,
            corner_radius=10,
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self.do_logout
        ).pack(side="right")

    def format_date(self, date_str):
        if not date_str or date_str == 'N/A': return "N/A"
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%d/%m/%Y")
        except: return date_str

    def change_theme(self, new_theme):
        ctk.set_appearance_mode(new_theme.lower())

    def do_logout(self):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn đăng xuất?"):
            self.app.auth_service.logout()
            self.app.show_login()
