
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import json
import os
from PIL import Image, ImageTk
from app.services.browser_service import BrowserService
from app.services.api_service import LabsApiService
from app.services.account_manager import AccountManager
from app.ui.rounded_button import RoundedButton

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Google Labs Automation - Batch Mode")
        self.root.geometry("1400x800")

        # Services
        self.account_manager = AccountManager()
        self.browser_service = BrowserService()
        
        # Job queue and tracking
        self.job_queue = []  # List of {image, prompt, status, account, ...}
        self.running_jobs = {}  # account_name -> list of running job indices
        self.max_jobs_per_account = 4
        self.is_running = False
        self.lock = threading.Lock()
        
        # Image cache for thumbnails
        self.thumbnail_cache = {}
        
        # Style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Card.TFrame", background="#f0f0f0", relief="raised")
        style.configure("Treeview", font=("Arial", 10), rowheight=25)

        # Layout
        self.main_container = tk.Frame(root)
        self.main_container.pack(fill="both", expand=True)
        
        # Sidebar
        self.sidebar = tk.Frame(self.main_container, bg="#2c3e50", width=200)
        self.sidebar.pack(side="left", fill="y", ipadx=5)
        
        tk.Label(self.sidebar, text="🤖 Labs Tool", bg="#2c3e50", fg="white", font=("Segoe UI", 18, "bold")).pack(pady=30)
        
        self.btn_acc = RoundedButton(self.sidebar, text="Quản lý Tài khoản", command=lambda: self.show_view("account"), width=180, height=40, bg_color="#2c3e50", fg_color="#34495e", hover_color="#1abc9c")
        self.btn_acc.pack(pady=5)
        
        self.btn_vid = RoundedButton(self.sidebar, text="Tạo Video (Batch)", command=lambda: self.show_view("video"), width=180, height=40, bg_color="#2c3e50", fg_color="#2c3e50", hover_color="#1abc9c")
        self.btn_vid.pack(pady=5)

        # Content Area
        self.content_area = tk.Frame(self.main_container, bg="white")
        self.content_area.pack(side="left", fill="both", expand=True)

        self.frames = {}
        self.create_account_view()
        self.create_video_view()

        self.show_view("account")

    def show_view(self, name):
        if name == "account":
            self.btn_acc.itemconfig(self.btn_acc.rect, fill="#34495e", outline="#34495e")
            self.btn_acc.fg_color = "#34495e"
            self.btn_vid.itemconfig(self.btn_vid.rect, fill="#2c3e50", outline="#2c3e50")
            self.btn_vid.fg_color = "#2c3e50"
            
            self.frames["account"].pack(fill="both", expand=True)
            self.frames["video"].pack_forget()
            self.refresh_account_ui()
        else:
            self.btn_acc.itemconfig(self.btn_acc.rect, fill="#2c3e50", outline="#2c3e50")
            self.btn_acc.fg_color = "#2c3e50"
            self.btn_vid.itemconfig(self.btn_vid.rect, fill="#34495e", outline="#34495e")
            self.btn_vid.fg_color = "#34495e"

            self.frames["account"].pack_forget()
            self.frames["video"].pack(fill="both", expand=True)

    # ==================== ACCOUNT VIEW ====================
    def create_account_view(self):
        self.frames["account"] = tk.Frame(self.content_area, bg="white")
        
        toolbar = tk.Frame(self.frames["account"], bg="#ecf0f1", pady=15)
        toolbar.pack(fill="x")
        
        RoundedButton(toolbar, text="➕ Thêm Cookie", command=self.add_new_account, width=120, height=35, bg_color="#ecf0f1", fg_color="#27ae60", hover_color="#2ecc71").pack(side="left", padx=15)
        RoundedButton(toolbar, text="🔃 Refresh", command=self.refresh_account_ui, width=100, height=35, bg_color="#ecf0f1", fg_color="#3498db", hover_color="#5dade2").pack(side="left", padx=5)
        RoundedButton(toolbar, text="ℹ Hướng dẫn", command=self.show_setup_guide, width=110, height=35, bg_color="#ecf0f1", fg_color="#9b59b6", hover_color="#8e44ad").pack(side="left", padx=5)

        self.canvas = tk.Canvas(self.frames["account"], bg="white", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.frames["account"], orient="vertical", command=self.canvas.yview)
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

    def refresh_account_ui(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        accounts = self.account_manager.accounts
        
        if not accounts:
            # Empty state with instructions
            self.create_empty_state()
            return
        
        for idx, acc in enumerate(accounts):
            self.create_account_card(idx, acc)
    
    def create_empty_state(self):
        """Show instructions when no accounts exist"""
        import webbrowser
        
        empty_frame = tk.Frame(self.scrollable_frame, bg="white", padx=30, pady=40)
        empty_frame.pack(fill="both", expand=True)
        
        # Icon
        tk.Label(empty_frame, text="🍪", font=("Segoe UI", 48), bg="white").pack(pady=(20, 10))
        
        # Title
        tk.Label(empty_frame, text="Chưa có tài khoản nào!", 
                font=("Segoe UI", 16, "bold"), bg="white", fg="#2c3e50").pack(pady=(0, 20))
        
        # Instructions card
        instr_card = tk.Frame(empty_frame, bg="#f8f9fa", padx=25, pady=20, 
                             highlightbackground="#e0e0e0", highlightthickness=1)
        instr_card.pack(fill="x", pady=10)
        
        tk.Label(instr_card, text="📌 Hướng dẫn thêm tài khoản:", 
                font=("Segoe UI", 12, "bold"), bg="#f8f9fa", fg="#2c3e50").pack(anchor="w", pady=(0, 15))
        
        # Step 1
        step1 = tk.Frame(instr_card, bg="#f8f9fa")
        step1.pack(fill="x", pady=5)
        tk.Label(step1, text="1️⃣", font=("Segoe UI", 14), bg="#f8f9fa").pack(side="left")
        tk.Label(step1, text="Tải Extension Copy Cookie:", font=("Segoe UI", 10), bg="#f8f9fa", fg="#555").pack(side="left", padx=(5, 0))
        
        link_btn = tk.Label(step1, text="📥 Tải Extension", font=("Segoe UI", 10, "underline"), 
                           bg="#3498db", fg="white", cursor="hand2", padx=10, pady=3)
        link_btn.pack(side="left", padx=10)
        link_btn.bind("<Button-1>", lambda e: webbrowser.open("https://drive.google.com/file/d/1JgF9JO-Mdj7j7aqYsLp-Vwu4ShHpwr1u/view?usp=sharing"))
        
        # Step 2
        step2 = tk.Frame(instr_card, bg="#f8f9fa")
        step2.pack(fill="x", pady=5)
        tk.Label(step2, text="2️⃣", font=("Segoe UI", 14), bg="#f8f9fa").pack(side="left")
        tk.Label(step2, text="Giải nén file ZIP đã tải về", font=("Segoe UI", 10), bg="#f8f9fa", fg="#555").pack(side="left", padx=(5, 0))
        
        # Step 3
        step3 = tk.Frame(instr_card, bg="#f8f9fa")
        step3.pack(fill="x", pady=5)
        tk.Label(step3, text="3️⃣", font=("Segoe UI", 14), bg="#f8f9fa").pack(side="left")
        step3_text = tk.Frame(step3, bg="#f8f9fa")
        step3_text.pack(side="left", padx=(5, 0))
        tk.Label(step3_text, text="Mở Chrome → ", font=("Segoe UI", 10), bg="#f8f9fa", fg="#555").pack(side="left")
        tk.Label(step3_text, text="chrome://extensions", font=("Consolas", 10), bg="#ecf0f1", fg="#e74c3c", padx=5).pack(side="left")
        
        # Step 4
        step4 = tk.Frame(instr_card, bg="#f8f9fa")
        step4.pack(fill="x", pady=5)
        tk.Label(step4, text="4️⃣", font=("Segoe UI", 14), bg="#f8f9fa").pack(side="left")
        tk.Label(step4, text="Bật ", font=("Segoe UI", 10), bg="#f8f9fa", fg="#555").pack(side="left", padx=(5, 0))
        tk.Label(step4, text="Developer mode", font=("Segoe UI", 10, "bold"), bg="#f8f9fa", fg="#e67e22").pack(side="left")
        tk.Label(step4, text=" (góc phải trên)", font=("Segoe UI", 10), bg="#f8f9fa", fg="#555").pack(side="left")
        
        # Step 5
        step5 = tk.Frame(instr_card, bg="#f8f9fa")
        step5.pack(fill="x", pady=5)
        tk.Label(step5, text="5️⃣", font=("Segoe UI", 14), bg="#f8f9fa").pack(side="left")
        tk.Label(step5, text="Click ", font=("Segoe UI", 10), bg="#f8f9fa", fg="#555").pack(side="left", padx=(5, 0))
        tk.Label(step5, text="Load unpacked", font=("Segoe UI", 10, "bold"), bg="#f8f9fa", fg="#27ae60").pack(side="left")
        tk.Label(step5, text=" → Chọn thư mục extension đã giải nén", font=("Segoe UI", 10), bg="#f8f9fa", fg="#555").pack(side="left")
        
        # Step 6
        step6 = tk.Frame(instr_card, bg="#f8f9fa")
        step6.pack(fill="x", pady=5)
        tk.Label(step6, text="6️⃣", font=("Segoe UI", 14), bg="#f8f9fa").pack(side="left")
        tk.Label(step6, text="Vào ", font=("Segoe UI", 10), bg="#f8f9fa", fg="#555").pack(side="left", padx=(5, 0))
        tk.Label(step6, text="labs.google", font=("Segoe UI", 10, "bold"), bg="#f8f9fa", fg="#3498db").pack(side="left")
        tk.Label(step6, text=" → Đăng nhập → Click icon Extension → Copy Cookie", font=("Segoe UI", 10), bg="#f8f9fa", fg="#555").pack(side="left")
        
        # Step 7
        step7 = tk.Frame(instr_card, bg="#f8f9fa")
        step7.pack(fill="x", pady=5)
        tk.Label(step7, text="7️⃣", font=("Segoe UI", 14), bg="#f8f9fa").pack(side="left")
        tk.Label(step7, text="Quay lại đây → Click ", font=("Segoe UI", 10), bg="#f8f9fa", fg="#555").pack(side="left", padx=(5, 0))
        tk.Label(step7, text="➕ Thêm Cookie", font=("Segoe UI", 10, "bold"), bg="#27ae60", fg="white", padx=5).pack(side="left")
        tk.Label(step7, text=" → Dán Cookie", font=("Segoe UI", 10), bg="#f8f9fa", fg="#555").pack(side="left")
    
    def show_setup_guide(self):
        """Show setup instructions in a popup window"""
        import webbrowser
        
        win = tk.Toplevel(self.root)
        win.title("Hướng dẫn cài đặt")
        win.geometry("650x480")
        win.configure(bg="white")
        win.resizable(False, False)
        
        # Title
        tk.Label(win, text="🍪 Hướng dẫn lấy Cookie", font=("Segoe UI", 16, "bold"), bg="white", fg="#2c3e50").pack(pady=(20, 15))
        
        # Instructions card
        instr_card = tk.Frame(win, bg="#f8f9fa", padx=25, pady=20)
        instr_card.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        
        steps = [
            ("1️⃣", "Tải Extension Copy Cookie:", "📥 Tải Extension", "https://drive.google.com/file/d/1JgF9JO-Mdj7j7aqYsLp-Vwu4ShHpwr1u/view?usp=sharing"),
            ("2️⃣", "Giải nén file ZIP đã tải về", None, None),
            ("3️⃣", "Mở Chrome → chrome://extensions", None, None),
            ("4️⃣", "Bật Developer mode (góc phải trên)", None, None),
            ("5️⃣", "Click Load unpacked → Chọn thư mục extension", None, None),
            ("6️⃣", "Vào labs.google → Đăng nhập → Click Extension → Copy", None, None),
            ("7️⃣", "Quay lại app → Click ➕ Thêm Cookie → Dán", None, None),
        ]
        
        for num, text, btn_text, btn_url in steps:
            row = tk.Frame(instr_card, bg="#f8f9fa")
            row.pack(fill="x", pady=6)
            tk.Label(row, text=num, font=("Segoe UI", 14), bg="#f8f9fa").pack(side="left")
            tk.Label(row, text=text, font=("Segoe UI", 10), bg="#f8f9fa", fg="#555").pack(side="left", padx=(8, 0))
            
            if btn_text and btn_url:
                btn = tk.Label(row, text=btn_text, font=("Segoe UI", 10), bg="#3498db", fg="white", cursor="hand2", padx=10, pady=2)
                btn.pack(side="left", padx=10)
                btn.bind("<Button-1>", lambda e, url=btn_url: webbrowser.open(url))
        
        # Close button
        tk.Button(win, text="Đóng", command=win.destroy, bg="#95a5a6", fg="white", font=("Segoe UI", 10), padx=30, pady=5, bd=0).pack(pady=15)

    def create_account_card(self, idx, acc):
        container = tk.Frame(self.scrollable_frame, bg="white", pady=5)
        container.pack(fill="x", padx=10, pady=5)
        
        card = tk.LabelFrame(container, text="", padx=15, pady=10, bg="#fdfdfd", bd=1, relief="solid", font=("Arial", 1))
        card.config(text="") 
        card.pack(fill="x", expand=True)
        
        header = tk.Frame(card, bg="#fdfdfd")
        header.pack(fill="x")
        tk.Label(header, text=acc['name'][:40], bg="#fdfdfd", font=("Segoe UI", 12, "bold"), fg="#2c3e50").pack(side="left")
        
        status = acc.get('status', 'Unknown')
        color = "#95a5a6"
        if "Live" in status: color = "#27ae60"
        elif "Die" in status: color = "#c0392b"
        
        tk.Label(header, text=f"• {status}", fg=color, bg="#fdfdfd", font=("Segoe UI", 10)).pack(side="right")
        
        pid = acc.get('project_id')
        if pid:
            link = tk.Label(card, text=f"Project ID: {pid}", fg="#3498db", bg="#fdfdfd", font=("Segoe UI", 9, "underline"), cursor="hand2")
            link.pack(anchor="w", padx=0, pady=(0,5))
            
            def open_project(event, p=pid):
                import webbrowser
                webbrowser.open(f"https://labs.google/fx/vi/tools/flow/project/{p}")
                
            link.bind("<Button-1>", open_project)
        else:
            tk.Label(card, text="No Project ID", fg="#95a5a6", bg="#fdfdfd", font=("Segoe UI", 9)).pack(anchor="w")

        action_frame = tk.Frame(card, bg="#fdfdfd")
        action_frame.pack(fill="x", pady=(15, 0))
        
        RoundedButton(action_frame, text="Browser", command=lambda i=idx: self.open_browser(i), width=80, height=30, bg_color="#fdfdfd", fg_color="#34495e", hover_color="#5D6D7E").pack(side="left", padx=2)
        RoundedButton(action_frame, text="Check", command=lambda i=idx: self.check_cookie(i), width=80, height=30, bg_color="#fdfdfd", fg_color="#3498db", hover_color="#2980b9").pack(side="left", padx=2)
        RoundedButton(action_frame, text="Delete", command=lambda i=idx: self.delete_account(i), width=60, height=30, bg_color="#fdfdfd", fg_color="#e74c3c", hover_color="#c0392b").pack(side="right", padx=2)

    # ==================== VIDEO VIEW (NEW BATCH MODE) ====================
    def create_video_view(self):
        self.frames["video"] = tk.Frame(self.content_area, bg="white")
        
        # Top toolbar
        toolbar = tk.Frame(self.frames["video"], bg="#ecf0f1", pady=10)
        toolbar.pack(fill="x")
        
        RoundedButton(toolbar, text="📂 Import Excel", command=self.import_excel, width=130, height=35, bg_color="#ecf0f1", fg_color="#e67e22", hover_color="#d35400").pack(side="left", padx=15)
        RoundedButton(toolbar, text="📥 Tải Template", command=self.download_template, width=120, height=35, bg_color="#ecf0f1", fg_color="#3498db", hover_color="#2980b9").pack(side="left", padx=5)
        
        self.btn_start = RoundedButton(toolbar, text="▶ START", command=self.start_batch, width=100, height=35, bg_color="#ecf0f1", fg_color="#27ae60", hover_color="#1e8449")
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_stop = RoundedButton(toolbar, text="⏹ STOP", command=self.stop_batch, width=100, height=35, bg_color="#ecf0f1", fg_color="#e74c3c", hover_color="#c0392b")
        self.btn_stop.pack(side="left", padx=5)
        
        # Separator
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=15, pady=5)
        
        # Aspect Ratio
        tk.Label(toolbar, text="Tỷ lệ:", bg="#ecf0f1", font=("Segoe UI", 9)).pack(side="left")
        self.combo_ratio = ttk.Combobox(toolbar, values=["Landscape (16:9)", "Portrait (9:16)"], state="readonly", width=14, font=("Segoe UI", 9))
        self.combo_ratio.set("Landscape (16:9)")
        self.combo_ratio.pack(side="left", padx=(5, 15))
        
        # Copy count
        tk.Label(toolbar, text="Bản sao:", bg="#ecf0f1", font=("Segoe UI", 9)).pack(side="left")
        self.spin_count = tk.Spinbox(toolbar, from_=1, to=4, width=3, font=("Segoe UI", 9))
        self.spin_count.pack(side="left", padx=5)
        
        # Status label
        self.lbl_status = tk.Label(toolbar, text="Chờ import Excel...", bg="#ecf0f1", font=("Segoe UI", 10), fg="#7f8c8d")
        self.lbl_status.pack(side="right", padx=20)
        
        # Main content: Left (Queue Preview) + Right (Progress)
        content = tk.Frame(self.frames["video"], bg="white")
        content.pack(fill="both", expand=True, padx=10, pady=10)
        
        # LEFT PANEL - Queue Preview
        left_panel = tk.LabelFrame(content, text="📋 Danh sách Jobs (từ Excel)", font=("Segoe UI", 11, "bold"), bg="white", fg="#2c3e50", padx=10, pady=10)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Help text
        help_text = "💡 Lưu file Excel cùng thư mục với ảnh → chỉ cần nhập tên ảnh. Nếu khác thư mục → dùng đường dẫn tuyệt đối (VD: C:\\folder\\image.jpg)"
        tk.Label(left_panel, text=help_text, bg="#fff3cd", fg="#856404", font=("Segoe UI", 8), wraplength=400, justify="left", padx=8, pady=4).pack(fill="x", pady=(0, 8))
        
        # Queue list with scrollbar
        queue_container = tk.Frame(left_panel, bg="white")
        queue_container.pack(fill="both", expand=True)
        
        self.queue_canvas = tk.Canvas(queue_container, bg="white", highlightthickness=0)
        self.queue_scrollbar = ttk.Scrollbar(queue_container, orient="vertical", command=self.queue_canvas.yview)
        self.queue_list_frame = tk.Frame(self.queue_canvas, bg="white")
        
        self.queue_list_frame.bind(
            "<Configure>",
            lambda e: self.queue_canvas.configure(scrollregion=self.queue_canvas.bbox("all"))
        )
        
        self.queue_canvas.create_window((0, 0), window=self.queue_list_frame, anchor="nw")
        self.queue_canvas.configure(yscrollcommand=self.queue_scrollbar.set)
        
        self.queue_canvas.pack(side="left", fill="both", expand=True)
        self.queue_scrollbar.pack(side="right", fill="y")
        
        # RIGHT PANEL - Progress
        right_panel = tk.LabelFrame(content, text="⚡ Tiến trình", font=("Segoe UI", 11, "bold"), bg="white", fg="#2c3e50", padx=10, pady=10)
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Progress list with scrollbar
        progress_container = tk.Frame(right_panel, bg="white")
        progress_container.pack(fill="both", expand=True)
        
        self.progress_canvas = tk.Canvas(progress_container, bg="white", highlightthickness=0)
        self.progress_scrollbar = ttk.Scrollbar(progress_container, orient="vertical", command=self.progress_canvas.yview)
        self.progress_list_frame = tk.Frame(self.progress_canvas, bg="white")
        
        self.progress_list_frame.bind(
            "<Configure>",
            lambda e: self.progress_canvas.configure(scrollregion=self.progress_canvas.bbox("all"))
        )
        
        self.progress_canvas.create_window((0, 0), window=self.progress_list_frame, anchor="nw")
        self.progress_canvas.configure(yscrollcommand=self.progress_scrollbar.set)
        
        self.progress_canvas.pack(side="left", fill="both", expand=True)
        self.progress_scrollbar.pack(side="right", fill="y")
        
        # Download All button (bottom of progress panel)
        btn_download_all = tk.Frame(right_panel, bg="white")
        btn_download_all.pack(fill="x", pady=(10, 0))
        RoundedButton(btn_download_all, text="📥 Tải tất cả", command=self.download_all_videos, width=120, height=32, bg_color="white", fg_color="#27ae60", hover_color="#1e8449").pack(side="right")
        
        # Progress card references
        self.progress_cards = {}
    
    def download_template(self):
        """Create and save a template Excel file"""
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile="template_jobs.xlsx"
        )
        if not save_path:
            return
        
        try:
            import pandas as pd
            
            # Create template with sample data
            data = {
                'image': [
                    'C:\\path\\to\\image1.jpg',
                    'C:\\path\\to\\image2.jpg',
                    'C:\\path\\to\\image3.jpg',
                ],
                'prompt': [
                    'A gentle breeze moves through the scene',
                    'The camera slowly zooms in on the subject',
                    'Soft lighting changes gradually in the background',
                ]
            }
            
            df = pd.DataFrame(data)
            df.to_excel(save_path, index=False)
            
            messagebox.showinfo("Success", f"Đã tạo template:\n{save_path}\n\nSửa đường dẫn image và prompt rồi import lại.")
            
            # Open file location
            os.startfile(os.path.dirname(save_path))
            
        except ImportError:
            messagebox.showerror("Error", "Cần cài đặt pandas và openpyxl:\npip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Error", f"Lỗi tạo template: {e}")
    
    def import_excel(self):
        """Import Excel file with columns: image, prompt"""
        filepath = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        if not filepath:
            return
        
        try:
            import pandas as pd
            df = pd.read_excel(filepath)
            
            # Check required columns
            if 'image' not in df.columns or 'prompt' not in df.columns:
                messagebox.showerror("Error", "Excel phải có 2 cột: 'image' và 'prompt'")
                return
            
            # Clear old queue
            self.job_queue = []
            
            # Parse rows
            base_dir = os.path.dirname(filepath)
            for idx, row in df.iterrows():
                image_path = str(row['image']).strip()
                prompt = str(row['prompt']).strip()
                
                # Handle relative paths
                if not os.path.isabs(image_path):
                    image_path = os.path.join(base_dir, image_path)
                
                if not os.path.exists(image_path):
                    print(f"Warning: Image not found: {image_path}")
                    continue
                
                self.job_queue.append({
                    'index': len(self.job_queue),
                    'image': image_path,
                    'prompt': prompt,
                    'status': 'pending',  # pending, processing, polling, success, failed
                    'account': None,
                    'operation': None,
                    'video_url': None,
                    'error': None
                })
            
            self.refresh_queue_preview()
            self.lbl_status.config(text=f"Tổng: {len(self.job_queue)} jobs | Chờ bắt đầu...")
            
        except ImportError:
            messagebox.showerror("Error", "Cần cài đặt pandas và openpyxl:\npip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("Error", f"Lỗi đọc Excel: {e}")
    
    def refresh_queue_preview(self):
        """Refresh the queue preview panel"""
        for widget in self.queue_list_frame.winfo_children():
            widget.destroy()
        
        for job in self.job_queue:
            self.create_queue_item(job)
    
    def create_queue_item(self, job):
        """Create a queue item card with thumbnail and prompt preview"""
        idx = job['index']
        
        # Card with subtle shadow effect
        card = tk.Frame(self.queue_list_frame, bg="#ffffff", padx=10, pady=8, highlightbackground="#e0e0e0", highlightthickness=1)
        card.pack(fill="x", pady=3, padx=2)
        
        # Main horizontal layout
        content = tk.Frame(card, bg="#ffffff")
        content.pack(fill="x")
        
        # Left: Thumbnail with rounded border effect
        thumb_container = tk.Frame(content, bg="#e0e0e0", padx=2, pady=2)
        thumb_container.pack(side="left", anchor="center")
        
        thumb_frame = tk.Frame(thumb_container, bg="#f5f5f5", width=56, height=42)
        thumb_frame.pack()
        thumb_frame.pack_propagate(False)
        
        try:
            img = Image.open(job['image'])
            img.thumbnail((54, 40))
            photo = ImageTk.PhotoImage(img)
            self.thumbnail_cache[idx] = photo
            lbl_img = tk.Label(thumb_frame, image=photo, bg="#f5f5f5")
            lbl_img.pack(expand=True)
        except:
            tk.Label(thumb_frame, text="🖼", font=("Segoe UI", 14), bg="#f5f5f5", fg="#bdc3c7").pack(expand=True)
        
        # Middle: Info (vertically centered)
        info_frame = tk.Frame(content, bg="#ffffff")
        info_frame.pack(side="left", fill="both", expand=True, padx=(12, 8), anchor="center")
        
        # Job number
        tk.Label(info_frame, text=f"Job #{idx+1}", font=("Segoe UI", 10, "bold"), bg="#ffffff", fg="#2c3e50").pack(anchor="w")
        
        # Prompt preview
        prompt_preview = job['prompt'][:45] + "..." if len(job['prompt']) > 45 else job['prompt']
        tk.Label(info_frame, text=prompt_preview, font=("Segoe UI", 9), bg="#ffffff", fg="#7f8c8d", anchor="w").pack(anchor="w", fill="x")
        
        # Right side: Actions & Status (vertically centered)
        right_frame = tk.Frame(content, bg="#ffffff")
        right_frame.pack(side="right", anchor="center")
        
        # Status badge (show first)
        status = job['status']
        status_config = {
            'pending': ('#f39c12', '⏳', 'Chờ'),
            'processing': ('#3498db', '⚙', 'Đang xử lý'),
            'polling': ('#9b59b6', '📡', 'Chờ kết quả'),
            'success': ('#27ae60', '✓', 'Hoàn thành'),
            'failed': ('#e74c3c', '✗', 'Lỗi')
        }
        color, icon, text = status_config.get(status, ('#95a5a6', '?', 'Unknown'))
        
        status_frame = tk.Frame(right_frame, bg="#ffffff")
        status_frame.pack(side="right", padx=(8, 0))
        
        # Status with background
        status_bg = tk.Frame(status_frame, bg=color, padx=6, pady=2)
        status_bg.pack()
        tk.Label(status_bg, text=f"{icon}", font=("Segoe UI", 10), bg=color, fg="white").pack()
        
        # Edit/Delete buttons (only for pending)
        if job['status'] == 'pending':
            btn_frame = tk.Frame(right_frame, bg="#ffffff")
            btn_frame.pack(side="right")
            
            # Edit button - styled
            edit_btn = tk.Button(btn_frame, text="✎", font=("Segoe UI", 10), 
                                bg="#ecf0f1", fg="#3498db", activebackground="#d5dbdb",
                                bd=0, padx=8, pady=4, cursor="hand2", relief="flat",
                                command=lambda i=idx: self.edit_job(i))
            edit_btn.pack(side="left", padx=2)
            
            # Delete button - styled  
            del_btn = tk.Button(btn_frame, text="🗑", font=("Segoe UI", 10),
                               bg="#ecf0f1", fg="#e74c3c", activebackground="#d5dbdb",
                               bd=0, padx=8, pady=4, cursor="hand2", relief="flat",
                               command=lambda i=idx: self.delete_job(i))
            del_btn.pack(side="left", padx=2)
    
    def edit_job(self, idx):
        """Edit a job's prompt"""
        job = next((j for j in self.job_queue if j['index'] == idx), None)
        if not job or job['status'] != 'pending':
            return
        
        # Create edit dialog
        win = tk.Toplevel(self.root)
        win.title(f"Sửa Job #{idx+1}")
        win.geometry("500x300")
        win.configure(bg="white")
        
        tk.Label(win, text="Đường dẫn ảnh:", bg="white", font=("Segoe UI", 10)).pack(pady=(15, 5), padx=20, anchor="w")
        entry_img = tk.Entry(win, font=("Segoe UI", 10), width=60)
        entry_img.pack(padx=20, fill="x")
        entry_img.insert(0, job['image'])
        
        tk.Label(win, text="Prompt:", bg="white", font=("Segoe UI", 10)).pack(pady=(15, 5), padx=20, anchor="w")
        txt_prompt = tk.Text(win, font=("Segoe UI", 10), height=5)
        txt_prompt.pack(padx=20, fill="both", expand=True)
        txt_prompt.insert("1.0", job['prompt'])
        
        def save():
            new_image = entry_img.get().strip()
            new_prompt = txt_prompt.get("1.0", tk.END).strip()
            
            if not new_image or not new_prompt:
                messagebox.showwarning("Warning", "Vui lòng điền đầy đủ!")
                return
            
            job['image'] = new_image
            job['prompt'] = new_prompt
            self.refresh_queue_preview()
            win.destroy()
        
        tk.Button(win, text="Lưu", command=save, bg="#27ae60", fg="white", font=("Segoe UI", 10), padx=20, pady=5).pack(pady=15)
    
    def delete_job(self, idx):
        """Delete a job from queue"""
        job = next((j for j in self.job_queue if j['index'] == idx), None)
        if not job or job['status'] != 'pending':
            return
        
        self.job_queue = [j for j in self.job_queue if j['index'] != idx]
        # Re-index remaining jobs
        for i, j in enumerate(self.job_queue):
            j['index'] = i
        self.refresh_queue_preview()
        self.lbl_status.config(text=f"Còn {len(self.job_queue)} jobs")
    
    def download_all_videos(self):
        """Download all completed videos to a folder"""
        # Get completed jobs with video URLs
        completed = [j for j in self.job_queue if j['status'] == 'success' and j.get('video_url')]
        
        if not completed:
            messagebox.showinfo("Info", "Chưa có video nào hoàn thành để tải!")
            return
        
        # Ask for folder
        folder = filedialog.askdirectory(title="Chọn thư mục lưu video")
        if not folder:
            return
        
        self.lbl_status.config(text=f"Đang tải {len(completed)} video...")
        
        def download_worker():
            api = LabsApiService()
            success_count = 0
            
            for job in completed:
                try:
                    filename = f"video_job_{job['index']+1}.mp4"
                    save_path = os.path.join(folder, filename)
                    
                    if api.download_video(job['video_url'], save_path):
                        success_count += 1
                except Exception as e:
                    print(f"Download error: {e}")
            
            self.root.after(0, lambda: [
                self.lbl_status.config(text=f"Đã tải {success_count}/{len(completed)} video"),
                messagebox.showinfo("Done", f"Đã tải {success_count} video vào:\n{folder}"),
                os.startfile(folder)
            ])
        
        threading.Thread(target=download_worker, daemon=True).start()
    
    def refresh_progress_panel(self):
        """Refresh the progress panel with active jobs"""
        for widget in self.progress_list_frame.winfo_children():
            widget.destroy()
        self.progress_cards = {}
        
        # Show all non-pending jobs
        for job in self.job_queue:
            if job['status'] != 'pending':
                self.create_progress_card(job)
    
    def create_progress_card(self, job):
        """Create a progress card for a job"""
        idx = job['index']
        
        card = tk.Frame(self.progress_list_frame, bg="white", bd=1, relief="solid", padx=10, pady=8)
        card.pack(fill="x", pady=3)
        
        # Header: Job number + Account
        header = tk.Frame(card, bg="white")
        header.pack(fill="x")
        
        tk.Label(header, text=f"Job #{idx+1}", font=("Segoe UI", 10, "bold"), bg="white", fg="#2c3e50").pack(side="left")
        
        acc_name = job.get('account', 'N/A')
        if acc_name and len(acc_name) > 20:
            acc_name = acc_name[:20] + "..."
        tk.Label(header, text=f"[{acc_name}]", font=("Segoe UI", 8), bg="white", fg="#7f8c8d").pack(side="left", padx=5)
        
        # Status
        status = job['status']
        status_texts = {
            'processing': ('🔄 Đang xử lý...', '#3498db'),
            'polling': ('📡 Đang chờ video...', '#9b59b6'),
            'success': ('✓ Hoàn thành', '#27ae60'),
            'failed': ('✗ Lỗi', '#e74c3c')
        }
        text, color = status_texts.get(status, ('...', '#95a5a6'))
        
        status_label = tk.Label(header, text=text, font=("Segoe UI", 9), bg="white", fg=color)
        status_label.pack(side="right")
        
        # Progress Bar for active jobs
        if status in ('processing', 'polling'):
            progress = job.get('progress', 0)
            pb_frame = tk.Frame(card, bg="#f0f0f0", height=4)
            pb_frame.pack(fill="x", pady=(5, 0))
            
            # Colored bar based on percentage
            bar_width = int(progress)
            if bar_width > 0:
                tk.Frame(pb_frame, bg=color, width=0).place(relx=0, rely=0, relwidth=progress/100, relheight=1)
                
            # Text percentage
            tk.Label(card, text=f"{int(progress)}%", font=("Segoe UI", 7), bg="white", fg="#7f8c8d").pack(anchor="e")
        
        # Prompt preview
        prompt_preview = job['prompt'][:60] + "..." if len(job['prompt']) > 60 else job['prompt']
        tk.Label(card, text=prompt_preview, font=("Segoe UI", 8), bg="white", fg="#7f8c8d", wraplength=300, justify="left").pack(anchor="w", pady=(5, 0))
        
        # Error message and Retry button if failed
        if job['status'] == 'failed':
            err_frame = tk.Frame(card, bg="white")
            err_frame.pack(anchor="w", fill="x")
            
            if job.get('error'):
                tk.Label(err_frame, text=f"Error: {job['error'][:40]}...", font=("Segoe UI", 8), bg="white", fg="#e74c3c").pack(side="left")
            
            def retry_job(j=job):
                j['status'] = 'pending'
                j['error'] = None
                j['operation'] = None
                j['video_url'] = None
                self.refresh_queue_preview()
                self.refresh_progress_panel()
                # Restart batch if not running
                if not self.is_running:
                    self.start_batch()
            
            RoundedButton(err_frame, text="🔄 Thử lại", command=retry_job, width=80, height=22, bg_color="white", fg_color="#e67e22", hover_color="#d35400").pack(side="right", padx=5)
        
        # Action buttons if success
        if job['status'] == 'success' and job.get('video_url'):
            btn_frame = tk.Frame(card, bg="white")
            btn_frame.pack(anchor="w", pady=(5, 0))
            
            def preview_video(url=job['video_url'], i=idx):
                self.show_video_preview(url, i)
            
            def open_video(url=job['video_url']):
                import webbrowser
                webbrowser.open(url)
            
            def download_video(url=job['video_url'], i=idx):
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".mp4",
                    filetypes=[("MP4 Video", "*.mp4")],
                    initialfile=f"video_job_{i+1}.mp4"
                )
                if save_path:
                    api = LabsApiService()
                    threading.Thread(target=lambda: api.download_video(url, save_path), daemon=True).start()
            
            RoundedButton(btn_frame, text="▶ Xem", command=preview_video, width=60, height=22, bg_color="white", fg_color="#9b59b6", hover_color="#8e44ad").pack(side="left", padx=2)
            RoundedButton(btn_frame, text="Mở", command=open_video, width=50, height=22, bg_color="white", fg_color="#3498db", hover_color="#2980b9").pack(side="left", padx=2)
            RoundedButton(btn_frame, text="Tải về", command=download_video, width=60, height=22, bg_color="white", fg_color="#27ae60", hover_color="#1e8449").pack(side="left", padx=2)
        
        self.progress_cards[idx] = card
    
    def show_video_preview(self, video_url, job_idx):
        """Show video preview in a popup window"""
        import tempfile
        import requests
        
        # Create preview window
        preview_win = tk.Toplevel(self.root)
        preview_win.title(f"Preview - Job #{job_idx + 1}")
        preview_win.geometry("720x480")
        preview_win.configure(bg="black")
        
        # Loading label
        loading_label = tk.Label(preview_win, text="⏳ Đang tải video...", font=("Segoe UI", 14), bg="black", fg="white")
        loading_label.pack(expand=True)
        
        def load_and_play():
            try:
                # Download to temp file
                temp_dir = tempfile.gettempdir()
                temp_path = os.path.join(temp_dir, f"preview_job_{job_idx}.mp4")
                
                response = requests.get(video_url, stream=True)
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Play video
                preview_win.after(0, lambda: play_video(temp_path))
                
            except Exception as e:
                preview_win.after(0, lambda: loading_label.config(text=f"Lỗi: {e}"))
        
        def play_video(video_path):
            try:
                from tkVideoPlayer import TkinterVideo
                
                loading_label.destroy()
                
                # Video player
                player = TkinterVideo(preview_win, scaled=True)
                player.load(video_path)
                player.pack(expand=True, fill="both")
                player.play()
                
                # Controls
                ctrl_frame = tk.Frame(preview_win, bg="#2c3e50", pady=5)
                ctrl_frame.pack(fill="x")
                
                def toggle_play():
                    if player.is_paused():
                        player.play()
                        btn_play.config(text="⏸")
                    else:
                        player.pause()
                        btn_play.config(text="▶")
                
                def restart():
                    player.seek(0)
                    player.play()
                
                btn_play = tk.Button(ctrl_frame, text="⏸", font=("Arial", 12), bg="#3498db", fg="white", bd=0, padx=15, command=toggle_play)
                btn_play.pack(side="left", padx=10)
                
                tk.Button(ctrl_frame, text="⟲", font=("Arial", 12), bg="#e67e22", fg="white", bd=0, padx=15, command=restart).pack(side="left", padx=5)
                
                tk.Button(ctrl_frame, text="✕ Đóng", font=("Segoe UI", 10), bg="#e74c3c", fg="white", bd=0, padx=15, command=preview_win.destroy).pack(side="right", padx=10)
                
            except ImportError:
                loading_label.config(text="Cần cài: pip install tkvideoplayer")
            except Exception as e:
                loading_label.config(text=f"Lỗi phát video: {e}")
        
        threading.Thread(target=load_and_play, daemon=True).start()
    
    def start_batch(self):
        """Start processing all queued jobs"""
        if not self.job_queue:
            messagebox.showwarning("Warning", "Chưa import Excel!")
            return
        
        live_accounts = [a for a in self.account_manager.accounts if "Live" in a.get('status', '')]
        if not live_accounts:
            messagebox.showerror("Error", "Không có tài khoản Live nào!")
            return
        
        self.is_running = True
        self.running_jobs = {a['name']: [] for a in live_accounts}
        
        self.lbl_status.config(text=f"Đang chạy... ({len(live_accounts)} accounts)")
        
        # Start worker thread
        threading.Thread(target=self.batch_worker, daemon=True).start()
    
    def stop_batch(self):
        """Stop all processing"""
        self.is_running = False
        self.lbl_status.config(text="Đã dừng")
        self.browser_service.close_all_browsers()
    
    def batch_worker(self):
        """Main worker thread that manages job distribution"""
        import time
        
        live_accounts = [a for a in self.account_manager.accounts if "Live" in a.get('status', '')]
        
        while self.is_running:
            # Check for pending jobs
            pending_jobs = [j for j in self.job_queue if j['status'] == 'pending']
            if not pending_jobs:
                # Check if all jobs done
                active_jobs = [j for j in self.job_queue if j['status'] in ('processing', 'polling')]
                if not active_jobs:
                    self.root.after(0, lambda: self.lbl_status.config(text="Hoàn tất!"))
                    # Close browsers when done
                    self.browser_service.close_all_browsers()
                    break
                time.sleep(1)
                continue
            
            # Find available account
            for acc in live_accounts:
                if not self.is_running:
                    break
                
                with self.lock:
                    running_count = len([j for j in self.job_queue if j.get('account') == acc['name'] and j['status'] in ('processing', 'polling')])
                
                if running_count < self.max_jobs_per_account:
                    # Get next pending job
                    job = next((j for j in self.job_queue if j['status'] == 'pending'), None)
                    if job:
                        job['status'] = 'processing'
                        job['account'] = acc['name']
                        
                        # Update UI
                        self.root.after(0, self.refresh_queue_preview)
                        self.root.after(0, self.refresh_progress_panel)
                        
                        # Start job thread
                        threading.Thread(target=self.process_job, args=(job, acc), daemon=True).start()
            
            time.sleep(0.5)
    
    def process_job(self, job, account):
        """Process a single job"""
        import time
        
        try:
            api = LabsApiService()
            api.set_credentials(account['cookies'], account.get('access_token'))
            
            # 1. Upload image
            upload_result = api.upload_image(job['image'])
            media_id = upload_result.get('mediaId')
            if not media_id:
                raise Exception("Image Upload Failed")
            
            # 2. Get recaptcha token (visible browser - headless is blocked by Google)
            # Use account name as cache key to reuse browser per account
            token = self.browser_service.fetch_recaptcha_token(account['cookies'], use_visible_browser=True, cache_key=account['name'])
            if not token:
                raise Exception("ReCaptcha Token Failed (Check Console)")
            
            # 3. Generate video with settings from UI
            project_id = account.get('project_id')
            
            # Get aspect ratio from combo
            ratio_text = self.combo_ratio.get()
            aspect_ratio = "VIDEO_ASPECT_RATIO_PORTRAIT" if "Portrait" in ratio_text else "VIDEO_ASPECT_RATIO_LANDSCAPE"
            
            # Get copy count
            try:
                count = int(self.spin_count.get())
            except:
                count = 1
            
            gen_result = api.generate_video(
                job['prompt'], 
                media_id, 
                aspect_ratio, 
                count, 
                project_id, 
                token
            )
            
            operations = gen_result.get('operations', [])
            if not operations:
                raise Exception("No operations returned")
            
            job['operation'] = operations[0]
            job['status'] = 'polling'
            self.root.after(0, self.refresh_queue_preview)
            self.root.after(0, self.refresh_progress_panel)
            
            # 4. Poll for completion
            job['progress'] = 10
            
            # Start progress simulator in background
            def simulate_progress():
                import time
                for i in range(10, 95):
                    if job['status'] != 'polling' or not self.is_running:
                        break
                    job['progress'] = i
                    self.root.after(0, self.refresh_progress_panel)
                    time.sleep(0.8) # 0.8s * 85 steps ~= 68s total
            
            threading.Thread(target=simulate_progress, daemon=True).start()
            
            while self.is_running:
                time.sleep(5)
                status_res = api.check_video_status(operations)
                ops = status_res.get('operations', [])
                
                if ops:
                    op = ops[0]
                    st = op.get('status')
                    
                    if st == 'MEDIA_GENERATION_STATUS_SUCCESSFUL':
                        video_url = api.extract_video_url(op)
                        job['video_url'] = video_url
                        job['status'] = 'success'
                        break
                    elif st == 'MEDIA_GENERATION_STATUS_FAILED':
                        job['status'] = 'failed'
                        job['error'] = 'Video generation failed'
                        break
                    
                    operations = ops
            
        except Exception as e:
            job['status'] = 'failed'
            job['error'] = str(e)
            import traceback
            traceback.print_exc()
        
        finally:
            self.root.after(0, self.refresh_queue_preview)
            self.root.after(0, self.refresh_progress_panel)

    # ==================== ACCOUNT ACTIONS ====================
    def add_new_account(self):
        win = tk.Toplevel(self.root)
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
                import traceback
                try:
                    api = LabsApiService()
                    api.set_credentials(raw)
                    
                    token = api.fetch_access_token()
                    if not token:
                        raise Exception("Không lấy được Access Token!")

                    pid = api.create_project()
                    if not pid:
                        raise Exception("Không tạo được Project ID!")
                    
                    self.account_manager.add_account(raw, token, pid)
                    self.root.after(0, lambda: [self.refresh_account_ui(), win.destroy(), messagebox.showinfo("Success", "Thêm tài khoản thành công!")])
                    
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
                    
            threading.Thread(target=process, daemon=True).start()
            
        RoundedButton(win, text="Lưu & Lấy Token", command=save, width=150, height=40, bg_color="white", fg_color="#27ae60").pack(pady=10)

    def delete_account(self, idx):
        if messagebox.askyesno("Confirm", "Delete this account?"):
            self.account_manager.delete_account(idx)
            self.refresh_account_ui()

    def open_browser(self, idx):
        acc = self.account_manager.get_account(idx)
        threading.Thread(target=lambda: self.browser_service.launch_browser(json.dumps(acc['cookies'])), daemon=True).start()

    def check_cookie(self, idx):
        acc = self.account_manager.get_account(idx)
        
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
                
                self.account_manager.save_accounts()
                self.root.after(0, self.refresh_account_ui)
            except: pass
        threading.Thread(target=run, daemon=True).start()
