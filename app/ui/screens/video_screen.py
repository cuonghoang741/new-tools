
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import webbrowser
from PIL import Image, ImageTk
from app.ui.rounded_button import RoundedButton
from app.services.api_service import LabsApiService

class VideoScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.auto_download_dir = None
        self.setup_ui()

    def setup_ui(self):
        # Top toolbar
        toolbar = tk.Frame(self.parent, bg="#ecf0f1", pady=10)
        toolbar.pack(fill="x")
        
        RoundedButton(toolbar, text="📂 Import Excel", command=self.import_excel, width=130, height=35, bg_color="#ecf0f1", fg_color="#e67e22", hover_color="#d35400").pack(side="left", padx=15)
        RoundedButton(toolbar, text="📥 Tải Template", command=self.download_template, width=120, height=35, bg_color="#ecf0f1", fg_color="#3498db", hover_color="#2980b9").pack(side="left", padx=5)
        
        self.btn_start = RoundedButton(toolbar, text="▶ START", command=self.start_batch, width=100, height=35, bg_color="#ecf0f1", fg_color="#27ae60", hover_color="#1e8449")
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_stop = RoundedButton(toolbar, text="⏹ STOP", command=self.stop_batch, width=100, height=35, bg_color="#ecf0f1", fg_color="#e74c3c", hover_color="#c0392b")
        self.btn_stop.pack(side="left", padx=5)
        
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=15, pady=5)
        
        tk.Label(toolbar, text="Tỷ lệ:", bg="#ecf0f1", font=("Segoe UI", 9)).pack(side="left")
        self.combo_ratio = ttk.Combobox(toolbar, values=["Landscape (16:9)", "Portrait (9:16)"], state="readonly", width=14, font=("Segoe UI", 9))
        self.combo_ratio.set("Landscape (16:9)")
        self.combo_ratio.pack(side="left", padx=(5, 15))
        
        tk.Label(toolbar, text="Bản sao:", bg="#ecf0f1", font=("Segoe UI", 9)).pack(side="left")
        self.spin_count = tk.Spinbox(toolbar, from_=1, to=4, width=3, font=("Segoe UI", 9))
        self.spin_count.pack(side="left", padx=5)
        
        tk.Label(toolbar, text="Start Short:", bg="#ecf0f1", font=("Segoe UI", 9)).pack(side="left")
        self.spin_start_index = tk.Spinbox(toolbar, from_=1, to=1000, width=5, font=("Segoe UI", 9))
        self.spin_start_index.delete(0, "end")
        self.spin_start_index.insert(0, "1")
        self.spin_start_index.pack(side="left", padx=5)
        
        self.var_auto_download = tk.BooleanVar(value=False)
        def on_auto_download_toggle():
            if self.var_auto_download.get():
                folder = filedialog.askdirectory(title="Chọn thư mục lưu Auto Download")
                if folder:
                    self.auto_download_dir = folder
                    messagebox.showinfo("Info", f"Đã chọn thư mục lưu:\n{folder}")
                else:
                    self.var_auto_download.set(False)
            else:
                self.auto_download_dir = None

        tk.Checkbutton(toolbar, text="Auto Download", variable=self.var_auto_download, command=on_auto_download_toggle, bg="#ecf0f1", font=("Segoe UI", 9)).pack(side="left", padx=10)
        
        self.lbl_status = tk.Label(toolbar, text="Chờ import Excel...", bg="#ecf0f1", font=("Segoe UI", 10), fg="#7f8c8d")
        self.lbl_status.pack(side="right", padx=20)
        
        # Content Split View
        paned = tk.PanedWindow(self.parent, orient=tk.HORIZONTAL, bg="#cfd8dc", sashwidth=4)
        paned.pack(fill="both", expand=True, padx=10, pady=10)
        
        # LEFT PANEL - Queue
        left_panel = tk.LabelFrame(paned, text="📋 Queue", font=("Segoe UI", 10, "bold"), bg="white", fg="#2c3e50", padx=5, pady=5)
        
        tk.Label(left_panel, text=r"💡 Để file template cùng folder với ảnh thì chỉ việc nhập tên ảnh, để khác thì cần nhập đường dẫn đầy đủ vd: C:/Users/admin/Desktop/1.png", bg="#fff3cd", fg="#856404", font=("Segoe UI", 8), wraplength=280).pack(fill="x", pady=(0, 5))
        
        queue_container = tk.Frame(left_panel, bg="white")
        queue_container.pack(fill="both", expand=True)
        
        self.queue_canvas = tk.Canvas(queue_container, bg="white", highlightthickness=0)
        self.queue_scrollbar = ttk.Scrollbar(queue_container, orient="vertical", command=self.queue_canvas.yview)
        self.queue_list_frame = tk.Frame(self.queue_canvas, bg="white")
        
        self.queue_list_frame.bind("<Configure>", lambda e: self.queue_canvas.configure(scrollregion=self.queue_canvas.bbox("all")))
        self.queue_canvas.create_window((0, 0), window=self.queue_list_frame, anchor="nw", width=320)
        
        self.queue_canvas.configure(yscrollcommand=self.queue_scrollbar.set)
        self.queue_canvas.pack(side="left", fill="both", expand=True)
        self.queue_scrollbar.pack(side="right", fill="y")
        
        # RIGHT PANEL - Gallery
        right_panel = tk.LabelFrame(paned, text="⚡ Gallery", font=("Segoe UI", 10, "bold"), bg="white", fg="#2c3e50", padx=5, pady=5)
        
        progress_container = tk.Frame(right_panel, bg="white")
        progress_container.pack(fill="both", expand=True)
        
        self.progress_canvas = tk.Canvas(progress_container, bg="white", highlightthickness=0)
        self.progress_scrollbar = ttk.Scrollbar(progress_container, orient="vertical", command=self.progress_canvas.yview)
        self.progress_list_frame = tk.Frame(self.progress_canvas, bg="white")
        
        self.progress_list_frame.bind("<Configure>", lambda e: self.progress_canvas.configure(scrollregion=self.progress_canvas.bbox("all")))
        self.progress_canvas.create_window((0, 0), window=self.progress_list_frame, anchor="nw")
        
        self.progress_canvas.configure(yscrollcommand=self.progress_scrollbar.set)
        self.progress_canvas.pack(side="left", fill="both", expand=True)
        self.progress_scrollbar.pack(side="right", fill="y")
        
        btn_download_all = tk.Frame(right_panel, bg="white")
        btn_download_all.pack(fill="x", pady=(10, 0))
        RoundedButton(btn_download_all, text="📥 Tải tất cả Video", command=self.download_all_videos, width=150, height=35, bg_color="white", fg_color="#3498db", hover_color="#2980b9").pack(side="right")

        paned.add(left_panel, width=350)
        paned.add(right_panel, stretch="always")

        def _on_mousewheel(event):
            self.queue_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.queue_canvas.bind_all("<MouseWheel>", _on_mousewheel)

    def download_template(self):
        import pandas as pd
        save_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], initialfile="template_video.xlsx")
        if not save_path: return
        try:
            data = {"image": ["dog.jpg", "cat.png"], "prompt": ["cute dog", "cat playing"]}
            pd.DataFrame(data).to_excel(save_path, index=False)
            messagebox.showinfo("Success", f"Đã tạo template:\n{save_path}")
            os.startfile(os.path.dirname(save_path))
        except Exception as e:
            messagebox.showerror("Error", f"Lỗi: {e}")

    def import_excel(self):
        filepath = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if not filepath: return
        try:
            import pandas as pd
            df = pd.read_excel(filepath)
            if 'prompt' not in df.columns:
                messagebox.showerror("Error", "Cần cột 'prompt'!")
                return
            
            has_image_col = 'image' in df.columns
            self.app.job_queue = []
            base_dir = os.path.dirname(filepath)
            
            for idx, row in df.iterrows():
                image_path = None
                if has_image_col:
                    val = str(row['image']).strip()
                    if val and val.lower() not in ('nan', 'none', ''):
                        image_path = val if os.path.isabs(val) else os.path.join(base_dir, val)
                        if not os.path.exists(image_path): image_path = None
                
                prompt = str(row['prompt']).strip()
                self.app.job_queue.append({
                    'index': len(self.app.job_queue),
                    'image': image_path,
                    'prompt': prompt,
                    'status': 'pending',
                    'progress': 0
                })
                
            self.refresh_queue_preview()
            self.lbl_status.config(text=f"Đã import {len(self.app.job_queue)} jobs")
        except Exception as e:
            messagebox.showerror("Error", f"Lỗi Import: {e}")

    def refresh_queue_preview(self):
        for w in self.queue_list_frame.winfo_children(): w.destroy()
        self.app.thumbnail_cache = {}
        
        for idx, job in enumerate(self.app.job_queue):
            content = tk.Frame(self.queue_list_frame, bg="white", pady=5)
            content.pack(fill="x", padx=5)
            
            # Thumbnail Frame
            thumb_frame = tk.Frame(content, bg="#f5f5f5", width=60, height=45)
            thumb_frame.pack(side="left", padx=5)
            thumb_frame.pack_propagate(False)
            
            if job['image']:
                try:
                    img = Image.open(job['image'])
                    img.thumbnail((58, 43))
                    photo = ImageTk.PhotoImage(img)
                    self.app.thumbnail_cache[idx] = photo
                    tk.Label(thumb_frame, image=photo, bg="#f5f5f5").pack(expand=True)
                except:
                    tk.Label(thumb_frame, text="🖼", font=("Segoe UI", 14), bg="#f5f5f5", fg="#7f8c8d").pack(expand=True)
            else:
                tk.Label(thumb_frame, text="📝", font=("Segoe UI", 16), bg="#f5f5f5", fg="#3498db").pack(expand=True)
            
            info = tk.Frame(content, bg="white")
            info.pack(side="left", fill="both", expand=True)
            job_type = "Img2Vid" if job['image'] else "Txt2Vid"
            tk.Label(info, text=f"#{idx+1} {job_type}", font=("Segoe UI", 9, "bold"), bg="white").pack(anchor="w")
            tk.Label(info, text=job['prompt'][:25]+"...", font=("Segoe UI", 8), fg="#7f8c8d", bg="white").pack(anchor="w")
            
            st = job['status']
            status_map = {'pending': '⏳', 'processing': '⚙️', 'polling': '👀', 'success': '✅', 'failed': '❌'}
            colors = {'pending': '#f39c12', 'processing': '#3498db', 'polling': '#9b59b6', 'success': '#27ae60', 'failed': '#e74c3c'}
            
            tk.Label(content, text=status_map.get(st, st), fg=colors.get(st, 'black'), bg="white", font=("Segoe UI", 12)).pack(side="right", padx=5)
            
            ttk.Separator(self.queue_list_frame, orient="horizontal").pack(fill="x", padx=5)

    def start_batch(self):
        if not self.app.job_queue: return
        live_accounts = [a for a in self.app.account_manager.accounts if "Live" in a.get('status', '')]
        if not live_accounts:
            messagebox.showerror("Error", "Không có tài khoản Live!")
            return
            
        if self.var_auto_download.get() and not self.auto_download_dir:
            if not messagebox.askyesno("Warning", "Chưa chọn thư mục Auto Download! Tiếp tục?"): return
            self.var_auto_download.set(False)
            
        self.app.is_running = True
        
        # Use safe merge instead of reset to avoid conflict with Image Tab if running
        with self.app.lock:
            if not isinstance(self.app.running_jobs, dict): self.app.running_jobs = {}
            for acc in live_accounts:
                if acc['name'] not in self.app.running_jobs:
                    self.app.running_jobs[acc['name']] = []
        
        self.lbl_status.config(text=f"Đang chạy... ({len(live_accounts)} accounts)")
        threading.Thread(target=self.batch_worker, daemon=True).start()

    def stop_batch(self):
        self.app.is_running = False
        self.lbl_status.config(text="Đã dừng")

    def batch_worker(self):
        import time
        live_accounts = [a for a in self.app.account_manager.accounts if "Live" in a.get('status', '')]
        
        while self.app.is_running:
            pending = [j for j in self.app.job_queue if j['status'] == 'pending']
            if not pending:
                if not [j for j in self.app.job_queue if j['status'] in ('processing', 'polling')]:
                    self.app.root.after(0, lambda: self.lbl_status.config(text="Hoàn tất!"))
                    break
                time.sleep(1)
                continue
            
            for acc in live_accounts:
                if not self.app.is_running: break
                
                with self.app.lock:
                    if acc['name'] not in self.app.running_jobs: self.app.running_jobs[acc['name']] = []
                    cnt = len([j for j in self.app.job_queue if j.get('account') == acc['name'] and j['status'] in ('processing', 'polling')])
                
                if cnt < self.app.max_jobs_per_account:
                    job = next((j for j in self.app.job_queue if j['status'] == 'pending'), None)
                    if job:
                        job['status'] = 'processing'
                        job['account'] = acc['name']
                        self.app.root.after(0, self.refresh_queue_preview)
                        self.app.root.after(0, self.refresh_progress_panel)
                        threading.Thread(target=self.process_job, args=(job, acc), daemon=True).start()
            time.sleep(1)

    def process_job(self, job, account):
        import time
        try:
            api = LabsApiService()
            api.set_credentials(account['cookies'], account.get('access_token'))
            
            media_id = None
            if job['image']:
                res = api.upload_image(job['image'])
                media_id = res.get('mediaId')
                if not media_id: raise Exception("Upload failed")
            
            token = self.app.browser_service.fetch_recaptcha_token(account['cookies'], use_visible_browser=True)
            if not token: raise Exception("Failed Recaptcha")
            
            project_id = account.get('project_id')
            ratio_txt = self.combo_ratio.get()
            ratio = "VIDEO_ASPECT_RATIO_PORTRAIT" if "Portrait" in ratio_txt else "VIDEO_ASPECT_RATIO_LANDSCAPE"
            try: count = int(self.spin_count.get())
            except: count = 1
            
            if media_id:
                gen = api.generate_video(job['prompt'], media_id, ratio, count, project_id, token)
            else:
                gen = api.generate_video_text(job['prompt'], ratio, count, project_id, token)
            
            ops = gen.get('operations', [])
            if not ops: raise Exception("No operations")
            
            job['operation'] = ops[0]
            job['status'] = 'polling'
            job['progress'] = 10
            
            self.app.root.after(0, self.refresh_progress_panel)
            
            def simulate():
                for i in range(10, 95):
                    if job['status'] != 'polling' or not self.app.is_running: break
                    job['progress'] = i
                    self.app.root.after(0, self.refresh_progress_panel)
                    time.sleep(0.8)
            threading.Thread(target=simulate, daemon=True).start()
            
            while self.app.is_running:
                time.sleep(5)
                st_res = api.check_video_status(ops)
                if st_res and 'operations' in st_res:
                    op = st_res['operations'][0]
                    st = op.get('status')
                    if st == 'MEDIA_GENERATION_STATUS_SUCCESSFUL':
                        url = api.extract_video_url(op)
                        job['video_url'] = url
                        job['status'] = 'success'
                        job['progress'] = 100
                        
                        if self.var_auto_download.get() and self.auto_download_dir:
                            try:
                                start_idx = 1
                                try: start_idx = int(self.spin_start_index.get())
                                except: pass
                                f_idx = start_idx + job['index']
                                path = os.path.join(self.auto_download_dir, f"video_{f_idx}.mp4")
                                threading.Thread(target=lambda: api.download_video(url, path), daemon=True).start()
                            except: pass
                        break
                    elif st == 'MEDIA_GENERATION_STATUS_FAILED':
                        job['status'] = 'failed'
                        job['error'] = 'Failed'
                        break
        except Exception as e:
            job['status'] = 'failed'
            job['error'] = str(e)
        finally:
            self.app.root.after(0, self.refresh_queue_preview)
            self.app.root.after(0, self.refresh_progress_panel)

    def refresh_progress_panel(self):
        for w in self.progress_list_frame.winfo_children(): w.destroy()
        
        # Grid layout for active jobs
        active = [j for j in self.app.job_queue if j['status'] in ('processing', 'polling', 'success', 'failed')]
        cols = 3
        
        for idx, job in enumerate(active):
            r = idx // cols
            c = idx % cols
            self.create_progress_card(job, r, c)

    def create_progress_card(self, job, r, c):
        # Minimal Card Grid
        card = tk.Frame(self.progress_list_frame, bg="white", bd=1, relief="solid", width=200, height=180, cursor="hand2")
        card.grid(row=r, column=c, padx=8, pady=8)
        card.pack_propagate(False)
        
        # Header
        header = tk.Frame(card, bg="white", height=25)
        header.pack(fill="x", padx=5, pady=2)
        header.pack_propagate(False)
        
        tk.Label(header, text=f"#{job['index']+1}", font=("Segoe UI", 9, "bold"), fg="#7f8c8d", bg="white").pack(side="left")
        
        st = job['status']
        status_map = {'processing': '⚙️', 'polling': '👀', 'success': '✅', 'failed': '❌'}
        color_map = {'processing': '#3498db', 'polling': '#9b59b6', 'success': '#27ae60', 'failed': '#e74c3c'}
        
        tk.Label(header, text=status_map.get(st, st), fg=color_map.get(st, 'black'), bg="white", font=("Segoe UI", 12)).pack(side="right")
        
        # Content
        content = tk.Frame(card, bg="#f5f5f5")
        content.pack(fill="both", expand=True, padx=5, pady=5)
        
        def on_click(e):
            if job.get('video_url'):
                webbrowser.open(job['video_url'])
        
        card.bind("<Button-1>", on_click)
        content.bind("<Button-1>", on_click)
        
        if st in ('processing', 'polling'):
            prog = job.get('progress', 0)
            tk.Label(content, text=f"{int(prog)}%", font=("Segoe UI", 14, "bold"), bg="#f5f5f5", fg="#3498db").pack(expand=True)
            pb = tk.Frame(content, bg="#e0e0e0", height=4)
            pb.pack(fill="x", padx=10, pady=10)
            tk.Frame(pb, bg="#3498db", width=0).place(relx=0, rely=0, relwidth=prog/100, relheight=1)
        
        elif st == 'success' and job.get('video_url'):
            tk.Label(content, text="▶ VIDEO", font=("Segoe UI", 12, "bold"), bg="#f5f5f5", fg="#2c3e50").pack(expand=True)
            tk.Label(content, text="(Click to Open)", font=("Segoe UI", 8), bg="#f5f5f5", fg="gray").pack()
            
        elif st == 'failed':
            tk.Label(content, text=f"Failed", fg="red", bg="#f5f5f5").pack(expand=True)
            
        # Hover
        def on_enter(e): card.config(bg="#ecf0f1")
        def on_leave(e): card.config(bg="white")
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

    def download_all_videos(self):
        done = [j for j in self.app.job_queue if j['status'] == 'success' and j.get('video_url')]
        if not done: return
        folder = filedialog.askdirectory()
        if not folder: return
        
        try: start_idx = int(self.spin_start_index.get())
        except: start_idx = 1
        
        api = LabsApiService()
        for job in done:
            idx = start_idx + job['index']
            path = os.path.join(folder, f"video_{idx}.mp4")
            threading.Thread(target=lambda: api.download_video(job['video_url'], path), daemon=True).start()
