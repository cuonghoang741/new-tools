
import customtkinter as ctk
from tkinter import filedialog, messagebox
import threading
import os
from PIL import Image, ImageTk
from app.services.api_service import LabsApiService

class VideoScreen:
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
            text="Tạo Video (Batch)", 
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
        
        # Template button on right side
        ctk.CTkButton(
            right_opts,
            text="📥 Template",
            font=("SF Pro Display", 11),
            width=105,
            height=32,
            corner_radius=8,
            fg_color="#374151",
            hover_color="#4b5563",
            command=self.download_template
        ).pack(side="right", padx=(15, 0))

        # ctk.CTkButton(
        #     right_opts,
        #     text="🧪 Mock",
        #     font=("SF Pro Display", 11),
        #     width=60,
        #     height=32,
        #     corner_radius=8,
        #     fg_color="#374151",
        #     hover_color="#4b5563",
        #     command=self.add_mock_data
        # ).pack(side="right", padx=(15, 0))
        
        ctk.CTkLabel(
            right_opts, 
            text="Tỷ lệ:", 
            font=("SF Pro Display", 11),
            text_color="#a0a3bd"
        ).pack(side="left", padx=(0, 5))
        
        self.combo_ratio = ctk.CTkOptionMenu(
            right_opts,
            values=["Landscape (16:9)", "Portrait (9:16)"],
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
            text="💡 Đặt ảnh cùng folder với Excel để chỉ nhập tên file", 
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
        
        ctk.CTkButton(
            gallery_header,
            text="📥 Tải tất cả",
            font=("SF Pro Display", 11),
            width=100,
            height=32,
            corner_radius=8,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self.download_all_videos
        ).pack(side="right")
        
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

    def download_template(self):
        import pandas as pd
        save_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], initialfile="template_video.xlsx")
        if not save_path: return
        try:
            data = {"image": ["dog.jpg", "cat.png"], "prompt": ["cute dog", "cat playing"]}
            pd.DataFrame(data).to_excel(save_path, index=False)
            messagebox.showinfo("Success", f"✅ Đã tạo template:\n{save_path}")
            os.startfile(os.path.dirname(save_path))
        except Exception as e:
            messagebox.showerror("Error", f"Lỗi: {e}")

    def clear_queue(self):
        if not self.app.job_queue: return
        if self.app.is_running:
            messagebox.showwarning("Warning", "Đang chạy batch! Hãy STOP trước.")
            return
            
        if messagebox.askyesno("Xác nhận", "Xóa toàn bộ queue?"):
            self.app.job_queue = []
            self.refresh_queue_preview()
            self.refresh_progress_panel()
            self.lbl_status.configure(text="🗑️ Đã xóa queue")

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
                image_name = None
                if has_image_col:
                    val = str(row['image']).strip()
                    if val and val.lower() not in ('nan', 'none', ''):
                        image_path = val if os.path.isabs(val) else os.path.join(base_dir, val)
                        if not os.path.exists(image_path): image_path = None
                        else: image_name = os.path.splitext(os.path.basename(image_path))[0]
                
                prompt = str(row['prompt']).strip()
                self.app.job_queue.append({
                    'index': len(self.app.job_queue),
                    'image': image_path,
                    'image_name': image_name,
                    'prompt': prompt,
                    'status': 'pending',
                    'progress': 0
                })
                
            self.refresh_queue_preview()
            self.lbl_status.configure(text=f"✅ Đã import {len(self.app.job_queue)} jobs")
        except Exception as e:
            messagebox.showerror("Error", f"Lỗi Import: {e}")

    def refresh_queue_preview(self):
        for w in self.queue_scroll.winfo_children(): w.destroy()
        self.app.thumbnail_cache = {}
        
        total_jobs = len(self.app.job_queue)
        self.queue_count_label.configure(text=f"{total_jobs} jobs")
        
        # Pagination Logic
        total_pages = (total_jobs + self.queue_per_page - 1) // self.queue_per_page
        if total_pages < 1: total_pages = 1
        if self.queue_page > total_pages: self.queue_page = total_pages
        if self.queue_page < 1: self.queue_page = 1
        
        start = (self.queue_page - 1) * self.queue_per_page
        end = start + self.queue_per_page
        page_items = self.app.job_queue[start:end]
        
        # Update Controls
        self.lbl_page.configure(text=f"Page {self.queue_page}/{total_pages}")
        self.btn_prev.configure(state="normal" if self.queue_page > 1 else "disabled")
        self.btn_next.configure(state="normal" if self.queue_page < total_pages else "disabled")
        
        for idx, job in enumerate(page_items):
            # Pass absolute index to create_queue_item if needed, or just job object
            self.create_queue_item(job['index'], job)

    def prev_page(self):
        if self.queue_page > 1:
            self.queue_page -= 1
            self.refresh_queue_preview()

    def next_page(self):
        # Calculate max page
        total_jobs = len(self.app.job_queue)
        total_pages = (total_jobs + self.queue_per_page - 1) // self.queue_per_page
        if self.queue_page < total_pages:
            self.queue_page += 1
            self.refresh_queue_preview()

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
            try:
                img = Image.open(job['image'])
                img.thumbnail((48, 48))
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=(48, 48))
                self.app.thumbnail_cache[idx] = photo
                ctk.CTkLabel(thumb_frame, image=photo, text="").pack(expand=True)
            except:
                ctk.CTkLabel(thumb_frame, text="Img", font=("SF Pro Display", 11, "bold"), text_color="#6c7293").pack(expand=True)
        else:
            ctk.CTkLabel(thumb_frame, text="Txt", font=("SF Pro Display", 11, "bold"), text_color="#6366f1").pack(expand=True)
        
        # Info
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=10)
        
        job_type = "Img→Vid" if job['image'] else "Text→Vid"
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
            'polling': ('👁️', '#8b5cf6'),
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
                if self.app.is_running and self.app.job_queue[i]['status'] == 'processing':
                    messagebox.showwarning("Warning", "Không thể xóa job đang chạy!")
                    return
                self.app.job_queue.pop(i)
                for k, j in enumerate(self.app.job_queue): j['index'] = k
                self.refresh_queue_preview()
                self.refresh_progress_panel()
            
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
        if not self.app.job_queue: return
        live_accounts = [a for a in self.app.account_manager.accounts if "Live" in a.get('status', '')]
        if not live_accounts:
            messagebox.showerror("Error", "Không có tài khoản Live!")
            return
            
        if self.var_auto_download.get() and not self.auto_download_dir:
            if not messagebox.askyesno("Warning", "Chưa chọn thư mục Auto Download! Tiếp tục?"): return
            self.var_auto_download.set(False)
            
        self.app.is_running = True
        
        with self.app.lock:
            if not isinstance(self.app.running_jobs, dict): self.app.running_jobs = {}
            for acc in live_accounts:
                if acc['name'] not in self.app.running_jobs:
                    self.app.running_jobs[acc['name']] = []
        
        self.lbl_status.configure(text=f"🚀 Đang chạy... ({len(live_accounts)} accounts)")
        self.btn_start.configure(state="disabled", fg_color="#4a4a6a")
        threading.Thread(target=self.batch_worker, daemon=True).start()

    def stop_batch(self):
        self.app.is_running = False
        self.lbl_status.configure(text="⏹️ Đã dừng")
        self.btn_start.configure(state="normal", fg_color="#22c55e")

    def batch_worker(self):
        import time
        live_accounts = [a for a in self.app.account_manager.accounts if "Live" in a.get('status', '')]
        
        while self.app.is_running:
            pending = [j for j in self.app.job_queue if j['status'] == 'pending']
            if not pending:
                if not [j for j in self.app.job_queue if j['status'] in ('processing', 'polling')]:
                    self.app.browser_service.close_all_sessions()
                    self.app.is_running = False
                    self.app.root.after(0, lambda: [
                        self.lbl_status.configure(text="✅ Hoàn tất!"),
                        self.btn_start.configure(state="normal", fg_color="#22c55e")
                    ])
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
                        time.sleep(0.5)
            time.sleep(1)

    def process_job(self, job, account):
        import time
        try:
            api = LabsApiService()
            api.set_credentials(account['cookies'], account.get('access_token'))
            if not self.app.is_running: return
            
            media_id = None
            if job['image']:
                res = api.upload_image(job['image'])
                media_id = res.get('mediaId')
                if not media_id: raise Exception("Upload failed")
            
            token = self.app.browser_service.fetch_recaptcha_token(account['cookies'], account_id=account['name'], use_visible_browser=True)
            if not self.app.is_running: return
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
                                name = f"short_{job['image_name']}.mp4" if job.get('image_name') else f"video_{job['index']}.mp4"
                                path = os.path.join(self.auto_download_dir, name)
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
        for w in self.gallery_scroll.winfo_children(): w.destroy()
        
        active = [j for j in self.app.job_queue if j['status'] in ('processing', 'polling', 'success', 'failed')]
        
        # Create grid
        cols = 3
        row_frame = None
        
        for idx, job in enumerate(active):
            if idx % cols == 0:
                row_frame = ctk.CTkFrame(self.gallery_scroll, fg_color="transparent")
                row_frame.pack(fill="x", pady=5)
            
            self.create_progress_card(job, row_frame)

    def create_progress_card(self, job, parent):
        card = ctk.CTkFrame(parent, width=200, height=180, fg_color="#16213e", corner_radius=14)
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
            'polling': ('👁️', '#8b5cf6'),
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
            job['progress'] = 0
            self.refresh_queue_preview()
            self.refresh_progress_panel()
            
            # Run immediately in background
            import threading
            threading.Thread(target=self.process_job, args=(job, acc), daemon=True).start()
        
        if st in ('processing', 'polling'):
            prog = job.get('progress', 0)
            ctk.CTkLabel(
                content, 
                text=f"{int(prog)}%", 
                font=("SF Pro Display", 24, "bold"),
                text_color="#6366f1"
            ).pack(expand=True)
            
            progress_bar = ctk.CTkProgressBar(content, width=160, height=6, corner_radius=3, fg_color="#1a1a2e", progress_color="#6366f1")
            progress_bar.set(prog/100)
            progress_bar.pack(pady=(0, 15))
            
        elif st == 'success' and job.get('video_url'):
            # Thumbnail container
            thumb_frame = ctk.CTkFrame(content, fg_color="transparent", width=160, height=90)
            thumb_frame.pack(expand=True, pady=5)
            thumb_frame.pack_propagate(False)

            if 'thumb_video_ctk' not in job:
                ctk.CTkLabel(thumb_frame, text="Loading thumb...", font=("SF Pro Display", 11), text_color="#6c7293").place(relx=0.5, rely=0.5, anchor="center")
                
                def load_thumb():
                    try:
                        import cv2
                        cap = cv2.VideoCapture(job['video_url'])
                        ret, frame = cap.read()
                        cap.release()
                        if ret:
                            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            pil_img = Image.fromarray(frame)
                            pil_img.thumbnail((160, 90))
                            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
                            job['thumb_video_ctk'] = ctk_img
                            self.app.root.after(0, self.refresh_progress_panel)
                    except Exception as e:
                        print(f"Thumb error: {e}")

                threading.Thread(target=load_thumb, daemon=True).start()
            else:
                # Show thumbnail and Play overlay
                thumb_lbl = ctk.CTkLabel(thumb_frame, image=job['thumb_video_ctk'], text="")
                thumb_lbl.place(relx=0.5, rely=0.5, anchor="center")
                
                # Overlay Play Button
                # Overlay Play Button
                # Overlay Play Label (Cleaner than Button)
                play_lbl = ctk.CTkLabel(
                    thumb_frame,
                    text="▶",
                    width=40,
                    height=40,
                    fg_color="transparent",
                    text_color="#ffffff",
                    font=("SF Pro Display", 24),
                    cursor="hand2"
                )
                play_lbl.place(relx=0.5, rely=0.5, anchor="center")
                
                # Bind click events to both label and surrounding frame for better UX
                play_lbl.bind("<Button-1>", lambda e: self.play_video(job))
                thumb_lbl.bind("<Button-1>", lambda e: self.play_video(job))
            
        elif st == 'failed':
            ctk.CTkLabel(
                content, 
                text="Failed", 
                font=("SF Pro Display", 12),
                text_color="#ef4444"
            ).pack(expand=True, pady=(15, 5))
            
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
            ).pack(pady=(0, 15))

    def play_video(self, job):
        if not job.get('video_url'):
            return
        
        # Create video player popup
        player = ctk.CTkToplevel(self.app.root)
        player.title(f"Video Player - #{job['index']+1}")
        player.geometry("720x480")
        player.configure(fg_color="#0f0f23")
        player.transient(self.app.root)
        player.attributes("-topmost", True)  # Always on top
        player.lift()
        player.focus_force()
        
        # Video display
        video_frame = ctk.CTkFrame(player, fg_color="#000000", corner_radius=0)
        video_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        video_label = ctk.CTkLabel(video_frame, text="Loading...", text_color="#ffffff", font=("SF Pro Display", 14))
        video_label.pack(expand=True)
        
        # Controls
        controls = ctk.CTkFrame(player, fg_color="#1a1a2e", height=50, corner_radius=0)
        controls.pack(fill="x", padx=10, pady=(0, 10))
        controls.pack_propagate(False)
        
        ctrl_inner = ctk.CTkFrame(controls, fg_color="transparent")
        ctrl_inner.pack(expand=True)
        
        is_playing = [True]
        cap = [None]
        
        def stop_video():
            is_playing[0] = False
            if cap[0]:
                cap[0].release()
            player.destroy()
        
        ctk.CTkButton(
            ctrl_inner,
            text="⏹ Close",
            font=("SF Pro Display", 12, "bold"),
            width=100,
            height=35,
            corner_radius=8,
            fg_color="#ef4444",
            hover_color="#dc2626",
            command=stop_video
        ).pack(side="left", padx=10)
        
        # Open in browser button
        import webbrowser
        ctk.CTkButton(
            ctrl_inner,
            text="↗ Browser",
            font=("SF Pro Display", 12),
            width=100,
            height=35,
            corner_radius=8,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=lambda: webbrowser.open(job['video_url'])
        ).pack(side="left", padx=10)
        
        player.bind("<Escape>", lambda e: stop_video())
        player.protocol("WM_DELETE_WINDOW", stop_video)
        
        def play_thread():
            try:
                import cv2
                cap[0] = cv2.VideoCapture(job['video_url'])
                
                if not cap[0].isOpened():
                    player.after(0, lambda: video_label.configure(text="Cannot load video"))
                    return
                
                fps = cap[0].get(cv2.CAP_PROP_FPS) or 30
                delay = int(1000 / fps)
                
                while is_playing[0] and cap[0].isOpened():
                    ret, frame = cap[0].read()
                    if not ret:
                        cap[0].set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    
                    # Resize to fit
                    h, w = frame.shape[:2]
                    max_w, max_h = 700, 380
                    scale = min(max_w/w, max_h/h)
                    new_w, new_h = int(w*scale), int(h*scale)
                    frame = cv2.resize(frame, (new_w, new_h))
                    
                    # Convert to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                    photo = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
                    
                    if is_playing[0]:
                        player.after(0, lambda p=photo: video_label.configure(image=p, text=""))
                    
                    cv2.waitKey(delay)
                    
            except ImportError:
                player.after(0, lambda: video_label.configure(text="OpenCV not installed!\nOpening in browser..."))
                player.after(2000, lambda: [webbrowser.open(job['video_url']), player.destroy()])
            except Exception as e:
                player.after(0, lambda: video_label.configure(text=f"Error: {str(e)[:50]}"))
        
        threading.Thread(target=play_thread, daemon=True).start()

    def download_all_videos(self):
        done = [j for j in self.app.job_queue if j['status'] == 'success' and j.get('video_url')]
        if not done:
            messagebox.showinfo("Info", "Chưa có video nào hoàn thành!")
            return
            
    def add_mock_data(self):
        mocks = [
            {
                "prompt": "Mock Test Video 1",
                "image": None,
                "video_url": "https://www.gstatic.com/aitestkitchen/website/flow/banners/20250814_0325_d1a5b056_bg.mp4",
                "status": "success",
                "progress": 100
            },
            {
                "prompt": "Mock Test Video 2",
                "image": None,
                "video_url": "https://www.gstatic.com/aitestkitchen/website/flow/banners/flow31_bg_05905f5a.mp4",
                "status": "success",
                "progress": 100
            }
        ]
        
        for m in mocks:
            idx = len(self.app.job_queue)
            m['index'] = idx
            self.app.job_queue.append(m)
            
        self.refresh_queue_preview()
        self.refresh_progress_panel()
        messagebox.showinfo("Mock Mode", "Đã thêm 2 video test!")
        
    def clear_queue(self):
        # Keep only processing, polling or success jobs that user wants to keep?
        # Typically "Clear Queue" clears pending and failed.
        # But user might want to clear EVERYTHING except processing.
        
        running = [j for j in self.app.job_queue if j['status'] in ('processing', 'polling')]
        if running:
            # If jobs are running, only clear others
            new_q = running
            self.app.job_queue = new_q
            self.refresh_queue_preview()
            self.refresh_progress_panel()
        else:
            self.app.job_queue = []
            self.refresh_queue_preview()
            self.refresh_progress_panel()
            
        # Re-index
        for i, j in enumerate(self.app.job_queue): j['index'] = i
        folder = filedialog.askdirectory()
        if not folder: return
        
        api = LabsApiService()
        for job in done:
            name = f"short_{job['image_name']}.mp4" if job.get('image_name') else f"video_{job['index']}.mp4"
            path = os.path.join(folder, name)
            url = job['video_url']
            threading.Thread(target=lambda u=url, p=path: api.download_video(u, p), daemon=True).start()
        
        messagebox.showinfo("Info", f"⬇️ Đang tải {len(done)} video...")
