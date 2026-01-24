
import tkinter as tk
from tkinter import messagebox
from app.ui.rounded_button import RoundedButton

class LoginScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.setup_ui()

    def setup_ui(self):
        # Background
        self.parent.configure(bg="#ecf0f1")
        
        # Center Frame
        frame = tk.Frame(self.parent, bg="white", padx=40, pady=40)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        
        tk.Label(frame, text="Animo Studio Bot", font=("Segoe UI", 20, "bold"), bg="white", fg="#2c3e50").pack(pady=(0, 20))
        
        tk.Label(frame, text="Email", font=("Segoe UI", 10), bg="white", fg="#7f8c8d").pack(anchor="w")
        self.entry_email = tk.Entry(frame, width=30, font=("Segoe UI", 11), bd=1, relief="solid")
        self.entry_email.pack(pady=(5, 15), ipady=3)
        
        tk.Label(frame, text="Password", font=("Segoe UI", 10), bg="white", fg="#7f8c8d").pack(anchor="w")
        self.entry_pass = tk.Entry(frame, width=30, font=("Segoe UI", 11), bd=1, relief="solid", show="*")
        self.entry_pass.pack(pady=(5, 20), ipady=3)
        self.entry_pass.bind("<Return>", lambda e: self.do_login())
        
        self.btn_login = RoundedButton(frame, text="LOGIN", command=self.do_login, width=250, height=40, bg_color="white", fg_color="#3498db", hover_color="#2980b9")
        self.btn_login.pack()
        
        self.lbl_msg = tk.Label(frame, text="", bg="white", fg="red", font=("Segoe UI", 9))
        self.lbl_msg.pack(pady=10)

    def do_login(self):
        email = self.entry_email.get()
        pwd = self.entry_pass.get()
        if not email or not pwd:
            self.lbl_msg.config(text="Vui lòng nhập Email và Password")
            return
            
        self.lbl_msg.config(text="Đang đăng nhập...", fg="blue")
        self.parent.update()
        
        success, msg = self.app.auth_service.login(email, pwd)
        if success:
            self.lbl_msg.config(text="Đăng nhập thành công! Đang kiểm tra gói...", fg="green")
            self.parent.update()
            self.app.check_auth_and_redirect()
        else:
            self.lbl_msg.config(text=f"Lỗi: {msg}", fg="red")
