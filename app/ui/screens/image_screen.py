
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
from PIL import Image, ImageTk
from app.services.api_service import LabsApiService
import requests
from io import BytesIO

class ImageScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.auto_download_dir = None
        self.queue_page = 1
        self.queue_per_page = 20
        self.setup_ui()

    def setup_ui(self):
        # Header
        header = ctk.CTkFrame(self.parent, fg_color="transparent", height=60)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header, 
            text="Tạo Ảnh (Batch)", 
            font=("SF Pro Display", 22, "bold"),
            text_color="#ffffff"
        ).pack(side="left")
        
        self.lbl_status = ctk.CTkLabel(
            header, 
            text="Chờ import Excel...", 
            font=("SF Pro Display", 12),
            text_color="#6c7293"
        )
        self.lbl_status.pack(side="right", padx=10)
        
        # Toolbar
        toolbar = ctk.CTkFrame(self.parent, fg_color="#1a1a2e", corner_radius=12, height=65)
        toolbar.pack(fill="x", pady=(0, 15))
        toolbar.pack_propagate(False)
        
        toolbar_inner = ctk.CTkFrame(toolbar, fg_color="transparent")
        toolbar_inner.pack(fill="x", padx=15, pady=12)
        
        # Left buttons
        left_btns = ctk.CTkFrame(toolbar_inner, fg_color="transparent")
        left_btns.pack(side="left")
        
        ctk.CTkButton(
            left_btns,
            text="📂 Import",
            font=("SF Pro Display", 12, "bold"),
            width=100,
            height=38,
            corner_radius=10,
            fg_color="#f97316",
            hover_color="#ea580c",
            command=self.import_excel
        ).pack(side="left", padx=5)
        
        self.btn_start = ctk.CTkButton(
            left_btns,
            text="▶ START",
            font=("SF Pro Display", 12, "bold"),
            width=100,
            height=38,
            corner_radius=10,
            fg_color="#22c55e",
            hover_color="#16a34a",
            command=self.start_batch
        )
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_stop = ctk.CTkButton(
            left_btns,
            text="⏹️ STOP",
            font=("SF Pro Display", 12, "bold"),
            width=100,
            height=38,
            corner_radius=10,
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=self.stop_batch
        )
        self.btn_stop.pack(side="left", padx=5)
        
        # Right options
        right_opts = ctk.CTkFrame(toolbar_inner, fg_color="transparent")
        right_opts.pack(side="right")
        
        ctk.CTkLabel(
            right_opts, 
            text="Tỷ lệ:", 
            font=("SF Pro Display", 11),
            text_color="#a0a3bd"
        ).pack(side="left", padx=(0, 5))
        
        self.combo_ratio = ctk.CTkOptionMenu(
            right_opts,
            values=["Landscape (16:9)", "Portrait (9:16)", "Square (1:1)"],
            font=("SF Pro Display", 11),
            width=140,
            height=32,
            corner_radius=8,
            fg_color="#16213e",
            button_color="#6366f1",
            button_hover_color="#5855eb"
        )
        self.combo_ratio.set("Landscape (16:9)")
        self.combo_ratio.pack(side="left", padx=5)
        
        ctk.CTkLabel(
            right_opts, 
            text="Copies:", 
            font=("SF Pro Display", 11),
            text_color="#a0a3bd"
        ).pack(side="left", padx=(15, 5))
        
        self.spin_count = ctk.CTkOptionMenu(
            right_opts,
            values=["1", "2", "3", "4"],
            font=("SF Pro Display", 11),
            width=60,
            height=32,
            corner_radius=8,
            fg_color="#16213e",
            button_color="#6366f1"
        )
        self.spin_count.set("1")
        self.spin_count.pack(side="left", padx=5)
        
        self.var_auto_download = ctk.BooleanVar(value=False)
        self.chk_auto = ctk.CTkCheckBox(
            right_opts,
            text="Auto Download",
            font=("SF Pro Display", 11),
            text_color="#a0a3bd",
            variable=self.var_auto_download,
            command=self.on_auto_download_toggle,
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=5,
            fg_color="#6366f1",
            hover_color="#5855eb"
        )
        self.chk_auto.pack(side="left", padx=15)
        
        # Content: Split View
        content = ctk.CTkFrame(self.parent, fg_color="transparent")
        content.pack(fill="both", expand=True)
        
        # LEFT: Queue Panel
        left_panel = ctk.CTkFrame(content, fg_color="#1a1a2e", corner_radius=16, width=380)
        left_panel.pack(side="left", fill="y", padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Queue Header
        queue_header = ctk.CTkFrame(left_panel, fg_color="transparent", height=50)
        queue_header.pack(fill="x", padx=15, pady=(15, 10))
        queue_header.pack_propagate(False)
        
        ctk.CTkLabel(
            queue_header, 
            text="📋 Queue", 
            font=("SF Pro Display", 15, "bold"),
            text_color="#ffffff"
        ).pack(side="left")
        
        self.queue_count_label = ctk.CTkLabel(
            queue_header, 
            text="0 jobs", 
            font=("SF Pro Display", 11),
            text_color="#6c7293"
        )
        self.queue_count_label.pack(side="right")
        
        ctk.CTkButton(
            queue_header,
            text="🗑️ Clear",
            font=("SF Pro Display", 10),
            width=60,
            height=24,
            corner_radius=6,
            fg_color="#374151",
            hover_color="#4b5563",
            command=self.clear_queue
        ).pack(side="right", padx=(0, 10))
        
        # Tip
        tip = ctk.CTkLabel(
            left_panel, 
            text="💡 Cột 'prompt' bắt buộc, 'image' tùy chọn (Image2Image)", 
            font=("SF Pro Display", 10),
            text_color="#6c7293",
            wraplength=340
        )
        tip.pack(fill="x", padx=15, pady=(0, 10))
        
        # Queue List
        self.queue_scroll = ctk.CTkScrollableFrame(
            left_panel, 
            fg_color="transparent",
            scrollbar_button_color="#3a3a5e"
        )
        self.queue_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        # Pagination Controls
        pag_frame = ctk.CTkFrame(left_panel, fg_color="transparent", height=30)
        pag_frame.pack(fill="x", padx=10, pady=(0, 15))
        
        self.btn_prev = ctk.CTkButton(pag_frame, text="<", width=30, height=24, fg_color="#374151", command=self.prev_page, state="disabled")
        self.btn_prev.pack(side="left")
        
        self.lbl_page = ctk.CTkLabel(pag_frame, text="Page 1", font=("SF Pro Display", 11), text_color="#6c7293")
        self.lbl_page.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(pag_frame, text=">", width=30, height=24, fg_color="#374151", command=self.next_page, state="disabled")
        self.btn_next.pack(side="right")
        
        # RIGHT: Gallery Panel
        right_panel = ctk.CTkFrame(content, fg_color="#1a1a2e", corner_radius=16)
        right_panel.pack(side="left", fill="both", expand=True)
        
        # Gallery Header
        gallery_header = ctk.CTkFrame(right_panel, fg_color="transparent", height=50)
        gallery_header.pack(fill="x", padx=15, pady=(15, 10))
        gallery_header.pack_propagate(False)
        
        ctk.CTkLabel(
            gallery_header, 
            text="⚡ Gallery", 
            font=("SF Pro Display", 15, "bold"),
            text_color="#ffffff"
        ).pack(side="left")
        
        # Gallery Grid
        self.gallery_scroll = ctk.CTkScrollableFrame(
            right_panel, 
            fg_color="transparent",
            scrollbar_button_color="#3a3a5e"
        )
        self.gallery_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))

    def on_auto_download_toggle(self):
        if self.var_auto_download.get():
            folder = filedialog.askdirectory(title="Chọn thư mục lưu Auto Download")
            if folder:
                self.auto_download_dir = folder
                messagebox.showinfo("Info", f"Đã chọn thư mục:\n{folder}")
            else:
                self.var_auto_download.set(False)
        else:
            self.auto_download_dir = None

    def import_excel(self):
        filepath = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if not filepath: return
        try:
            import pandas as pd
            df = pd.read_excel(filepath)
            if 'prompt' not in df.columns:
                messagebox.showerror("Error", "Cần cột 'prompt'!")
                return
            
            has_img = 'image' in df.columns
            self.app.image_job_queue = []
            base_dir = os.path.dirname(filepath)
            
            for idx, row in df.iterrows():
                img_path = None
                if has_img:
                    val = str(row['image']).strip()
                    if val and val.lower() not in ('nan', 'none', ''):
                        img_path = val if os.path.isabs(val) else os.path.join(base_dir, val)
                        if not os.path.exists(img_path): img_path = None
                
                self.app.image_job_queue.append({
                    'index': len(self.app.image_job_queue),
                    'prompt': str(row['prompt']).strip(),
                    'image': img_path,
                    'status': 'pending'
                })
            
            self.refresh_queue()
            self.lbl_status.configure(text=f"✅ Jobs: {len(self.app.image_job_queue)}")
        except Exception as e:
            messagebox.showerror("Error", f"Lỗi: {e}")

    def refresh_queue(self):
        for w in self.queue_scroll.winfo_children(): w.destroy()
        
        total_jobs = len(self.app.image_job_queue)
        self.queue_count_label.configure(text=f"{total_jobs} jobs")
        
        # Pagination Logic
        total_pages = (total_jobs + self.queue_per_page - 1) // self.queue_per_page
        if total_pages < 1: total_pages = 1
        if self.queue_page > total_pages: self.queue_page = total_pages
        if self.queue_page < 1: self.queue_page = 1
        
        start = (self.queue_page - 1) * self.queue_per_page
        end = start + self.queue_per_page
        page_items = self.app.image_job_queue[start:end]
        
        # Update Controls
        self.lbl_page.configure(text=f"Page {self.queue_page}/{total_pages}")
        self.btn_prev.configure(state="normal" if self.queue_page > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.queue_page < total_pages else "disabled")
        
        for idx, job in enumerate(page_items):
            self.create_queue_item(job['index'], job)

    def prev_page(self):
        if self.queue_page > 1:
            self.queue_page -= 1
            self.refresh_queue()

    def next_page(self):
        # Calculate max page
        total_jobs = len(self.app.image_job_queue)
        total_pages = (total_jobs + self.queue_per_page - 1) // self.queue_per_page
        if self.queue_page < total_pages:
            self.queue_page += 1
            self.refresh_queue()

    def create_queue_item(self, idx, job):
        item = ctk.CTkFrame(self.queue_scroll, fg_color="#16213e", corner_radius=12, height=70)
        item.pack(fill="x", pady=4)
        item.pack_propagate(False)
        
        inner = ctk.CTkFrame(item, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)
        
        # Thumbnail
        thumb_frame = ctk.CTkFrame(inner, width=50, height=50, fg_color="#2a2a4e", corner_radius=8)
        thumb_frame.pack(side="left")
        thumb_frame.pack_propagate(False)
        
        if job['image']:
            thumb_key = f"img_in_{idx}_{id(job)}"
            if thumb_key in self.app.thumbnail_cache:
                ctk.CTkLabel(thumb_frame, image=self.app.thumbnail_cache[thumb_key], text="").pack(expand=True)
            else:
                try:
                    img = Image.open(job['image'])
                    img.thumbnail((48, 48))
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=(48, 48))
                    self.app.thumbnail_cache[thumb_key] = photo
                    ctk.CTkLabel(thumb_frame, image=photo, text="").pack(expand=True)
                except:
                    ctk.CTkLabel(thumb_frame, text="Img", font=("SF Pro Display", 11, "bold"), text_color="#6c7293").pack(expand=True)
        else:
            ctk.CTkLabel(thumb_frame, text="Txt", font=("SF Pro Display", 11, "bold"), text_color="#6366f1").pack(expand=True)
        
        # Info
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=10)
        
        job_type = "Img→Img" if job['image'] else "Text→Img"
        ctk.CTkLabel(
            info, 
            text=f"#{idx+1} {job_type}", 
            font=("SF Pro Display", 12, "bold"),
            text_color="#ffffff",
            anchor="w"
        ).pack(fill="x")
        
        ctk.CTkLabel(
            info, 
            text=job['prompt'][:30] + ("..." if len(job['prompt']) > 30 else ""), 
            font=("SF Pro Display", 10),
            text_color="#6c7293",
            anchor="w"
        ).pack(fill="x")
        
        # Status + Delete
        st = job['status']
        status_config = {
            'pending': ('⏳', '#f59e0b'),
            'processing': ('⚙️', '#3b82f6'),
            'success': ('✅', '#22c55e'),
            'failed': ('⛔', '#ef4444')
        }
        icon, color = status_config.get(st, ('○', '#6c7293'))
        
        right_frame = ctk.CTkFrame(inner, fg_color="transparent")
        right_frame.pack(side="right")
        
        ctk.CTkLabel(
            right_frame, 
            text=icon, 
            font=("SF Pro Display", 16, "bold"),
            text_color=color
        ).pack(side="left", padx=0)
        
        # Delete button for pending/failed
        if st in ('pending', 'failed'):
            def remove_job(i=idx):
                if self.app.is_image_running and self.app.image_job_queue[i]['status'] == 'processing':
                    messagebox.showwarning("Warning", "Không thể xóa job đang chạy!")
                    return
                self.app.image_job_queue.pop(i)
                for k, j in enumerate(self.app.image_job_queue): j['index'] = k
                self.refresh_queue()
                self.refresh_progress()
            
            del_btn = ctk.CTkButton(
                right_frame,
                text="✕",
                width=28,
                height=28,
                corner_radius=6,
                fg_color="transparent",
                hover_color="#ef4444",
                text_color="#6c7293",
                font=("SF Pro Display", 14, "bold"),
                command=remove_job
            )
            del_btn.pack(side="left", padx=0)

    def start_batch(self):
        if not self.app.image_job_queue: return
        if self.var_auto_download.get() and not self.auto_download_dir:
            if not messagebox.askyesno("Warning", "Chưa chọn thư mục Auto Download! Tiếp tục?"): return
            self.var_auto_download.set(False)
            
        self.app.is_image_running = True
        self.lbl_status.configure(text="🚀 Đang chạy...")
        self.btn_start.configure(state="disabled", fg_color="#4a4a6a")
        threading.Thread(target=self.batch_worker, daemon=True).start()

    def stop_batch(self):
        self.app.is_image_running = False
        self.lbl_status.configure(text="⏹️ Đã dừng")
        self.btn_start.configure(state="normal", fg_color="#22c55e")

    def batch_worker(self):
        import time
        live_accounts = [a for a in self.app.account_manager.accounts if "Live" in a.get('status','')]
        max_concurrent = 4  # Max 4 jobs at a time like video
        
        while self.app.is_image_running:
            pending = [j for j in self.app.image_job_queue if j['status'] == 'pending']
            processing = [j for j in self.app.image_job_queue if j['status'] == 'processing']
            
            if not pending:
                if not processing:
                    self.app.browser_service.close_all_sessions()
                    self.app.root.after(0, lambda: [
                        self.lbl_status.configure(text="✅ Hoàn tất!"),
                        self.btn_start.configure(state="normal", fg_color="#22c55e")
                    ])
                    break
                time.sleep(1)
                continue
            
            # Check if we can start more jobs
            if len(processing) >= max_concurrent:
                time.sleep(1)
                continue
            
            for acc in live_accounts:
                if not self.app.is_image_running: break
                if len(processing) >= max_concurrent: break
                
                with self.app.lock:
                    if acc['name'] not in self.app.running_jobs:
                        self.app.running_jobs[acc['name']] = []
                        
                with self.app.lock:
                    cnt = len(self.app.running_jobs.get(acc['name'], []))
                
                if cnt < self.app.max_jobs_per_account:
                    job = next((j for j in self.app.image_job_queue if j['status'] == 'pending'), None)
                    if job:
                        job['status'] = 'processing'
                        job['account'] = acc['name']
                        processing.append(job)  # Track locally too
                        with self.app.lock:
                            if acc['name'] not in self.app.running_jobs: self.app.running_jobs[acc['name']] = []
                        
                        self.app.root.after(0, self.refresh_queue)
                        self.app.root.after(0, self.refresh_progress)
                        threading.Thread(target=self.process_job, args=(job, acc), daemon=True).start()
            time.sleep(1)

    def process_job(self, job, account):
        try:
            api = LabsApiService()
            api.set_credentials(account['cookies'], account.get('access_token'))
            project_id = account.get('project_id')
            
            print("[DEBUG] Preparing Image Generation...")
            session_id = api.prepare_image_generation()
            
            media_id = None
            if job['image']:
                up = api.upload_image(job['image'])
                media_id = up.get('mediaId')
            
            # Use IMAGE_GENERATION action for recaptcha
            token = self.app.browser_service.fetch_recaptcha_token_with_project(account['cookies'], project_id, account_id=account['name'], use_visible_browser=True, action='IMAGE_GENERATION')
            if not token: raise Exception("No Recaptcha Token")
            
            ratio_map = {"Landscape (16:9)":"IMAGE_ASPECT_RATIO_LANDSCAPE", "Portrait (9:16)":"IMAGE_ASPECT_RATIO_PORTRAIT", "Square (1:1)":"IMAGE_ASPECT_RATIO_SQUARE"}
            ratio = ratio_map.get(self.combo_ratio.get(), "IMAGE_ASPECT_RATIO_LANDSCAPE")
            try: count = int(self.spin_count.get())
            except: count = 1
            
            res = api.generate_image_batch(job['prompt'], ratio, count, project_id, token, media_id, session_id=session_id)
            
            urls = []
            for m in res.get('media', []):
                u = m.get('image', {}).get('generatedImage', {}).get('fifeUrl')
                if u: urls.append(u)
            
            if not urls: raise Exception("No URL")
            
            job['status'] = 'success'
            job['video_url'] = urls[0]
            job['all_urls'] = urls
            
            if self.var_auto_download.get() and self.auto_download_dir:
                for k, u in enumerate(urls):
                    path = os.path.join(self.auto_download_dir, f"img_{job['index']}_{k+1}.png")
                    with open(path, 'wb') as f: f.write(requests.get(u).content)
                    
        except Exception as e:
            job['status'] = 'failed'
            job['error'] = str(e)
        finally:
            with self.app.lock:
                pass
            self.app.root.after(0, self.refresh_queue)
            self.app.root.after(0, self.refresh_progress)

    def refresh_progress(self):
        for w in self.gallery_scroll.winfo_children(): w.destroy()
        
        jobs = [j for j in self.app.image_job_queue if j['status'] != 'pending']
        
        # Create grid
        cols = 3
        row_frame = None
        
        for idx, job in enumerate(jobs):
            if idx % cols == 0:
                row_frame = ctk.CTkFrame(self.gallery_scroll, fg_color="transparent")
                row_frame.pack(fill="x", pady=5)
            
            self.create_image_progress_card(job, row_frame)

    def create_image_progress_card(self, job, parent):
        card = ctk.CTkFrame(parent, width=200, height=200, fg_color="#16213e", corner_radius=14)
        card.pack(side="left", padx=6, pady=4)
        card.pack_propagate(False)
        
        # Header
        header = ctk.CTkFrame(card, fg_color="transparent", height=35)
        header.pack(fill="x", padx=12, pady=(10, 5))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header, 
            text=f"#{job['index']+1}", 
            font=("SF Pro Display", 11, "bold"),
            text_color="#6c7293"
        ).pack(side="left")
        
        st = job['status']
        status_config = {
            'processing': ('⚙️', '#3b82f6'),
            'success': ('✅', '#22c55e'),
            'failed': ('⛔', '#ef4444')
        }
        icon, color = status_config.get(st, ('⏳', '#6c7293'))
        
        ctk.CTkLabel(
            header, 
            text=icon, 
            font=("SF Pro Display", 14, "bold"),
            text_color=color
        ).pack(side="right")
        
        # Content
        content = ctk.CTkFrame(card, fg_color="#2a2a4e", corner_radius=10)
        content.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        def retry():
            # Find a live account to retry with
            live_accounts = [a for a in self.app.account_manager.accounts if "Live" in a.get('status', '')]
            if not live_accounts:
                from tkinter import messagebox
                messagebox.showerror("Error", "Không có tài khoản Live!")
                return
            
            acc = live_accounts[0]
            job['status'] = 'processing'
            job['error'] = None
            job['account'] = acc['name']
            self.refresh_queue()
            self.refresh_progress()
            
            # Run immediately in background
            import threading
            threading.Thread(target=self.process_job, args=(job, acc), daemon=True).start()
        
        if st == 'failed':
            ctk.CTkLabel(
                content, 
                text="Failed", 
                font=("SF Pro Display", 12),
                text_color="#ef4444"
            ).pack(expand=True, pady=(20, 5))
            
            ctk.CTkButton(
                content,
                text="🔄 Retry",
                font=("SF Pro Display", 11),
                width=70,
                height=28,
                corner_radius=6,
                fg_color="#374151",
                hover_color="#4b5563",
                command=retry
            ).pack(pady=(0, 20))
            
        elif st == 'success' and job.get('video_url'):
            # Load and show thumbnail
            if 'thumb_preview_ctk' not in job:
                ctk.CTkLabel(
                    content, 
                    text="⏳ Loading...", 
                    font=("SF Pro Display", 11),
                    text_color="#6c7293"
                ).pack(expand=True)
                
                def load():
                    try:
                        r = requests.get(job['video_url'], timeout=10)
                        img = Image.open(BytesIO(r.content))
                        img.thumbnail((180, 130))
                        p = ctk.CTkImage(light_image=img, dark_image=img, size=(180, 130))
                        job['thumb_preview_ctk'] = p
                        self.app.root.after(0, self.refresh_progress)
                    except: pass
                threading.Thread(target=load, daemon=True).start()
            else:
                lbl = ctk.CTkLabel(content, image=job['thumb_preview_ctk'], text="", cursor="hand2")
                lbl.pack(expand=True, pady=5)
                lbl.bind("<Button-1>", lambda e: self.show_lightbox(job['video_url']))
        else:
            # Processing
            ctk.CTkLabel(
                content, 
                text="⚙️", 
                font=("Segoe UI Emoji", 28)
            ).pack(expand=True)
            ctk.CTkLabel(
                content, 
                text="Generating...", 
                font=("SF Pro Display", 11),
                text_color="#6c7293"
            ).pack(pady=(0, 15))

    def show_lightbox(self, img_url):
        top = ctk.CTkToplevel(self.app.root)
        top.title("Preview Image")
        top.attributes("-topmost", True)  # Always on top
        top.lift()
        top.focus_force()
        
        try: top.state("zoomed")
        except: top.attributes("-fullscreen", True)
        top.configure(fg_color="#000000")
        
        top.bind("<Escape>", lambda e: top.destroy())
        top.bind("<Button-1>", lambda e: top.destroy())
        
        lbl = ctk.CTkLabel(
            top, 
            text="⏳ Loading full quality...", 
            font=("SF Pro Display", 16),
            text_color="#ffffff"
        )
        lbl.pack(expand=True)
        
        def load():
            try:
                resp = requests.get(img_url)
                pil_img = Image.open(BytesIO(resp.content))
                
                sw, sh = top.winfo_screenwidth(), top.winfo_screenheight()
                ratio = min(sw/pil_img.width, sh/pil_img.height)
                if ratio < 1:
                    nw, nh = int(pil_img.width * ratio * 0.9), int(pil_img.height * ratio * 0.9)
                    pil_img = pil_img.resize((nw, nh), Image.Resampling.LANCZOS)
                
                photo = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(pil_img.width, pil_img.height))
                self.app.root.after(0, lambda: lbl.configure(image=photo, text=""))
            except Exception as e:
                self.app.root.after(0, lambda: lbl.configure(text=f"❌ Error: {e}"))
                
        threading.Thread(target=load, daemon=True).start()

    def clear_queue(self):
        running = [j for j in self.app.image_job_queue if j['status'] in ('processing', 'polling')]
        if running:
            new_q = running
            self.app.image_job_queue = new_q
            self.refresh_queue()
            self.refresh_progress()
        else:
            self.app.image_job_queue = []
            self.refresh_queue()
            self.refresh_progress()
            
        for i, j in enumerate(self.app.image_job_queue): j['index'] = i
