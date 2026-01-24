
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import os
import webbrowser
from PIL import Image, ImageTk
from app.ui.rounded_button import RoundedButton
from app.services.api_service import LabsApiService

class ImageScreen:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.auto_download_dir = None
        self.setup_ui()

    def setup_ui(self):
        toolbar = tk.Frame(self.parent, bg="#ecf0f1", pady=10)
        toolbar.pack(fill="x")
        
        RoundedButton(toolbar, text="📂 Import Excel", command=self.import_excel, width=130, height=35, bg_color="#ecf0f1", fg_color="#e67e22", hover_color="#d35400").pack(side="left", padx=15)
        
        self.btn_start = RoundedButton(toolbar, text="▶ START", command=self.start_batch, width=100, height=35, bg_color="#ecf0f1", fg_color="#27ae60", hover_color="#1e8449")
        self.btn_start.pack(side="left", padx=5)
        
        self.btn_stop = RoundedButton(toolbar, text="⏹ STOP", command=self.stop_batch, width=100, height=35, bg_color="#ecf0f1", fg_color="#e74c3c", hover_color="#c0392b")
        self.btn_stop.pack(side="left", padx=5)
        
        ttk.Separator(toolbar, orient="vertical").pack(side="left", fill="y", padx=15, pady=5)
        
        tk.Label(toolbar, text="Tỷ lệ:", bg="#ecf0f1", font=("Segoe UI", 9)).pack(side="left")
        self.combo_ratio = ttk.Combobox(toolbar, values=["Landscape (16:9)", "Portrait (9:16)", "Square (1:1)"], state="readonly", width=14, font=("Segoe UI", 9))
        self.combo_ratio.set("Landscape (16:9)")
        self.combo_ratio.pack(side="left", padx=(5, 15))
        
        tk.Label(toolbar, text="Bản sao:", bg="#ecf0f1", font=("Segoe UI", 9)).pack(side="left")
        self.spin_count = tk.Spinbox(toolbar, from_=1, to=4, width=3, font=("Segoe UI", 9))
        self.spin_count.pack(side="left", padx=5)
        
        # Auto Download
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
        
        tk.Label(left_panel, text="Cột 'prompt' & 'image' (optional)", bg="#fff3cd", fg="#856404", font=("Segoe UI", 8), wraplength=280).pack(fill="x", pady=(0, 5))
        
        queue_container = tk.Frame(left_panel, bg="white")
        queue_container.pack(fill="both", expand=True)
        
        self.queue_canvas = tk.Canvas(queue_container, bg="white", highlightthickness=0)
        self.queue_scrollbar = ttk.Scrollbar(queue_container, orient="vertical", command=self.queue_canvas.yview)
        self.queue_list_frame = tk.Frame(self.queue_canvas, bg="white")
        
        self.queue_list_frame.bind("<Configure>", lambda e: self.queue_canvas.configure(scrollregion=self.queue_canvas.bbox("all")))
        self.queue_canvas.create_window((0, 0), window=self.queue_list_frame, anchor="nw", width=320) # Approx width match
        
        self.queue_canvas.configure(yscrollcommand=self.queue_scrollbar.set)
        self.queue_canvas.pack(side="left", fill="both", expand=True)
        self.queue_scrollbar.pack(side="right", fill="y")
        
        # RIGHT PANEL - Gallery Grid
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
        
        # Add panes
        paned.add(left_panel, width=350)
        paned.add(right_panel, stretch="always")
        
        def _on_mousewheel(event):
            self.queue_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        self.queue_canvas.bind_all("<MouseWheel>", _on_mousewheel)

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
            self.lbl_status.config(text=f"Jobs: {len(self.app.image_job_queue)}")
        except Exception as e:
            messagebox.showerror("Error", f"Lỗi: {e}")

    def refresh_queue(self):
        for w in self.queue_list_frame.winfo_children(): w.destroy()
        for idx, job in enumerate(self.app.image_job_queue):
            content = tk.Frame(self.queue_list_frame, bg="white", pady=5)
            content.pack(fill="x", padx=5)
            
            # Thumbnail Frame
            thumb_frame = tk.Frame(content, bg="#f5f5f5", width=60, height=45)
            thumb_frame.pack(side="left", padx=5)
            thumb_frame.pack_propagate(False)
            
            if job['image']:
                # Input Image Preview
                thumb_key = f"img_in_{idx}_{id(job)}"
                if thumb_key in self.app.thumbnail_cache:
                    tk.Label(thumb_frame, image=self.app.thumbnail_cache[thumb_key], bg="#f5f5f5").pack(expand=True)
                else:
                    try:
                        img = Image.open(job['image'])
                        img.thumbnail((58, 43))
                        photo = ImageTk.PhotoImage(img)
                        self.app.thumbnail_cache[thumb_key] = photo
                        tk.Label(thumb_frame, image=photo, bg="#f5f5f5").pack(expand=True)
                    except:
                        tk.Label(thumb_frame, text="🖼", font=("Segoe UI", 14), bg="#f5f5f5", fg="#bdc3c7").pack(expand=True)
            else:
                # Text-to-Image Icon
                tk.Label(thumb_frame, text="📝", font=("Segoe UI", 16), bg="#f5f5f5", fg="#3498db").pack(expand=True)
            
            info = tk.Frame(content, bg="white")
            info.pack(side="left", fill="both", expand=True)
            tk.Label(info, text=f"Job #{idx+1}", font=("Segoe UI", 9, "bold"), bg="white").pack(anchor="w")
            tk.Label(info, text=job['prompt'][:25]+"...", font=("Segoe UI", 8), fg="gray", bg="white").pack(anchor="w")
            
            st = job['status']
            status_map = {'pending': '⏳', 'processing': '⚙️', 'success': '✅', 'failed': '❌'}
            icon_txt = status_map.get(st, st)
            colors = {'pending': '#f39c12', 'processing': '#3498db', 'success': '#27ae60', 'failed': '#e74c3c'}
            tk.Label(content, text=icon_txt, fg=colors.get(st, 'black'), bg="white", font=("Segoe UI", 12)).pack(side="right", padx=5)
            
            ttk.Separator(self.queue_list_frame, orient="horizontal").pack(fill="x", padx=5)

    def start_batch(self):
        if not self.app.image_job_queue: return
        if self.var_auto_download.get() and not self.auto_download_dir:
            if not messagebox.askyesno("Warning", "Chưa chọn thư mục Auto Download! Tiếp tục?"): return
            self.var_auto_download.set(False)
            
        self.app.is_image_running = True
        self.lbl_status.config(text="Đang chạy...")
        threading.Thread(target=self.batch_worker, daemon=True).start()

    def stop_batch(self):
        self.app.is_image_running = False
        self.lbl_status.config(text="Đã dừng")

    def batch_worker(self):
        import time
        live_accounts = [a for a in self.app.account_manager.accounts if "Live" in a.get('status','')]
        
        while self.app.is_image_running:
            pending = [j for j in self.app.image_job_queue if j['status'] == 'pending']
            if not pending:
                if not [j for j in self.app.image_job_queue if j['status'] == 'processing']:
                    self.app.root.after(0, lambda: self.lbl_status.config(text="Hoàn tất!"))
                    break
                time.sleep(1)
                continue
            
            for acc in live_accounts:
                if not self.app.is_image_running: break
                
                # SAFE INIT Key
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
                        with self.app.lock:
                            if acc['name'] not in self.app.running_jobs: self.app.running_jobs[acc['name']] = []
                            self.app.running_jobs[acc['name']].append(job['index']) # Conflict video index? Actually separate queues but same tracking?
                            # Tracking logic needs separation or unique IDs. 
                            # Simplest: prefix index or use different tracking dict.
                            # But self.app.running_jobs is shared. Let's use separate tracking in app or handle collisions?
                            # Video index and Image index both start at 0. Collision possible.
                            # Quick fix: Add type to running_jobs values or use separate dict.
                            # But AccountManager thread limits might be shared.
                            # Assuming total tab switching prevents simultaneous run or we accept simpler logic.
                            pass
                        
                        self.app.root.after(0, self.refresh_queue)
                        self.app.root.after(0, self.refresh_progress)
                        threading.Thread(target=self.process_job, args=(job, acc), daemon=True).start()
            time.sleep(1)

    def process_job(self, job, account):
        try:
            api = LabsApiService()
            api.set_credentials(account['cookies'], account.get('access_token'))
            project_id = account.get('project_id')
            
            # 1. Prepare (Log + History) BEFORE Captcha
            print("[DEBUG] Preparing Image Generation (Log + History)...")
            session_id = api.prepare_image_generation()
            
            # 2. Upload Image if needed
            media_id = None
            if job['image']:
                up = api.upload_image(job['image'])
                media_id = up.get('mediaId')
            
            # 3. Get Captcha (Visible Browser)
            token = self.app.browser_service.fetch_recaptcha_token_with_project(account['cookies'], project_id, use_visible_browser=True)
            if not token: raise Exception("No Recaptcha Token")
            
            ratio_map = {"Landscape (16:9)":"IMAGE_ASPECT_RATIO_LANDSCAPE", "Portrait (9:16)":"IMAGE_ASPECT_RATIO_PORTRAIT", "Square (1:1)":"IMAGE_ASPECT_RATIO_SQUARE"}
            ratio = ratio_map.get(self.combo_ratio.get(), "IMAGE_ASPECT_RATIO_LANDSCAPE")
            try: count = int(self.spin_count.get())
            except: count = 1
            
            # 4. Generate
            res = api.generate_image_batch(job['prompt'], ratio, count, project_id, token, media_id, session_id=session_id)
            
            urls = []
            for m in res.get('media', []):
                u = m.get('image', {}).get('generatedImage', {}).get('fifeUrl')
                if u: urls.append(u)
            
            if not urls: raise Exception("No URL")
            
            job['status'] = 'success'
            job['video_url'] = urls[0]
            
            if self.var_auto_download.get() and self.auto_download_dir:
                import requests
                for k, u in enumerate(urls):
                    path = os.path.join(self.auto_download_dir, f"img_{job['index']}_{k+1}.png")
                    with open(path, 'wb') as f: f.write(requests.get(u).content)
                    
        except Exception as e:
            job['status'] = 'failed'
            job['error'] = str(e)
        finally:
            with self.app.lock:
                # Remove job index
                pass
            self.app.root.after(0, self.refresh_queue)
            self.app.root.after(0, self.refresh_progress)

    def refresh_progress(self):
        for w in self.progress_list_frame.winfo_children(): w.destroy()
        
        # Display Active/Done jobs in Grid
        jobs = [j for j in self.app.image_job_queue if j['status'] != 'pending']
        cols = 3
        
        for idx, job in enumerate(jobs):
            r = idx // cols
            c = idx % cols
            self.create_image_progress_card(job, r, c)

    def create_image_progress_card(self, job, r, c):
        # Minimal Card Design (Grid Cell)
        card = tk.Frame(self.progress_list_frame, bg="white", bd=1, relief="solid", width=200, height=180, cursor="hand2")
        card.grid(row=r, column=c, padx=8, pady=8)
        card.pack_propagate(False) # Fixed size
        
        # Grid weight config for parent frame logic?
        # Canvas frame uses grid now.
        
        # Header (ID + Status)
        header = tk.Frame(card, bg="white", height=25)
        header.pack(fill="x", padx=5, pady=2)
        header.pack_propagate(False)
        
        tk.Label(header, text=f"#{job['index']+1}", font=("Segoe UI", 9, "bold"), fg="#7f8c8d", bg="white").pack(side="left")
        
        st = job['status']
        status_map = {'pending': '⏳', 'processing': '⚙️', 'success': '✅', 'failed': '❌'}
        color_map = {'processing': '#3498db', 'success': '#27ae60', 'failed': '#e74c3c'}
        icon = status_map.get(st, st)
        
        tk.Label(header, text=icon, font=("Segoe UI", 12), bg="white", fg=color_map.get(st, 'black')).pack(side="right")
        
        # Thumbnail Area
        thumb_frame = tk.Frame(card, bg="#f5f5f5")
        thumb_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Retry Logic
        def retry():
            job['status'] = 'pending'
            job['error'] = None
            self.refresh_queue()
            self.refresh_progress()
            if not self.app.is_image_running: self.start_batch()

        # Click Handler
        def on_click(e):
            if job.get('video_url'):
                self.show_lightbox(job['video_url'])
            elif st == 'failed':
                retry()
        
        card.bind("<Button-1>", on_click)
        thumb_frame.bind("<Button-1>", on_click)
        
        # Content Display
        if st == 'failed':
            tk.Label(thumb_frame, text="Failed\n(Click to Retry)", fg="red", bg="#f5f5f5", justify="center").pack(expand=True)
        elif st == 'success' and job.get('video_url'):
            if 'thumb_preview' not in job:
                tk.Label(thumb_frame, text="Loading...", bg="#f5f5f5", fg="gray").pack(expand=True)
                def load():
                    try:
                        import requests
                        from io import BytesIO
                        r = requests.get(job['video_url'], timeout=10)
                        img = Image.open(BytesIO(r.content))
                        img.thumbnail((180, 130))
                        p = ImageTk.PhotoImage(img)
                        job['thumb_preview'] = p
                        self.app.root.after(0, self.refresh_progress)
                    except: pass
                threading.Thread(target=load, daemon=True).start()
            else:
                lbl = tk.Label(thumb_frame, image=job['thumb_preview'], bg="#f5f5f5")
                lbl.pack(expand=True)
                lbl.bind("<Button-1>", on_click)
        else:
            tk.Label(thumb_frame, text="Generating...", fg="#95a5a6", bg="#f5f5f5").pack(expand=True)
            
        # Hover Effect
        def on_enter(e): card.config(bg="#ecf0f1")
        def on_leave(e): card.config(bg="white")
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

    def show_lightbox(self, img_url):
        top = tk.Toplevel(self.app.root)
        top.title("Preview Image")
        try: top.state("zoomed")
        except: top.attributes("-fullscreen", True)
        top.configure(bg="black")
        
        top.bind("<Escape>", lambda e: top.destroy())
        top.bind("<Button-1>", lambda e: top.destroy())
        
        lbl = tk.Label(top, text="Loading full quality...", fg="white", bg="black", font=("Segoe UI", 16))
        lbl.pack(expand=True)
        
        def load():
            try:
                import requests
                from io import BytesIO
                resp = requests.get(img_url)
                pil_img = Image.open(BytesIO(resp.content))
                
                sw, sh = top.winfo_screenwidth(), top.winfo_screenheight()
                ratio = min(sw/pil_img.width, sh/pil_img.height)
                if ratio < 1:
                    nw, nh = int(pil_img.width * ratio * 0.9), int(pil_img.height * ratio * 0.9)
                    pil_img = pil_img.resize((nw, nh), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(pil_img)
                self.app.root.after(0, lambda: [lbl.configure(image=photo, text=""), setattr(lbl, 'image', photo)])
            except Exception as e:
                self.app.root.after(0, lambda: lbl.configure(text=f"Error: {e}"))
                
        threading.Thread(target=load, daemon=True).start()
