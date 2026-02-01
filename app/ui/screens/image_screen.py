
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
        self.job_cards = {} # Cache for progress cards {job_index: {frame, refs, last_state_tuple}}
        self.queue_row_pool = [] # Pool of widgets for queue list items
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

        # # Test 2K Button
        # ctk.CTkButton(
        #     left_btns,
        #     text="Test 2K",
        #     font=("SF Pro Display", 12, "bold"),
        #     width=80,
        #     height=38,
        #     corner_radius=10,
        #     command=self.test_upscale_2k,
        #     fg_color="#8b5cf6",
        #     hover_color="#7c3aed"
        # ).pack(side="left", padx=(5, 0))
        
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
        # ).pack(side="left", padx=(5, 5))
        
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

        ctk.CTkButton(
            gallery_header,
            text="📥 Tải tất cả",
            font=("SF Pro Display", 11),
            width=90,
            height=32,
            corner_radius=8,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self.download_all_images
        ).pack(side="right", padx=(5, 0))
        
        self.btn_download_all_4k = ctk.CTkButton(
            gallery_header,
            text="📥 All 4K",
            font=("SF Pro Display", 10, "bold"),
            width=70,
            height=32,
            corner_radius=8,
            fg_color="#ec4899",
            hover_color="#db2777",
            command=lambda: self.download_all_upscaled("4K")
        )
        self.btn_download_all_4k.pack(side="right", padx=(5, 0))
        
        self.btn_download_all_2k = ctk.CTkButton(
            gallery_header,
            text="📥 All 2K",
            font=("SF Pro Display", 10, "bold"),
            width=70,
            height=32,
            corner_radius=8,
            fg_color="#8b5cf6",
            hover_color="#7c3aed",
            command=lambda: self.download_all_upscaled("2K")
        )
        self.btn_download_all_2k.pack(side="right", padx=(5, 0))
        
        # Gallery Grid
        self.gallery_scroll = ctk.CTkScrollableFrame(
            right_panel, 
            fg_color="transparent",
            scrollbar_button_color="#3a3a5e"
        )
        self.gallery_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))

    def download_all_images(self):
        done = [j for j in self.app.image_job_queue if j['status'] == 'success' and j.get('all_urls')]
        if not done:
            messagebox.showinfo("Info", "Chưa có ảnh nào hoàn thành!")
            return
            
        folder = filedialog.askdirectory()
        if not folder: return
        
        count = 0
        for job in done:
             try:
                 for k, u in enumerate(job['all_urls']):
                     name = f"img_{job['index']}_{k+1}.png"
                     path = os.path.join(folder, name)
                     # Download in separate threads to not block UI, but maybe limit concurrency in real app
                     # For now, just spawn threads as requested by "similar to video tab"
                     threading.Thread(target=lambda u=u, p=path: self._download_file(u, p), daemon=True).start()
                     count += 1
             except: pass
        
        messagebox.showinfo("Info", f"⬇️ Đang bắt đầu tải {count} ảnh...")

    def download_all_upscaled(self, resolution="2K"):
        """Download all successful images in 2K or 4K resolution"""
        done = [j for j in self.app.image_job_queue if j['status'] == 'success' and j.get('mediaId')]
        if not done:
            messagebox.showinfo("Info", "Chưa có ảnh nào hoàn thành!")
            return
            
        folder = filedialog.askdirectory(title=f"Chọn thư mục lưu ảnh {resolution}")
        if not folder: return
        
        # Get button reference for loading state
        btn = self.btn_download_all_2k if resolution == "2K" else self.btn_download_all_4k
        original_color = "#8b5cf6" if resolution == "2K" else "#ec4899"
        original_text = f"📥 All {resolution}"
        
        def update_btn(text, loading=False):
            self.app.root.after(0, lambda: btn.configure(
                text=text,
                state="disabled" if loading else "normal",
                fg_color="#4b5563" if loading else original_color
            ))
        
        def task():
            try:
                update_btn(f"⏳ 0/{len(done)}", True)
                
                # Find a live account
                live = [a for a in self.app.account_manager.accounts if "Live" in a.get('status', '')]
                if not live:
                    raise Exception("Cần ít nhất 1 tài khoản Live!")
                
                acc = live[0]
                project_id = acc.get('project_id')
                
                api = LabsApiService()
                api.set_credentials(acc['cookies'], acc.get('access_token'))
                
                success_count = 0
                
                for i, job in enumerate(done):
                    try:
                        update_btn(f"⏳ {i+1}/{len(done)}", True)
                        
                        media_id = job.get('mediaId')
                        if not media_id:
                            continue
                        
                        # Get recaptcha token
                        print(f"[All {resolution}] Job {i+1}/{len(done)} - Getting recaptcha...")
                        recaptcha_token = self.app.browser_service.fetch_recaptcha_token_with_project(
                            acc['cookies'], 
                            project_id, 
                            account_id=acc['name'],
                            use_visible_browser=True, 
                            action='IMAGE_GENERATION'
                        )
                        
                        if not recaptcha_token:
                            print(f"[All {resolution}] Job {i+1} - No recaptcha token!")
                            continue
                        
                        # Call upscale API
                        print(f"[All {resolution}] Job {i+1}/{len(done)} - Upscaling...")
                        upscale_result = api.upscale_image(
                            media_id, 
                            project_id=project_id,
                            recaptcha_token=recaptcha_token,
                            resolution=resolution
                        )
                        
                        if not upscale_result or 'encodedImage' not in upscale_result:
                            print(f"[All {resolution}] Job {i+1} - No encoded image!")
                            continue
                        
                        # Save file
                        save_path = os.path.join(folder, f"img_{resolution.lower()}_{job['index']}.jpg")
                        success = api.save_upscaled_image(upscale_result['encodedImage'], save_path)
                        
                        if success:
                            success_count += 1
                            print(f"[All {resolution}] Job {i+1} - Saved: {save_path}")
                        
                    except Exception as e:
                        print(f"[All {resolution}] Job {i+1} error: {e}")
                        continue
                
                self.app.root.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    f"✅ Đã tải {success_count}/{len(done)} ảnh {resolution}!\n\nThư mục: {folder}"
                ))
                
            except Exception as e:
                print(f"[All {resolution} Error] {e}")
                self.app.root.after(0, lambda err=str(e): messagebox.showerror("Error", f"Lỗi: {err}"))
            finally:
                update_btn(original_text, False)
        
        threading.Thread(target=task, daemon=True).start()


    def _download_file(self, url, path):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                with open(path, 'wb') as f: f.write(r.content)
        except Exception as e:
            print(f"Download failed: {e}")

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
            
            # Reset queue and cards
            self.app.image_job_queue = []
            for idx in list(self.job_cards.keys()):
                if self.job_cards[idx]['frame'].winfo_exists():
                    self.job_cards[idx]['frame'].destroy()
            self.job_cards.clear()
            
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
        
        # Virtual DOM for Queue List
        # 1. Ensure enough rows in pool
        while len(self.queue_row_pool) < len(page_items):
            self.create_queue_row_structure()
            
        # 2. Update visible rows
        for i, job in enumerate(page_items):
            row_data = self.queue_row_pool[i]
            row_data['frame'].pack(fill="x", pady=4) # Ensure visible
            self.update_queue_row(row_data, job)
            
        # 3. Hide unused rows
        for i in range(len(page_items), len(self.queue_row_pool)):
             self.queue_row_pool[i]['frame'].pack_forget()

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

    def create_queue_row_structure(self):
        item = ctk.CTkFrame(self.queue_scroll, fg_color="#16213e", corner_radius=12, height=70)
        item.pack_propagate(False)
        
        inner = ctk.CTkFrame(item, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)
        
        # Thumbnail
        thumb_frame = ctk.CTkFrame(inner, width=50, height=50, fg_color="#2a2a4e", corner_radius=8)
        thumb_frame.pack(side="left")
        thumb_frame.pack_propagate(False)
        
        lbl_thumb = ctk.CTkLabel(thumb_frame, text="")
        lbl_thumb.pack(expand=True)
        
        # Info
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=10)
        
        lbl_title = ctk.CTkLabel(info, text="", font=("SF Pro Display", 12, "bold"), text_color="#ffffff", anchor="w")
        lbl_title.pack(fill="x")
        
        lbl_prompt = ctk.CTkLabel(info, text="", font=("SF Pro Display", 10), text_color="#6c7293", anchor="w")
        lbl_prompt.pack(fill="x")
        
        # Right (Status + Delete)
        right_frame = ctk.CTkFrame(inner, fg_color="transparent")
        right_frame.pack(side="right")
        
        lbl_status = ctk.CTkLabel(right_frame, text="", font=("SF Pro Display", 16, "bold"))
        lbl_status.pack(side="left")
        
        btn_delete = ctk.CTkButton(right_frame, text="✕", width=28, height=28, corner_radius=6, 
                                   fg_color="transparent", hover_color="#ef4444", text_color="#6c7293", 
                                   font=("SF Pro Display", 14, "bold"))
        btn_delete.pack(side="left", padx=(5,0))
        
        row_data = {
            'frame': item,
            'lbl_thumb': lbl_thumb,
            'lbl_title': lbl_title,
            'lbl_prompt': lbl_prompt,
            'lbl_status': lbl_status,
            'btn_delete': btn_delete,
            'last_job_id': None,
            'last_status': None
        }
        self.queue_row_pool.append(row_data)
        return row_data

    def update_queue_row(self, row, job):
        # Update Text
        job_type = "Img→Img" if job.get('image') else "Text→Img"
        row['lbl_title'].configure(text=f"#{job['index']+1} {job_type}")
        
        prompt_txt = job['prompt'][:30] + ("..." if len(job['prompt']) > 30 else "")
        row['lbl_prompt'].configure(text=prompt_txt)
        
        # Status
        st = job['status']
        status_config = {
            'pending': ('⏳', '#f59e0b'),
            'processing': ('⚙️', '#3b82f6'),
            'success': ('✅', '#22c55e'),
            'failed': ('⛔', '#ef4444')
        }
        icon, color = status_config.get(st, ('○', '#6c7293'))
        row['lbl_status'].configure(text=icon, text_color=color)
        
        # Delete Button
        if st in ('pending', 'failed'):
            row['btn_delete'].configure(state="normal", command=lambda i=job['index']: self.remove_job_by_index(i))
            row['btn_delete'].pack(side="left", padx=(5,0))
        else:
             row['btn_delete'].pack_forget()

        # Thumbnail (Caching)
        # Thumbnail (Caching)
        job_signature = f"{job['index']}_{id(job)}"
        
        # Always update if signature mismatch OR if it's the first time
        if row['last_job_id'] != job_signature:
             row['last_job_id'] = job_signature
             
             if job.get('image'):
                thumb_key = f"img_in_{job['index']}_{id(job)}"
                if thumb_key in self.app.thumbnail_cache:
                    row['lbl_thumb'].configure(image=self.app.thumbnail_cache[thumb_key], text="")
                else:
                    try:
                        img = Image.open(job['image'])
                        img.thumbnail((48, 48))
                        photo = ctk.CTkImage(light_image=img, dark_image=img, size=(48, 48))
                        self.app.thumbnail_cache[thumb_key] = photo
                        row['lbl_thumb'].configure(image=photo, text="")
                    except:
                        row['lbl_thumb'].configure(image=None, text="Img")
             else:
                # Force clear image
                row['lbl_thumb'].configure(image=None, text="Txt", text_color="#6366f1")
                # Hack: sometimes CTk doesn't clear image immediately if valid one was there
                # We can set an empty pixel image if needed, but let's try just ensure it's None.
                # Actually, duplicate configure to ensure update
                row['lbl_thumb'].configure(image="")

    def remove_job_by_index(self, idx):
        if self.app.is_image_running:
             # Check if processing
             if idx < len(self.app.image_job_queue) and self.app.image_job_queue[idx]['status'] == 'processing':
                 messagebox.showwarning("Warning", "Không thể xóa job đang chạy!")
                 return
        
        # Find explicit index match
        target = -1
        for i, j in enumerate(self.app.image_job_queue):
             if j['index'] == idx:
                 target = i
                 break
        if target != -1:
             self.app.image_job_queue.pop(target)
             # Re-index
             for k, j in enumerate(self.app.image_job_queue): j['index'] = k
             self.refresh_queue()
             self.refresh_progress()

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
            media_ids = []
            for m in res.get('media', []):
                # Try to get fifeUrl
                img_data = m.get('image', {}).get('generatedImage', {})
                u = img_data.get('fifeUrl')
                # Media ID can be in mediaGenerationId or just name
                mid = img_data.get('mediaGenerationId') or m.get('name')
                
                if u: urls.append(u)
                if mid: media_ids.append(mid)
            
            if not urls: raise Exception("No URL")
            
            job['status'] = 'success'
            job['video_url'] = urls[0]
            job['all_urls'] = urls
            job['mediaId'] = media_ids[0] if media_ids else None
            job['all_mediaIds'] = media_ids
            
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
        # Configure grid columns for the scrollable frame
        self.gallery_scroll.grid_columnconfigure(0, weight=1)
        self.gallery_scroll.grid_columnconfigure(1, weight=1)
        self.gallery_scroll.grid_columnconfigure(2, weight=1)
        
        active_jobs = [j for j in self.app.image_job_queue if j['status'] != 'pending']
        active_indices = {j['index'] for j in active_jobs}
        
        # 1. Remove cards that are no longer active
        to_remove = [idx for idx in self.job_cards if idx not in active_indices]
        for idx in to_remove:
            if self.job_cards[idx]['frame'].winfo_exists():
                self.job_cards[idx]['frame'].destroy()
            del self.job_cards[idx]
            
        # 2. Create or Update cards
        cols = 3
        for i, job in enumerate(active_jobs):
            idx = job['index']
            row = i // cols
            col = i % cols
            
            if idx not in self.job_cards:
                self.create_image_progress_card(job)
            
            # Update position (grid)
            card_data = self.job_cards[idx]
            if card_data['frame'].winfo_exists():
                card_data['frame'].grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
                self.update_image_progress_card(idx, job)

    def create_image_progress_card(self, job):
        card = ctk.CTkFrame(self.gallery_scroll, width=200, height=200, fg_color="#16213e", corner_radius=14)
        card.pack_propagate(False)
        
        # Header
        header = ctk.CTkFrame(card, fg_color="transparent", height=35)
        header.pack(fill="x", padx=12, pady=(10, 5))
        
        lbl_idx = ctk.CTkLabel(
            header, 
            text=f"#{job['index']+1}", 
            font=("SF Pro Display", 11, "bold"),
            text_color="#6c7293"
        )
        lbl_idx.pack(side="left")
        
        lbl_icon = ctk.CTkLabel(
            header, 
            text="", 
            font=("SF Pro Display", 14, "bold")
        )
        lbl_icon.pack(side="right")
        
        # Download button in header (initially hidden)
        btn_dl_header = ctk.CTkButton(
            header,
            text="⬇️",
            width=28,
            height=24,
            corner_radius=6,
            fg_color="#374151",
            hover_color="#4b5563",
            font=("SF Pro Display", 12)
        )
        
        # Download 2K button in header
        btn_dl_2k = ctk.CTkButton(
            header,
            text="⬇️ 2K",
            width=40,
            height=24,
            corner_radius=6,
            fg_color="#8b5cf6",
            hover_color="#7c3aed",
            font=("SF Pro Display", 10, "bold")
        )
        
        # Download 4K button in header
        btn_dl_4k = ctk.CTkButton(
            header,
            text="⬇️ 4K",
            width=40,
            height=24,
            corner_radius=6,
            fg_color="#ec4899",
            hover_color="#db2777",
            font=("SF Pro Display", 10, "bold")
        )

        
        # Content Container
        content = ctk.CTkFrame(card, fg_color="#2a2a4e", corner_radius=10)
        content.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.job_cards[job['index']] = {
            'frame': card,
            'refs': {
                'lbl_idx': lbl_idx,
                'lbl_icon': lbl_icon,
                'btn_dl_header': btn_dl_header,
                'btn_dl_2k': btn_dl_2k,
                'btn_dl_4k': btn_dl_4k,
                'content': content,
                'widgets': {} # Dynamic widgets inside content
            },
            'last_state_tuple': None,
            'last_status': None
        }

    def update_image_progress_card(self, idx, job):
        if idx not in self.job_cards: return
        card_data = self.job_cards[idx]
        refs = card_data['refs']
        
        st = job['status']
        thumb_obj = job.get('thumb_preview_ctk')
        
        # Optimization: Check if state changed to avoid expensive configures
        state_tuple = (st, id(thumb_obj) if thumb_obj else None, job['index'])
        if card_data.get('last_state_tuple') == state_tuple:
            return
        card_data['last_state_tuple'] = state_tuple
        
        # Update Header
        refs['lbl_idx'].configure(text=f"#{job['index']+1}")
        
        status_config = {
            'processing': ('⚙️', '#3b82f6'),
            'success': ('✅', '#22c55e'),
            'failed': ('⛔', '#ef4444')
        }
        icon, color = status_config.get(st, ('⏳', '#6c7293'))
        refs['lbl_icon'].configure(text=icon, text_color=color)
        
        current_phase = st
        last_phase = card_data['last_status']
        content_frame = refs['content']
        widgets = refs['widgets']
        
        # Handle Header Download Button
        if st == 'success':
            refs['btn_dl_header'].configure(command=lambda j=job: self.download_single_image(j))
            refs['btn_dl_header'].pack(side="right", padx=5)
            
            # Upscale 2K button
            refs['btn_dl_2k'].configure(command=lambda j=job: self.download_upscaled_image(j, "2K"))
            refs['btn_dl_2k'].pack(side="right", padx=(0, 3))
            
            # Upscale 4K button
            refs['btn_dl_4k'].configure(command=lambda j=job: self.download_upscaled_image(j, "4K"))
            refs['btn_dl_4k'].pack(side="right", padx=(0, 3))
        else:
            refs['btn_dl_header'].pack_forget()
            refs['btn_dl_2k'].pack_forget()
            refs['btn_dl_4k'].pack_forget()

        if current_phase != last_phase:
            # Clear previous content
            for w in content_frame.winfo_children(): w.destroy()
            widgets.clear()
            card_data['last_status'] = current_phase
            
            if st == 'failed':
                ctk.CTkLabel(
                    content_frame, 
                    text="Failed", 
                    font=("SF Pro Display", 12),
                    text_color="#ef4444"
                ).pack(expand=True, pady=(20, 5))
                
                ctk.CTkButton(
                    content_frame,
                    text="🔄 Retry",
                    font=("SF Pro Display", 11),
                    width=70,
                    height=28,
                    corner_radius=6,
                    fg_color="#374151",
                    hover_color="#4b5563",
                    command=lambda j=job: self.retry_job(j)
                ).pack(pady=(0, 20))
                
            elif st == 'success':
                if job.get('video_url'):
                    thumb_lbl = ctk.CTkLabel(content_frame, text="", image=None, cursor="hand2")
                    thumb_lbl.pack(expand=True, pady=5)
                    thumb_lbl.bind("<Button-1>", lambda e, j=job: self.show_lightbox(j['video_url']))
                    widgets['thumb_lbl'] = thumb_lbl
                    # Note: Download button moved to header
            
            else: # Processing or others
                ctk.CTkLabel(
                    content_frame, 
                    text="⚙️", 
                    font=("Segoe UI Emoji", 28)
                ).pack(expand=True)
                ctk.CTkLabel(
                    content_frame, 
                    text="Generating...", 
                    font=("SF Pro Display", 11),
                    text_color="#6c7293"
                ).pack(pady=(0, 15))

        # Update Values
        if st == 'success':
             # Handle Thumbnail
            if 'thumb_preview_ctk' in job:
                if 'thumb_lbl' in widgets:
                    try:
                        widgets['thumb_lbl'].configure(text="", image=job['thumb_preview_ctk'])
                    except: pass
            else:
                if 'thumb_lbl' in widgets:
                    widgets['thumb_lbl'].configure(text="⏳ Loading...")
                
                # Initiate load if not already loading
                if not job.get('_thumb_loading'):
                    job['_thumb_loading'] = True
                    threading.Thread(target=self.load_thumbnail_thread, args=(job,), daemon=True).start()

    def load_thumbnail_thread(self, job):
        try:
            r = requests.get(job['video_url'], timeout=10)
            img = Image.open(BytesIO(r.content))
            img.thumbnail((180, 130))
            p = ctk.CTkImage(light_image=img, dark_image=img, size=(180, 130))
            job['thumb_preview_ctk'] = p
            
            # Update UI safely
            def update_thumb_ui():
                idx = job['index']
                if idx in self.job_cards:
                    widgets = self.job_cards[idx]['refs'].get('widgets', {})
                    if 'thumb_lbl' in widgets:
                        widgets['thumb_lbl'].configure(text="", image=p)
                        
            self.app.root.after(0, update_thumb_ui)
        except Exception as e:
            pass
        finally:
            job['_thumb_loading'] = False

    def retry_job(self, job):
        # Find a live account to retry with
        live_accounts = [a for a in self.app.account_manager.accounts if "Live" in a.get('status', '')]
        if not live_accounts:
            messagebox.showerror("Error", "Không có tài khoản Live!")
            return
        
        acc = live_accounts[0]
        job['status'] = 'processing'
        job['error'] = None
        job['account'] = acc['name']
        self.refresh_queue()
        self.refresh_progress() # Card moves to processing state
        
        # Run immediately in background
        threading.Thread(target=self.process_job, args=(job, acc), daemon=True).start()

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

    def download_single_image(self, job):
        save_path = filedialog.asksaveasfilename(
            defaultextension=".png", 
            filetypes=[("PNG", "*.png"), ("JPG", "*.jpg")],
            initialfile=f"image_{job['index']}.png"
        )
        if not save_path: return
        
        # Determine URL (preferred all_urls[0] if available, else video_url)
        url = job.get('all_urls', [job.get('video_url')])[0]
        if not url: return

        def dl_thread():
            try:
                self._download_file(url, save_path)
                messagebox.showinfo("Success", f"✅ Đã tải ảnh:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Lỗi tải ảnh: {e}")
        
        threading.Thread(target=dl_thread, daemon=True).start()

    def download_upscaled_image(self, job, resolution="2K"):
        save_path = filedialog.asksaveasfilename(
            defaultextension=".jpg", 
            filetypes=[("JPG", "*.jpg"), ("PNG", "*.png")],
            initialfile=f"image_{resolution.lower()}_{job['index']}.jpg",
            title=f"Lưu ảnh Upscale {resolution}"
        )
        if not save_path: return

        # Need mediaId from job. If not present (failed parsing?), can't upscale.
        media_id = job.get('mediaId')
        if not media_id:
            messagebox.showerror("Error", "Không tìm thấy Media ID của ảnh này!")
            return

        # Get the button reference to show loading state
        job_idx = job['index']
        btn_key = 'btn_dl_2k' if resolution == "2K" else 'btn_dl_4k'
        original_color = "#8b5cf6" if resolution == "2K" else "#ec4899"
        btn = None
        if job_idx in self.job_cards:
            btn = self.job_cards[job_idx]['refs'].get(btn_key)
        
        def set_loading(loading):
            """Update button state"""
            if btn:
                self.app.root.after(0, lambda: btn.configure(
                    text="⏳..." if loading else f"⬇️ {resolution}",
                    state="disabled" if loading else "normal",
                    fg_color="#4b5563" if loading else original_color
                ))

        def task():
            try:
                set_loading(True)
                
                # Find an account to perform upscale
                acc_name = job.get('account')
                acc = self.app.account_manager.get_account(acc_name)
                
                if not acc:
                    # Fallback to any live account
                    live = [a for a in self.app.account_manager.accounts if "Live" in a.get('status', '')]
                    if live:
                        acc = live[0]
                    else:
                        raise Exception("Cần ít nhất 1 tài khoản Live để upscale!")
                
                project_id = acc.get('project_id')
                
                api = LabsApiService()
                api.set_credentials(acc['cookies'], acc.get('access_token'))
                
                # Step 1: Get recaptcha token via browser service
                print(f"[Upscale {resolution}] Fetching recaptcha token...")
                recaptcha_token = self.app.browser_service.fetch_recaptcha_token_with_project(
                    acc['cookies'], 
                    project_id, 
                    account_id=acc['name'],
                    use_visible_browser=True, 
                    action='IMAGE_GENERATION'
                )
                
                if not recaptcha_token:
                    raise Exception("Không lấy được Recaptcha Token!")
                
                print(f"[Upscale {resolution}] Got recaptcha token: {str(recaptcha_token)[:50]}...")
                
                # Step 2: Call upscale API with resolution
                upscale_result = api.upscale_image(
                    media_id, 
                    project_id=project_id,
                    recaptcha_token=recaptcha_token,
                    resolution=resolution
                )
                
                if not upscale_result or 'encodedImage' not in upscale_result:
                    raise Exception("API không trả về ảnh Upscale!")
                
                # Step 3: Save base64 image
                success = api.save_upscaled_image(upscale_result['encodedImage'], save_path)
                
                if success:
                    self.app.root.after(0, lambda: messagebox.showinfo("Success", f"✅ Đã tải ảnh {resolution}:\n{save_path}"))
                else:
                    raise Exception("Lỗi lưu file!")
                
            except Exception as e:
                print(f"[Upscale Error] {e}")
                import traceback
                traceback.print_exc()
                self.app.root.after(0, lambda err=str(e): messagebox.showerror("Error", f"Lỗi Upscale: {err}"))
            finally:
                set_loading(False)
        
        threading.Thread(target=task, daemon=True).start()

    def test_upscale_2k(self):
        """Hardcoded test for 2K upscale debug"""
        media_id = "CAMSJGYyZjQ0YzQ0LWVkN2YtNGMwOC1iMjU1LTg2ZWU2NjNjZWFjMRokN2VlODBiNDItOWRiNi00MjI3LWEzNmEtYjY1OGZkNWZiMjE0IgNDQUUqJDZjMTE4MmEzLWRjZTUtNDNjMy1hZmQyLTc0MmFmNDA1NzlhZA"
        project_id = "f2f44c44-ed7f-4c08-b255-86ee663ceac1"
        
        save_path = filedialog.asksaveasfilename(
             defaultextension=".jpg", 
             filetypes=[("JPG", "*.jpg"), ("PNG", "*.png")],
             initialfile="test_2k_hardcoded.jpg",
             title="Lưu ảnh Test 2K"
        )
        if not save_path: return

        def task():
            try:
                # Find any live account
                live = [a for a in self.app.account_manager.accounts if "Live" in a.get('status', '')]
                if not live:
                     raise Exception("Cần ít nhất 1 tài khoản Live!")
                
                acc = live[0]
                api = LabsApiService()
                api.set_credentials(acc['cookies'], acc.get('access_token'))
                
                self.app.root.after(0, lambda: messagebox.showinfo("Info", f"Testing Upscale...\nAcc: {acc['name']}"))
                
                # Get recaptcha token
                recaptcha_token = self.app.browser_service.fetch_recaptcha_token_with_project(
                    acc['cookies'], 
                    project_id, 
                    account_id=acc['name'],
                    use_visible_browser=True, 
                    action='IMAGE_GENERATION'
                )
                
                if not recaptcha_token:
                    raise Exception("Không lấy được Recaptcha Token!")
                
                # Call upscale with recaptcha token
                upscale_result = api.upscale_image(
                    media_id, 
                    project_id=project_id,
                    recaptcha_token=recaptcha_token
                )
                
                if not upscale_result or 'encodedImage' not in upscale_result:
                     raise Exception("Không lấy được ảnh upscale")
                
                # Save base64 image     
                success = api.save_upscaled_image(upscale_result['encodedImage'], save_path)
                
                if success:
                    self.app.root.after(0, lambda: messagebox.showinfo("Success", f"✅ DONE 2K:\n{save_path}"))
                else:
                    raise Exception("Lỗi lưu file!")
                
            except Exception as e:
                print(f"Test Error: {e}")
                self.app.root.after(0, lambda err=str(e): messagebox.showerror("Error", f"Test Upscale Failed: {err}"))
                
        threading.Thread(target=task, daemon=True).start()

    def clear_queue(self):
        running = [j for j in self.app.image_job_queue if j['status'] in ('processing', 'polling')]
        
        # Reset queue and cards
        if running:
            # If jobs are running, only clear others
            self.app.image_job_queue = running
        else:
            self.app.image_job_queue = []
            
        for idx in list(self.job_cards.keys()):
             if self.job_cards[idx]['frame'].winfo_exists():
                 self.job_cards[idx]['frame'].destroy()
        self.job_cards.clear()
            
        self.refresh_queue()
        self.refresh_progress()
            
        for i, j in enumerate(self.app.image_job_queue): j['index'] = i

    def add_mock_data(self):
        mocks = [
            {
                "prompt": "Mock Image 1",
                "image": None,
                "video_url": "https://picsum.photos/400/300",
                "status": "success"
            },
            {
                "prompt": "Mock Image 2",
                "image": None,
                "video_url": "https://picsum.photos/400/300?2",
                "status": "success"
            },
            {
                "prompt": "Mock Image 3",
                "image": None,
                "video_url": "https://picsum.photos/400/300?3",
                "status": "success"
            }
        ]
        
        for m in mocks:
            idx = len(self.app.image_job_queue)
            m['index'] = idx
            self.app.image_job_queue.append(m)
            
        self.refresh_queue()
        self.refresh_progress()
