
import customtkinter as ctk
from tkinter import messagebox

class LoginScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        # Background gradient simulation
        self.parent.configure(fg_color="#0f0f23")
        
        # Center container with glass effect
        container = ctk.CTkFrame(
            self.parent, 
            width=420, 
            height=520,
            corner_radius=24,
            fg_color="#1a1a2e",
            border_width=1,
            border_color="#2a2a4e"
        )
        container.place(relx=0.5, rely=0.5, anchor="center")
        container.pack_propagate(False)
        
        # Inner padding frame
        inner = ctk.CTkFrame(container, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Logo/Icon
        ctk.CTkLabel(
            inner, 
            text="🤖", 
            font=("Segoe UI Emoji", 56)
        ).pack(pady=(10, 5))
        
        # Title
        ctk.CTkLabel(
            inner, 
            text="Trust Labs", 
            font=("SF Pro Display", 24, "bold"),
            text_color="#ffffff"
        ).pack(pady=(0, 5))
        
        ctk.CTkLabel(
            inner, 
            text="Sign in to continue", 
            font=("SF Pro Display", 12),
            text_color="#6c7293"
        ).pack(pady=(0, 30))
        
        # Email Field
        ctk.CTkLabel(
            inner, 
            text="Email", 
            font=("SF Pro Display", 12, "bold"),
            text_color="#a0a3bd",
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        self.entry_email = ctk.CTkEntry(
            inner, 
            height=45,
            corner_radius=12,
            font=("SF Pro Display", 13),
            placeholder_text="Enter your email",
            fg_color="#16213e",
            border_color="#2a2a4e",
            text_color="#ffffff"
        )
        self.entry_email.pack(fill="x", pady=(0, 15))
        
        # Password Field
        ctk.CTkLabel(
            inner, 
            text="Password", 
            font=("SF Pro Display", 12, "bold"),
            text_color="#a0a3bd",
            anchor="w"
        ).pack(fill="x", pady=(0, 5))
        
        self.entry_pass = ctk.CTkEntry(
            inner, 
            height=45,
            corner_radius=12,
            font=("SF Pro Display", 13),
            placeholder_text="Enter your password",
            show="•",
            fg_color="#16213e",
            border_color="#2a2a4e",
            text_color="#ffffff"
        )
        self.entry_pass.pack(fill="x", pady=(0, 25))
        self.entry_pass.bind("<Return>", lambda e: self.do_login())
        
        # Login Button with gradient-like effect
        self.btn_login = ctk.CTkButton(
            inner, 
            text="LOGIN",
            font=("SF Pro Display", 14, "bold"),
            height=48,
            corner_radius=12,
            fg_color="#6366f1",
            hover_color="#5855eb",
            command=self.do_login
        )
        self.btn_login.pack(fill="x", pady=(0, 15))
        
        # Message Label
        self.lbl_msg = ctk.CTkLabel(
            inner, 
            text="", 
            font=("SF Pro Display", 11),
            text_color="#ef4444"
        )
        self.lbl_msg.pack()
        
        # Loading indicator (hidden by default)
        self.loading_frame = ctk.CTkFrame(inner, fg_color="transparent", height=30)
        self.loading_label = ctk.CTkLabel(
            self.loading_frame, 
            text="", 
            font=("SF Pro Display", 11),
            text_color="#6366f1"
        )
        self.loading_label.pack()

    def do_login(self):
        email = self.entry_email.get()
        pwd = self.entry_pass.get()
        if not email or not pwd:
            self.lbl_msg.configure(text="⚠️ Vui lòng nhập Email và Password", text_color="#ef4444")
            return
        
        # Show loading state
        self.btn_login.configure(text="⏳ Đang đăng nhập...", state="disabled", fg_color="#4a4a6a")
        self.lbl_msg.configure(text="", text_color="#6366f1")
        self.parent.update()
        
        success, msg = self.app.auth_service.login(email, pwd)
        if success:
            self.lbl_msg.configure(text="✅ Đăng nhập thành công!", text_color="#22c55e")
            self.parent.update()
            self.app.check_auth_and_redirect()
        else:
            self.lbl_msg.configure(text=f"❌ {msg}", text_color="#ef4444")
            self.btn_login.configure(text="LOGIN", state="normal", fg_color="#6366f1")
