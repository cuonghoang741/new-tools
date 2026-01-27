
import customtkinter as ctk
from tkinter import messagebox
import threading
import json
import os

from app.services.account_manager import AccountManager
from app.services.browser_service import BrowserService
from app.services.auth_service import AuthService
from app.ui.screens.account_screen import AccountScreen
from app.ui.screens.video_screen import VideoScreen
from app.ui.screens.image_screen import ImageScreen
from app.ui.screens.login_screen import LoginScreen
from app.ui.screens.profile_screen import ProfileScreen

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Labs Automation - Batch Mode")
        self.root.geometry("1400x800")
        
        # Services
        self.account_manager = AccountManager()
        self.browser_service = BrowserService()
        self.auth_service = AuthService()
        
        # Shared State
        self.lock = threading.Lock()
        
        # Video State
        self.job_queue = []
        self.running_jobs = {} 
        self.is_running = False
        self.max_jobs_per_account = 4
        
        # Image State
        self.image_job_queue = []
        self.is_image_running = False
        
        self.thumbnail_cache = {}
        
        self.frames = {}
        self.screens = {}
        self.current_view = None
        
        # Check Auth
        if self.auth_service.load_token():
            self.check_auth_and_redirect()
        else:
            self.show_login()
            
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Bạn có muốn thoát ứng dụng?"):
            self.is_running = False
            self.is_image_running = False
            try:
                print("Closing all browser sessions...")
                self.browser_service.close_all_sessions()
            except: pass
            self.root.destroy()

    def show_login(self):
        for w in self.root.winfo_children(): w.destroy()
        self.frames = {}
        self.screens = {}
        self.login_screen = LoginScreen(self.root, self)

    def check_auth_and_redirect(self):
        print("Checking license...")
        valid, msg = self.auth_service.check_license()
        print(f"License Status: {valid}, Msg: {msg}")
        
        if valid:
            self.root.after(10, self.setup_main_interface)
        else:
            self.auth_service.logout()
            self.show_login()
            if hasattr(self, 'login_screen'):
                self.login_screen.lbl_msg.configure(text=str(msg))

    def setup_main_interface(self):
        for w in self.root.winfo_children(): w.destroy()
        
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True)
        
        # Sidebar with gradient-like effect
        self.sidebar = ctk.CTkFrame(self.main_container, width=240, corner_radius=0, fg_color="#1a1a2e")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # Logo Section
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(30, 40), padx=20)
        
        ctk.CTkLabel(logo_frame, text="🤖", font=("Segoe UI Emoji", 36)).pack()
        ctk.CTkLabel(logo_frame, text="Labs Tool Pro", font=("SF Pro Display", 22, "bold"), text_color="#ffffff").pack()
        ctk.CTkLabel(logo_frame, text="Batch Automation", font=("SF Pro Display", 11), text_color="#6c7293").pack()
        
        # Navigation Buttons
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=15)
        
        self.nav_buttons = {}
        nav_items = [
            ("account", "👥", "Tài khoản"),
            ("video", "🎬", "Tạo Video"),
            ("image", "✨", "Tạo Ảnh"),
            ("profile", "⚙️", "Cài đặt")
        ]
        
        for key, icon, text in nav_items:
            btn = ctk.CTkButton(
                nav_frame, 
                text=f"  {icon}  {text}",
                font=("SF Pro Display", 13),
                height=45,
                corner_radius=12,
                fg_color="transparent",
                text_color="#a0a3bd",
                hover_color="#16213e",
                anchor="w",
                command=lambda k=key: self.show_view(k)
            )
            btn.pack(fill="x", pady=3)
            self.nav_buttons[key] = btn
        
        # Version info at bottom
        version_label = ctk.CTkLabel(
            self.sidebar, 
            text="v2.0.0 • Dark Mode", 
            font=("SF Pro Display", 10), 
            text_color="#4a4a6a"
        )
        version_label.pack(side="bottom", pady=20)
        
        # Content Area
        self.content_area = ctk.CTkFrame(self.main_container, fg_color="#0f0f23", corner_radius=0)
        self.content_area.pack(side="left", fill="both", expand=True)
        
        # Initialize Screens
        self.frames["account"] = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.screens["account"] = AccountScreen(self.frames["account"], self)
        
        self.frames["video"] = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.screens["video"] = VideoScreen(self.frames["video"], self)
        
        self.frames["image"] = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.screens["image"] = ImageScreen(self.frames["image"], self)
        
        self.frames["profile"] = ctk.CTkFrame(self.content_area, fg_color="transparent")
        self.screens["profile"] = ProfileScreen(self.frames["profile"], self)
        
        self.show_view("account")

    def show_view(self, name):
        # Update nav button states
        for key, btn in self.nav_buttons.items():
            if key == name:
                btn.configure(fg_color="#6366f1", text_color="#ffffff", hover_color="#5855eb")
            else:
                btn.configure(fg_color="transparent", text_color="#a0a3bd", hover_color="#16213e")
        
        # Show/hide frames
        for key in self.frames:
            if key == name:
                self.frames[key].pack(fill="both", expand=True, padx=20, pady=20)
                if key == "account": self.screens["account"].refresh_ui()
                if key == "profile": self.screens["profile"].setup_ui()
            else:
                self.frames[key].pack_forget()
        
        self.current_view = name

    def show_setup_guide(self):
        msg = """
        Hướng dẫn thêm tài khoản:
        
        1. Tải Extension hỗ trợ từ Google Drive (link trong phần hướng dẫn chi tiết).
        2. Mở trình duyệt, vào phần quản lý Extensions, bật "Developer Mode".
        3. Kéo thả file extension vừa tải vào để cài đặt.
        4. Truy cập https://labs.google/fx/vi/tools/flow và đăng nhập.
        5. Mở Extension vừa cài, click "Copy JSON" để lấy cookie.
        6. Quay lại App -> Tab Tài khoản -> Bấm "➕ Thêm Cookie" và dán vào.
        
        Để tạo Video/Ảnh:
        - Chuẩn bị file Excel (.xlsx) với cột 'prompt' (và 'image' nếu cần).
        """
        messagebox.showinfo("Hướng dẫn", msg)
