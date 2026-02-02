
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
        self.job_cards = {}  # Cache for progress cards {job_index: {frame, refs, last_status}}
        self.queue_row_pool = [] # Pool of widgets for queue list items
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
            fg_color="#374151",
            hover_color="#4b5563",
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
            text="💡 Cột 'image' (start), 'image_2' (end - tùy chọn), 'prompt' bắt buộc", 
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
            command=self.download_all_videos
        ).pack(side="right", padx=(5, 0))
        
        self.btn_download_all_1080p = ctk.CTkButton(
            gallery_header,
            text="📥 All 1080p",
            font=("SF Pro Display", 10, "bold"),
            width=80,
            height=32,
            corner_radius=8,
            fg_color="#f97316",
            hover_color="#ea580c",
            command=lambda: self.download_all_upscaled("1080p")
        )
        self.btn_download_all_1080p.pack(side="right", padx=(5, 0))
        
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
            data = {"image": ["start1.jpg", "start2.png"], "image_2": ["end1.jpg", ""], "prompt": ["animate from start to end", "cat playing"]}
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
            
            # Clear job cards cache to remove internal references
            for idx in list(self.job_cards.keys()):
                if self.job_cards[idx]['frame'].winfo_exists():
                    self.job_cards[idx]['frame'].destroy()
            self.job_cards.clear()
            
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
            has_image_2_col = 'image_2' in df.columns
            
            # Reset queue and cards
            self.app.job_queue = []
            for idx in list(self.job_cards.keys()):
                if self.job_cards[idx]['frame'].winfo_exists():
                    self.job_cards[idx]['frame'].destroy()
            self.job_cards.clear()
            
            base_dir = os.path.dirname(filepath)
            
            for idx, row in df.iterrows():
                image_path = None
                image_name = None
                image_2_path = None
                
                # Parse image (start image)
                if has_image_col:
                    val = str(row['image']).strip()
                    if val and val.lower() not in ('nan', 'none', ''):
                        image_path = val if os.path.isabs(val) else os.path.join(base_dir, val)
                        if not os.path.exists(image_path): image_path = None
                        else: image_name = os.path.splitext(os.path.basename(image_path))[0]
                
                # Parse image_2 (end image)
                if has_image_2_col:
                    val2 = str(row['image_2']).strip()
                    if val2 and val2.lower() not in ('nan', 'none', ''):
                        image_2_path = val2 if os.path.isabs(val2) else os.path.join(base_dir, val2)
                        if not os.path.exists(image_2_path): image_2_path = None
                
                prompt = str(row['prompt']).strip()
                self.app.job_queue.append({
                    'index': len(self.app.job_queue),
                    'image': image_path,
                    'image_2': image_2_path,
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
        # NOTE: self.app.thumbnail_cache is used for queue list.
        
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
        
        # --- VIRTUAL DOM UPDATE ---
        # 1. Update needed rows
        for i, job in enumerate(page_items):
            if i >= len(self.queue_row_pool):
                self.create_queue_row_structure()
            
            row_widgets = self.queue_row_pool[i]
            self.update_queue_row(row_widgets, job)
            # Ensure visible
            if not row_widgets['frame'].winfo_ismapped():
                row_widgets['frame'].pack(fill="x", pady=4)

        # 2. Hide only unused rows
        for i in range(len(page_items), len(self.queue_row_pool)):
            self.queue_row_pool[i]['frame'].pack_forget()

    def create_queue_row_structure(self):
        item = ctk.CTkFrame(self.queue_scroll, fg_color="#16213e", corner_radius=12, height=70)
        item.pack_propagate(False)
        
        inner = ctk.CTkFrame(item, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=12, pady=10)
        
        # Status/Action (Pack RIGHT first to reserve space)
        right_box = ctk.CTkFrame(inner, fg_color="transparent")
        right_box.pack(side="right", padx=(0, 5))
        
        # Helper container for delete button to enforce size
        del_container = ctk.CTkFrame(right_box, width=30, height=30, fg_color="transparent")
        del_container.pack(side="right", padx=5)
        del_container.pack_propagate(False)

        del_btn = ctk.CTkButton(
            del_container, 
            text="✕", 
            width=30, 
            height=30,
            fg_color="transparent", 
            hover_color="#ef4444",
            text_color="#6c7293",
            font=("SF Pro Display", 14, "bold"),
            command=lambda: None
        )
        del_btn.pack(fill="both", expand=True)
        
        status_lbl = ctk.CTkLabel(right_box, text="", font=("SF Pro Display", 11, "bold"), text_color="#9ca3af")
        status_lbl.pack(side="right", padx=5)

        # Thumbnail Container (Left) - holds both start and end images
        thumb_container = ctk.CTkFrame(inner, fg_color="transparent")
        thumb_container.pack(side="left")
        
        # Start Image Thumbnail
        thumb_frame = ctk.CTkFrame(thumb_container, width=44, height=44, fg_color="#2a2a4e", corner_radius=6)
        thumb_frame.pack(side="left")
        thumb_frame.pack_propagate(False)
        
        thumb_lbl = ctk.CTkLabel(thumb_frame, text="", font=("SF Pro Display", 9, "bold"), text_color="#6c7293")
        thumb_lbl.pack(expand=True)
        
        # Arrow between thumbnails
        arrow_lbl = ctk.CTkLabel(thumb_container, text="→", font=("SF Pro Display", 12, "bold"), text_color="#6366f1")
        arrow_lbl.pack(side="left", padx=2)
        
        # End Image Thumbnail
        thumb_frame_2 = ctk.CTkFrame(thumb_container, width=44, height=44, fg_color="#2a2a4e", corner_radius=6)
        thumb_frame_2.pack(side="left")
        thumb_frame_2.pack_propagate(False)
        
        thumb_lbl_2 = ctk.CTkLabel(thumb_frame_2, text="", font=("SF Pro Display", 9, "bold"), text_color="#6c7293")
        thumb_lbl_2.pack(expand=True)
        
        # Info (Left, takes remaining space)
        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=10)
        
        title_lbl = ctk.CTkLabel(info, text="", font=("SF Pro Display", 12, "bold"), text_color="#ffffff", anchor="w")
        title_lbl.pack(fill="x")
        
        desc_lbl = ctk.CTkLabel(info, text="", font=("SF Pro Display", 11), text_color="#9ca3af", anchor="w")
        desc_lbl.pack(fill="x")
        
        self.queue_row_pool.append({
            'frame': item,
            'thumb_lbl': thumb_lbl,
            'thumb_lbl_2': thumb_lbl_2,
            'thumb_frame_2': thumb_frame_2,
            'arrow_lbl': arrow_lbl,
            'title_lbl': title_lbl,
            'desc_lbl': desc_lbl,
            'status_lbl': status_lbl,
            'del_btn': del_btn,
            'last_job_id': None
        })

    def update_queue_row(self, widgets, job):
        idx = job.get('index', 0)
        
        # Unique signature for this row's content
        job_signature = f"{idx}_{id(job)}"
        
        # Only update if job changed for this row slot
        if widgets.get('last_job_id') == job_signature:
             # Still update dynamic status
             pass
        else:
             widgets['last_job_id'] = job_signature
             
             job_type = "Img→Img→Vid" if (job.get('image') and job.get('image_2')) else ("Img→Vid" if job.get('image') else "Text→Vid")
             widgets['title_lbl'].configure(text=f"#{idx+1} {job_type}")
             
             prompt = job.get('prompt', '')
             short_prompt = (prompt[:40] + '...') if len(prompt) > 40 else prompt
             widgets['desc_lbl'].configure(text=short_prompt)
             
             # Delete Button
             widgets['del_btn'].configure(command=lambda: self.remove_job_by_index(idx))

             # Start Image Thumbnail
             img_path = job.get('image')
             thumb_key = f"vid_thumb_{id(job)}"
             
             if thumb_key in self.app.thumbnail_cache:
                  widgets['thumb_lbl'].configure(image=self.app.thumbnail_cache[thumb_key], text="")
             else:
                  if img_path and os.path.exists(img_path):
                      try:
                          img = Image.open(img_path)
                          img.thumbnail((42, 42))
                          photo = ctk.CTkImage(light_image=img, dark_image=img, size=(42, 42))
                          self.app.thumbnail_cache[thumb_key] = photo
                          widgets['thumb_lbl'].configure(image=photo, text="")
                      except:
                          widgets['thumb_lbl'].configure(image=None, text="ERR")
                  else:
                      widgets['thumb_lbl'].configure(image=None, text="TXT" if not img_path else "N/A")
             
             # End Image Thumbnail (image_2)
             img_path_2 = job.get('image_2')
             thumb_key_2 = f"vid_thumb2_{id(job)}"
             
             # Show/hide end image components based on whether there's an end image
             if img_path_2:
                  widgets['arrow_lbl'].pack(side="left", padx=2)
                  widgets['thumb_frame_2'].pack(side="left")
                  
                  if thumb_key_2 in self.app.thumbnail_cache:
                       widgets['thumb_lbl_2'].configure(image=self.app.thumbnail_cache[thumb_key_2], text="")
                  else:
                       if os.path.exists(img_path_2):
                           try:
                               img2 = Image.open(img_path_2)
                               img2.thumbnail((42, 42))
                               photo2 = ctk.CTkImage(light_image=img2, dark_image=img2, size=(42, 42))
                               self.app.thumbnail_cache[thumb_key_2] = photo2
                               widgets['thumb_lbl_2'].configure(image=photo2, text="")
                           except:
                               widgets['thumb_lbl_2'].configure(image=None, text="ERR")
                       else:
                           widgets['thumb_lbl_2'].configure(image=None, text="N/A")
             else:
                  # Hide end image components if no image_2
                  widgets['arrow_lbl'].pack_forget()
                  widgets['thumb_frame_2'].pack_forget()

        # Status (always update)
        st = job.get('status', 'pending')
        status_config = {
            'pending': ('⏳', '#f59e0b'),
            'processing': ('⚙️', '#3b82f6'),
            'polling': ('👁️', '#8b5cf6'),
            'success': ('✅', '#22c55e'),
            'failed': ('⛔', '#ef4444')
        }
        icon, color = status_config.get(st, ('○', '#9ca3af'))
        widgets['status_lbl'].configure(text=icon, text_color=color, font=("Segoe UI Emoji", 16))

    def remove_job_by_index(self, idx):
        # Find local index
        local_idx = -1
        for i, job in enumerate(self.app.job_queue):
            if job['index'] == idx:
                local_idx = i
                break
        
        if local_idx != -1:
            self.app.job_queue.pop(local_idx)
            self.refresh_queue_preview()  # Re-render efficient layout

    def test_upscale_2k(self):
        """Hardcoded test for 2K upscale debug (Copy from Image Screen)"""
        media_id = "CAMSJGYyZjQ0YzQ0LWVkN2YtNGMwOC1iMjU1LTg2ZWU2NjNjZWFjMRokN2VlODBiNDItOWRiNi00MjI3LWEzNmEtYjY1OGZkNWZiMjE0IgNDQUUqJDZjMTE4MmEzLWRjZTUtNDNjMy1hZmQyLTc0MmFmNDA1NzlhZA"
        project_id = "f2f44c44-ed7f-4c08-b255-86ee663ceac1"
        
        save_path = filedialog.asksaveasfilename(
             defaultextension=".png", 
             filetypes=[("PNG", "*.png")],
             initialfile="test_2k_hardcoded.png",
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
                api.set_credentials(acc['cookies']) # Use cookies (plural)
                
                self.app.root.after(0, lambda: messagebox.showinfo("Info", f"Testing Upscale...\nAcc: {acc['name']}"))
                
                # Call upscale 
                upscale_url = api.upscale_image(media_id, project_id=project_id)
                if not upscale_url:
                     raise Exception("Không lấy được URL upscale")
                     
                api.download_video(upscale_url, save_path)
                self.app.root.after(0, lambda: messagebox.showinfo("Success", f"✅ DONE 2K:\n{save_path}"))
                
            except Exception as e:
                print(f"Test Error: {e}")
                self.app.root.after(0, lambda err=str(e): messagebox.showerror("Error", f"Test Upscale Failed: {err}"))
                
        threading.Thread(target=task, daemon=True).start()

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
        
        job_type = "Img→Img→Vid" if (job.get('image') and job.get('image_2')) else ("Img→Vid" if job.get('image') else "Text→Vid")
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
        
        # Start UI Updater
        self._start_ui_updater()
        
        threading.Thread(target=self.batch_worker, daemon=True).start()

    def _start_ui_updater(self):
        if not self.app.is_running: return
        self.refresh_queue_preview()
        self.refresh_progress_panel()
        self.app.root.after(1000, self._start_ui_updater)

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
                        # UI refresh handled by periodic updater
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
            media_id_2 = None
            
            # Upload start image
            if job.get('image'):
                res = api.upload_image(job['image'])
                media_id = res.get('mediaId')
                if not media_id: raise Exception("Upload start image failed")
            
            # Upload end image (image_2)
            if job.get('image_2'):
                res2 = api.upload_image(job['image_2'])
                media_id_2 = res2.get('mediaId')
                if not media_id_2: raise Exception("Upload end image failed")
            
            # Retry logic for reCAPTCHA errors - max 3 attempts
            max_retries = 3
            gen = None
            last_error = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    token = self.app.browser_service.fetch_recaptcha_token(account['cookies'], account_id=account['name'], use_visible_browser=True)
                    if not self.app.is_running: return
                    if not token: raise Exception("Failed Recaptcha")
                    
                    project_id = account.get('project_id')
                    ratio_txt = self.combo_ratio.get()
                    ratio = "VIDEO_ASPECT_RATIO_PORTRAIT" if "Portrait" in ratio_txt else "VIDEO_ASPECT_RATIO_LANDSCAPE"
                    try: count = int(self.spin_count.get())
                    except: count = 1
                    
                    # Choose API based on image availability
                    if media_id and media_id_2:
                        # Start + End Image => batchAsyncGenerateVideoStartAndEndImage
                        gen = api.generate_video_start_end_image(job['prompt'], media_id, media_id_2, ratio, count, project_id, token)
                    elif media_id:
                        # Only Start Image => batchAsyncGenerateVideoStartImage
                        gen = api.generate_video(job['prompt'], media_id, ratio, count, project_id, token)
                    else:
                        # No Image => Text-to-Video
                        gen = api.generate_video_text(job['prompt'], ratio, count, project_id, token)
                    
                    # Check if response contains error (403 reCAPTCHA)
                    if gen and gen.get('error'):
                        error_code = gen.get('error', {}).get('code')
                        error_msg = gen.get('error', {}).get('message', '')
                        if error_code == 403 and 'reCAPTCHA' in error_msg:
                            print(f"[Job #{job['index']+1}] reCAPTCHA failed (attempt {attempt}/{max_retries}), retrying...")
                            last_error = f"reCAPTCHA failed: {error_msg}"
                            if attempt < max_retries:
                                time.sleep(2)  # Wait before retry
                                continue
                            else:
                                raise Exception(f"reCAPTCHA failed after {max_retries} attempts")
                    
                    # Success - break out of retry loop
                    break
                    
                except Exception as e:
                    last_error = str(e)
                    if 'reCAPTCHA' in str(e) or '403' in str(e) or 'Recaptcha' in str(e):
                        print(f"[Job #{job['index']+1}] Error (attempt {attempt}/{max_retries}): {e}")
                        if attempt < max_retries:
                            time.sleep(2)
                            continue
                        else:
                            raise Exception(f"reCAPTCHA failed after {max_retries} attempts: {e}")
                    raise
            
            ops = gen.get('operations', []) if gen else []
            if not ops: raise Exception(last_error or "No operations")
            
            job['operation'] = ops[0]
            job['status'] = 'polling'
            job['progress'] = 10
            
            # UI refresh handled by periodic updater
            
            def simulate():
                for i in range(10, 95):
                    if job['status'] != 'polling' or not self.app.is_running: break
                    job['progress'] = i
                    # UI refresh handled by periodic updater
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
                        
                        # Extract mediaId for 1080p upscale
                        # mediaGenerationId is at top level of op (not inside operation.metadata)
                        try:
                            job['mediaId'] = op.get('mediaGenerationId', '')
                            print(f"[Video] MediaId: {job['mediaId'][:60]}..." if job['mediaId'] else "[Video] MediaId: NOT FOUND")
                        except Exception as e:
                            print(f"[Video] MediaId extraction error: {e}")
                        
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
            pass # UI refresh handled by periodic updater

    def refresh_progress_panel(self):
        # Configure grid columns for the scrollable frame
        self.gallery_scroll.grid_columnconfigure(0, weight=1)
        self.gallery_scroll.grid_columnconfigure(1, weight=1)
        self.gallery_scroll.grid_columnconfigure(2, weight=1)
        
        active_jobs = [j for j in self.app.job_queue if j['status'] in ('processing', 'polling', 'success', 'failed')]
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
                self.create_progress_card(job)
            
            # Update position (grid)
            card_data = self.job_cards[idx]
            if card_data['frame'].winfo_exists():
                card_data['frame'].grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
                self.update_progress_card(idx, job)

    def create_progress_card(self, job):
        card = ctk.CTkFrame(self.gallery_scroll, width=200, height=180, fg_color="#16213e", corner_radius=14)
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
        
        # 1080p upscale button
        btn_1080p = ctk.CTkButton(
            header,
            text="⬇️ 1080p",
            width=60,
            height=24,
            corner_radius=6,
            fg_color="#f97316",
            hover_color="#ea580c",
            font=("SF Pro Display", 10, "bold")
        )
        # Don't pack yet, will be shown only on success
        
        # 4K upscale button
        btn_4k = ctk.CTkButton(
            header,
            text="⬇️ 4K",
            width=50,
            height=24,
            corner_radius=6,
            fg_color="#ec4899",
            hover_color="#db2777",
            font=("SF Pro Display", 10, "bold")
        )
        # Don't pack yet, will be shown only on success
        
        # Content Container
        content = ctk.CTkFrame(card, fg_color="#2a2a4e", corner_radius=10)
        content.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        
        self.job_cards[job['index']] = {
            'frame': card,
            'refs': {
                'lbl_idx': lbl_idx,
                'lbl_icon': lbl_icon,
                'btn_1080p': btn_1080p,
                'btn_4k': btn_4k,
                'content': content,
                'widgets': {} # Dynamic widgets inside content
            },
            'last_status': None
        }

    def update_progress_card(self, idx, job):
        if idx not in self.job_cards: return
        card_data = self.job_cards[idx]
        refs = card_data['refs']
        
        st = job['status']
        prog = job.get('progress', 0)
        thumb_obj = job.get('thumb_video_ctk')
        
        # Optimization: Check if state changed to avoid expensive configures
        state_tuple = (st, int(prog), id(thumb_obj) if thumb_obj else None, job['index'])
        if card_data.get('last_state_tuple') == state_tuple:
            return
        card_data['last_state_tuple'] = state_tuple
        
        # Update Header
        refs['lbl_idx'].configure(text=f"#{job['index']+1}")
        
        status_config = {
            'processing': ('⚙️', '#3b82f6'),
            'polling': ('👁️', '#8b5cf6'),
            'success': ('✅', '#22c55e'),
            'failed': ('⛔', '#ef4444')
        }
        icon, color = status_config.get(st, ('⏳', '#6c7293'))
        refs['lbl_icon'].configure(text=icon, text_color=color)
        
        # Handle 1080p and 4K button visibility
        if st == 'success' and (job.get('mediaId') or job.get('video_url')):
            refs['btn_1080p'].configure(command=lambda j=job: self.download_video_upscale(j, "1080p"))
            refs['btn_1080p'].pack(side="right", padx=(0, 3))
            refs['btn_4k'].configure(command=lambda j=job: self.download_video_upscale(j, "4K"))
            refs['btn_4k'].pack(side="right", padx=(0, 3))
        else:
            refs['btn_1080p'].pack_forget()
            refs['btn_4k'].pack_forget()
        
        # Check if we need to rebuild content (status changed)
        # We group processing/polling together as they share the same UI structure (progress bar)
        current_phase = 'progress' if st in ('processing', 'polling') else st
        last_phase = card_data['last_status']
        
        content_frame = refs['content']
        widgets = refs['widgets']

        
        if current_phase != last_phase:
            # Clear previous content
            for w in content_frame.winfo_children(): w.destroy()
            widgets.clear()
            card_data['last_status'] = current_phase
            
            # Rebuild based on new phase
            # Rebuild based on new phase
            if current_phase == 'progress':
                lbl_pct = ctk.CTkLabel(
                    content_frame, 
                    text="0%", 
                    font=("SF Pro Display", 32, "bold"),
                    text_color="#6366f1"
                )
                lbl_pct.pack(expand=True)
                
                # Removed Prog Bar as requested
                # prog_bar = ctk.CTkProgressBar(...)
                
                widgets['lbl_pct'] = lbl_pct
                # widgets['prog_bar'] = prog_bar
                
            elif st == 'success':
                if job.get('video_url'):
                    thumb_frame = ctk.CTkFrame(content_frame, fg_color="transparent", width=160, height=90)
                    thumb_frame.pack(expand=True, pady=5)
                    thumb_frame.pack_propagate(False)
                    
                    thumb_lbl = ctk.CTkLabel(thumb_frame, text="", image=None)
                    thumb_lbl.place(relx=0.5, rely=0.5, anchor="center")
                    
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
                    
                    # Bindings
                    play_lbl.bind("<Button-1>", lambda e, j=job: self.play_video(j))
                    thumb_lbl.bind("<Button-1>", lambda e, j=job: self.play_video(j))
                    
                    widgets['thumb_lbl'] = thumb_lbl
                    
                    # Trigger thumbnail load if needed
                    # We do this check below
                
            elif st == 'failed':
                ctk.CTkLabel(
                    content_frame, 
                    text="Failed", 
                    font=("SF Pro Display", 12),
                    text_color="#ef4444"
                ).pack(expand=True, pady=(15, 5))
                
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
                ).pack(pady=(0, 15))

        # Update Values
        if current_phase == 'progress':
            prog = job.get('progress', 0)
            if 'lbl_pct' in widgets:
                widgets['lbl_pct'].configure(text=f"{int(prog)}%")
            # if 'prog_bar' in widgets: widgets['prog_bar'].set(prog/100)
                
        elif st == 'success':
            # Handle Thumbnail
            if 'thumb_video_ctk' in job:
                if 'thumb_lbl' in widgets:
                    try:
                        widgets['thumb_lbl'].configure(text="", image=job['thumb_video_ctk'])
                    except: pass
            else:
                if 'thumb_lbl' in widgets:
                    widgets['thumb_lbl'].configure(text="Loading...")
                
                # Initiate load if not already loading
                if not job.get('_thumb_loading'):
                    job['_thumb_loading'] = True
                    threading.Thread(target=self.load_thumbnail_thread, args=(job,), daemon=True).start()

    def load_thumbnail_thread(self, job):
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
                
                # Update UI safely
                def update_thumb_ui():
                    idx = job['index']
                    if idx in self.job_cards:
                        widgets = self.job_cards[idx]['refs'].get('widgets', {})
                        if 'thumb_lbl' in widgets:
                            widgets['thumb_lbl'].configure(text="", image=ctk_img)
                            
                self.app.root.after(0, update_thumb_ui)
        except Exception as e:
            print(f"Thumb error: {e}")
        finally:
            job['_thumb_loading'] = False

    def retry_job(self, job):
        """Reset job and retry - either queue it or run immediately"""
        # Find a live account to retry with
        live_accounts = [a for a in self.app.account_manager.accounts if "Live" in a.get('status', '')]
        if not live_accounts:
            messagebox.showerror("Error", "Không có tài khoản Live!")
            return
        
        # 1. Remove the failed card from UI
        job_idx = job['index']
        if job_idx in self.job_cards:
            if self.job_cards[job_idx]['frame'].winfo_exists():
                self.job_cards[job_idx]['frame'].destroy()
            del self.job_cards[job_idx]
        
        # 2. Reset job state completely
        job['error'] = None
        job['progress'] = 0
        job['operation'] = None
        job['video_url'] = None
        job['mediaId'] = None
        job.pop('thumb_video_ctk', None)
        job.pop('_thumb_loading', None)
        
        # 3. Process based on batch state
        if self.app.is_running:
            # Batch is running - set to pending, batch_worker will pick it up
            job['status'] = 'pending'
            job['account'] = None
            self.refresh_queue_preview()
        else:
            # Batch stopped - run this job immediately
            acc = live_accounts[0]
            job['status'] = 'processing'
            job['account'] = acc['name']
            
            # Enable is_running for this job
            self.app.is_running = True
            self.lbl_status.configure(text="🔄 Đang retry...")
            self.btn_start.configure(state="disabled", fg_color="#4a4a6a")
            
            # Start UI updater
            self._start_ui_updater()
            
            # Run job in background, then cleanup
            def run_and_cleanup():
                try:
                    self.process_job(job, acc)
                finally:
                    # Check if there are more pending jobs after this one
                    pending = [j for j in self.app.job_queue if j['status'] == 'pending']
                    processing = [j for j in self.app.job_queue if j['status'] in ('processing', 'polling')]
                    
                    if not pending and not processing:
                        self.app.is_running = False
                        self.app.root.after(0, lambda: [
                            self.lbl_status.configure(text="✅ Hoàn tất!"),
                            self.btn_start.configure(state="normal", fg_color="#22c55e")
                        ])
            
            threading.Thread(target=run_and_cleanup, daemon=True).start()

    def play_video(self, job):
        if not job.get('video_url'):
            return
        
        # Create video player popup
        player = ctk.CTkToplevel(self.app.root)
        player.title(f"Video Player - #{job['index']+1}")
        player.geometry("720x520")
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

    def download_video_upscale(self, job, resolution="1080p"):
        """Download video in specified resolution (1080p or 4K)"""
        save_path = filedialog.asksaveasfilename(
            defaultextension=".mp4", 
            filetypes=[("MP4", "*.mp4")],
            initialfile=f"video_{resolution.lower()}_{job['index']}.mp4",
            title=f"Lưu Video {resolution}"
        )
        if not save_path: return

        media_id = job.get('mediaId')
        if not media_id:
            messagebox.showerror("Error", "Không tìm thấy Media ID của video này!")
            return

        # Get button reference for loading state
        job_idx = job['index']
        btn_key = 'btn_1080p' if resolution == "1080p" else 'btn_4k'
        original_color = "#f97316" if resolution == "1080p" else "#ec4899"
        btn = None
        if job_idx in self.job_cards:
            btn = self.job_cards[job_idx]['refs'].get(btn_key)
        
        def set_loading(text, loading=True):
            if btn:
                self.app.root.after(0, lambda: btn.configure(
                    text=text,
                    state="disabled" if loading else "normal",
                    fg_color="#4b5563" if loading else original_color
                ))

        def task():
            try:
                set_loading("⏳...", True)
                
                # Find a live account
                acc_name = job.get('account')
                acc = self.app.account_manager.get_account(acc_name)
                
                if not acc:
                    live = [a for a in self.app.account_manager.accounts if "Live" in a.get('status', '')]
                    if live:
                        acc = live[0]
                    else:
                        raise Exception("Cần ít nhất 1 tài khoản Live!")
                
                project_id = acc.get('project_id')
                
                api = LabsApiService()
                api.set_credentials(acc['cookies'], acc.get('access_token'))
                
                # Step 1: Get recaptcha token
                print(f"[{resolution}] Fetching recaptcha token...")
                set_loading("🔐 Token", True)
                
                recaptcha_token = self.app.browser_service.fetch_recaptcha_token_with_project(
                    acc['cookies'], 
                    project_id, 
                    account_id=acc['name'],
                    use_visible_browser=True, 
                    action='VIDEO_GENERATION'
                )
                
                if not recaptcha_token:
                    raise Exception("Không lấy được Recaptcha Token!")
                
                print(f"[{resolution}] Got recaptcha token: {str(recaptcha_token)[:50]}...")
                
                # Step 2: Call upscale API
                set_loading("📤 Start", True)
                print(f"[{resolution}] Starting video upscale...")
                
                # Determine aspect ratio from job
                aspect_ratio = "VIDEO_ASPECT_RATIO_LANDSCAPE"
                if job.get('ratio') == "9:16":
                    aspect_ratio = "VIDEO_ASPECT_RATIO_PORTRAIT"
                
                result = api.upscale_video(
                    media_id, 
                    project_id=project_id,
                    recaptcha_token=recaptcha_token,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution
                )
                
                if not result:
                    raise Exception(f"Không thể bắt đầu upscale video {resolution}!")
                
                # Step 3: Poll for completion
                video_url = None
                
                # Extract operation name and scene_id from response
                # Response format: { "operations": [{ "operation": {"name": "xxx_upsampled"}, "sceneId": "yyy", "status": "PENDING" }] }
                operations = result.get('operations', [])
                if operations:
                    op_data = operations[0]
                    op_name = op_data.get('operation', {}).get('name')
                    scene_id = op_data.get('sceneId', '')
                    
                    if op_name:
                        print(f"[{resolution}] Polling operation: {op_name}, sceneId: {scene_id}")
                        set_loading("⏳ Wait", True)
                        
                        poll_result = api.poll_video_upscale(op_name, scene_id, timeout=300)
                        
                        if poll_result and poll_result.get('done'):
                            video_url = poll_result.get('video_url')
                
                # If no operations, might have direct response
                if not video_url:
                    generated = result.get('generatedVideos', [])
                    if generated:
                        video_url = generated[0].get('video', {}).get('uri')
                
                if not video_url:
                    raise Exception(f"Không lấy được URL video {resolution}!")
                
                # Step 4: Download video
                set_loading("⬇️ DL", True)
                print(f"[{resolution}] Downloading: {video_url[:80]}...")
                
                import requests
                resp = requests.get(video_url, stream=True, timeout=120)
                resp.raise_for_status()
                
                with open(save_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                print(f"[{resolution}] Saved: {save_path}")
                self.app.root.after(0, lambda: messagebox.showinfo("Success", f"✅ Đã tải video {resolution}:\n{save_path}"))
                
            except Exception as e:
                print(f"[{resolution} Error] {e}")
                import traceback
                traceback.print_exc()
                self.app.root.after(0, lambda err=str(e): messagebox.showerror("Error", f"Lỗi {resolution}: {err}"))
            finally:
                set_loading(f"⬇️ {resolution}", False)
        
        threading.Thread(target=task, daemon=True).start()

    def download_all_videos(self):
        done = [j for j in self.app.job_queue if j['status'] == 'success' and j.get('video_url')]
        if not done:
            messagebox.showinfo("Info", "Chưa có video nào hoàn thành!")
            return

        folder = filedialog.askdirectory()
        if not folder: return
        
        api = LabsApiService()
        for job in done:
            name = f"short_{job['image_name']}.mp4" if job.get('image_name') else f"video_{job['index']}.mp4"
            path = os.path.join(folder, name)
            # Ensure unique name if overwriting?
            # For now keeping original logic
            url = job['video_url']
            threading.Thread(target=lambda u=url, p=path: api.download_video(u, p), daemon=True).start()
        
        messagebox.showinfo("Info", f"⬇️ Đang tải {len(done)} video...")

    def download_all_upscaled(self, resolution="1080p"):
        """Download all successful videos in specified resolution (1080p or 4K)"""
        done = [j for j in self.app.job_queue if j['status'] == 'success' and j.get('mediaId')]
        if not done:
            messagebox.showinfo("Info", "Chưa có video nào hoàn thành!")
            return
            
        folder = filedialog.askdirectory(title=f"Chọn thư mục lưu video {resolution}")
        if not folder: return
        
        btn = self.btn_download_all_1080p if resolution == "1080p" else self.btn_download_all_4k
        original_color = "#f97316" if resolution == "1080p" else "#ec4899"
        original_text = f"📥 All {resolution}"
        btn_key = 'btn_1080p' if resolution == "1080p" else 'btn_4k'
        
        def update_btn(text, loading=False):
            self.app.root.after(0, lambda: btn.configure(
                text=text,
                state="disabled" if loading else "normal",
                fg_color="#4b5563" if loading else original_color
            ))
        
        def set_card_buttons_state(disabled=True):
            """Disable/Enable all individual card buttons for this resolution"""
            def _update():
                for idx, card_data in self.job_cards.items():
                    card_btn = card_data['refs'].get(btn_key)
                    if card_btn:
                        card_btn.configure(
                            state="disabled" if disabled else "normal",
                            fg_color="#4b5563" if disabled else original_color
                        )
            self.app.root.after(0, _update)
        
        def task():
            try:
                update_btn(f"⏳ 0/{len(done)}", True)
                set_card_buttons_state(True)  # Disable individual buttons
                
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
                            action='VIDEO_GENERATION'
                        )
                        
                        if not recaptcha_token:
                            print(f"[All {resolution}] Job {i+1} - No recaptcha token!")
                            continue
                        
                        # Determine aspect ratio
                        aspect_ratio = "VIDEO_ASPECT_RATIO_LANDSCAPE"
                        if job.get('ratio') == "9:16":
                            aspect_ratio = "VIDEO_ASPECT_RATIO_PORTRAIT"
                        
                        # Call upscale API
                        print(f"[All {resolution}] Job {i+1}/{len(done)} - Upscaling...")
                        result = api.upscale_video(
                            media_id, 
                            project_id=project_id,
                            recaptcha_token=recaptcha_token,
                            aspect_ratio=aspect_ratio,
                            resolution=resolution
                        )
                        
                        if not result:
                            print(f"[All {resolution}] Job {i+1} - Upscale failed!")
                            continue
                        
                        # Poll for completion
                        video_url = None
                        operations = result.get('operations', [])
                        if operations:
                            op_data = operations[0]
                            op_name = op_data.get('operation', {}).get('name')
                            scene_id = op_data.get('sceneId', '')
                            
                            if op_name:
                                print(f"[All {resolution}] Job {i+1} - Polling: {op_name[:30]}...")
                                poll_result = api.poll_video_upscale(op_name, scene_id, timeout=300)
                                if poll_result and poll_result.get('done'):
                                    video_url = poll_result.get('video_url')
                        
                        if not video_url:
                            generated = result.get('generatedVideos', [])
                            if generated:
                                video_url = generated[0].get('video', {}).get('uri')
                        
                        if not video_url:
                            print(f"[All {resolution}] Job {i+1} - No video URL!")
                            continue
                        
                        # Download video
                        import requests
                        save_path = os.path.join(folder, f"video_{resolution.lower()}_{job['index']}.mp4")
                        resp = requests.get(video_url, stream=True, timeout=120)
                        resp.raise_for_status()
                        
                        with open(save_path, 'wb') as f:
                            for chunk in resp.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        success_count += 1
                        print(f"[All {resolution}] Job {i+1} - Saved: {save_path}")
                        
                    except Exception as e:
                        print(f"[All {resolution}] Job {i+1} error: {e}")
                        continue
                
                self.app.root.after(0, lambda: messagebox.showinfo(
                    "Success", 
                    f"✅ Đã tải {success_count}/{len(done)} video {resolution}!\n\nThư mục: {folder}"
                ))
                
            except Exception as e:
                print(f"[All {resolution} Error] {e}")
                self.app.root.after(0, lambda err=str(e): messagebox.showerror("Error", f"Lỗi: {err}"))
            finally:
                update_btn(original_text, False)
                set_card_buttons_state(False)  # Re-enable individual buttons
        
        threading.Thread(target=task, daemon=True).start()

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
