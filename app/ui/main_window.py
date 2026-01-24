
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json
import os

from app.services.account_manager import AccountManager
from app.services.browser_service import BrowserService
from app.services.auth_service import AuthService
from app.ui.rounded_button import RoundedButton
from app.ui.screens.account_screen import AccountScreen
from app.ui.screens.video_screen import VideoScreen
from app.ui.screens.image_screen import ImageScreen
from app.ui.screens.login_screen import LoginScreen
from app.ui.screens.profile_screen import ProfileScreen

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
        self.max_jobs_per_account = 4 # Default
        
        # Image State
        self.image_job_queue = []
        self.is_image_running = False
        
        self.thumbnail_cache = {} 

        # UI Resources
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        self.frames = {}
        self.screens = {}
        
        # Check Auth
        if self.auth_service.load_token():
            self.check_auth_and_redirect()
        else:
            self.show_login()

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
                self.login_screen.lbl_msg.config(text=str(msg))

    def setup_main_interface(self):
        for w in self.root.winfo_children(): w.destroy()
        
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)
        
        # Sidebar
        self.sidebar = tk.Frame(self.main_container, bg="#2c3e50", width=220)
        self.sidebar.pack(side="left", fill="y", ipadx=5)
        
        tk.Label(self.sidebar, text="🤖 Labs Tool", bg="#2c3e50", fg="white", font=("Segoe UI", 18, "bold")).pack(pady=30)
        
        self.btn_acc = RoundedButton(self.sidebar, text="Quản lý Tài khoản", command=lambda: self.show_view("account"), width=180, height=40, bg_color="#2c3e50", fg_color="#34495e", hover_color="#1abc9c")
        self.btn_acc.pack(pady=5)
        
        self.btn_vid = RoundedButton(self.sidebar, text="Tạo Video (Batch)", command=lambda: self.show_view("video"), width=180, height=40, bg_color="#2c3e50", fg_color="#2c3e50", hover_color="#1abc9c")
        self.btn_vid.pack(pady=5)
        
        self.btn_img = RoundedButton(self.sidebar, text="Tạo Ảnh (Batch)", command=lambda: self.show_view("image"), width=180, height=40, bg_color="#2c3e50", fg_color="#2c3e50", hover_color="#1abc9c")
        self.btn_img.pack(pady=5)
        
        self.btn_profile = RoundedButton(self.sidebar, text="Profile & License", command=lambda: self.show_view("profile"), width=180, height=40, bg_color="#2c3e50", fg_color="#2c3e50", hover_color="#1abc9c")
        self.btn_profile.pack(pady=5)
        
        # Content Area
        self.content_area = tk.Frame(self.main_container, bg="white")
        self.content_area.pack(side="left", fill="both", expand=True)
        
        # Initialize Screens
        self.frames["account"] = tk.Frame(self.content_area, bg="white")
        self.screens["account"] = AccountScreen(self.frames["account"], self)
        
        self.frames["video"] = tk.Frame(self.content_area, bg="white")
        self.screens["video"] = VideoScreen(self.frames["video"], self)
        
        self.frames["image"] = tk.Frame(self.content_area, bg="white")
        self.screens["image"] = ImageScreen(self.frames["image"], self)
        
        self.frames["profile"] = tk.Frame(self.content_area, bg="white")
        self.screens["profile"] = ProfileScreen(self.frames["profile"], self)
        
        self.show_view("account")

    def show_view(self, name):
        buttons = {
            "account": self.btn_acc, 
            "video": self.btn_vid, 
            "image": self.btn_img,
            "profile": self.btn_profile
        }
        
        for key, btn in buttons.items():
            color = "#34495e" if key == name else "#2c3e50"
            btn.itemconfig(btn.rect, fill=color, outline=color)
            btn.fg_color = color
            
            if key in self.frames:
                if key == name:
                    self.frames[key].pack(fill="both", expand=True)
                    if key == "account": self.screens["account"].refresh_ui()
                    if key == "profile": self.screens["profile"].setup_ui() # Refresh profile
                else:
                    self.frames[key].pack_forget()

    def show_setup_guide(self):
        msg = """
        Hướng dẫn Setup:
        1. Cài đặt Python 3.12+
        2. Cài Chrome
        3. Lấy Cookie từ Labs.google bằng EditThisCookie:
           - Login Labs
           - Click Extension -> Export (Clipboard)
           - Vào App -> Thêm Cookie -> Paste
        4. Để tạo Video/Ảnh:
           - Chuẩn bị file Excel (.xlsx)
           - Cột 'prompt': Nội dung Text
           - Cột 'image': Đường dẫn ảnh (Nếu muốn Image-to-Video/Image)
        """
        messagebox.showinfo("Hướng dẫn", msg)
