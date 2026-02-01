
import customtkinter as ctk
from tkinter import messagebox
import threading

class UpdateDialog:
    """
    Update notification dialog with download progress
    """
    
    def __init__(self, parent, updater_service, version, notes, on_close=None):
        self.parent = parent
        self.updater = updater_service
        self.version = version
        self.notes = notes
        self.on_close = on_close
        self.is_downloading = False
        
        self.create_dialog()
    
    def create_dialog(self):
        # Create toplevel window
        self.dialog = ctk.CTkToplevel(self.parent)
        self.dialog.title("🔄 Cập nhật mới")
        self.dialog.geometry("520x520")
        self.dialog.resizable(False, False)
        
        # Center on parent
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Make it appear on top
        self.dialog.after(10, lambda: self.dialog.lift())
        self.dialog.after(10, lambda: self.dialog.focus_force())
        
        # Main container
        main_frame = ctk.CTkFrame(self.dialog, fg_color="#1a1a2e", corner_radius=0)
        main_frame.pack(fill="both", expand=True)
        
        # Header
        header = ctk.CTkFrame(main_frame, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 20))
        
        ctk.CTkLabel(
            header,
            text="🎉",
            font=("Segoe UI Emoji", 48)
        ).pack()
        
        ctk.CTkLabel(
            header,
            text="Có phiên bản mới!",
            font=("SF Pro Display", 20, "bold"),
            text_color="#ffffff"
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            header,
            text=f"Phiên bản {self.version} đã sẵn sàng",
            font=("SF Pro Display", 13),
            text_color="#6c7293"
        ).pack()
        
        # Release notes
        notes_frame = ctk.CTkFrame(main_frame, fg_color="#16213e", corner_radius=12)
        notes_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        ctk.CTkLabel(
            notes_frame,
            text="📋 Có gì mới:",
            font=("SF Pro Display", 12, "bold"),
            text_color="#a0a3bd",
            anchor="w"
        ).pack(fill="x", padx=15, pady=(15, 5))
        
        # Scrollable notes
        notes_text = ctk.CTkTextbox(
            notes_frame,
            font=("SF Pro Display", 11),
            fg_color="transparent",
            text_color="#ffffff",
            height=80,
            wrap="word"
        )
        notes_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        notes_text.insert("1.0", self.notes or "Không có ghi chú")
        notes_text.configure(state="disabled")
        
        # Progress section (hidden initially)
        self.progress_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=30, pady=(0, 10))
        
        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=("SF Pro Display", 11),
            text_color="#6c7293"
        )
        self.progress_label.pack(fill="x")
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            height=8,
            corner_radius=4,
            fg_color="#2a2a4e",
            progress_color="#6366f1"
        )
        self.progress_bar.set(0)
        # Hidden initially
        
        # Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=30, pady=(0, 25))
        
        self.btn_later = ctk.CTkButton(
            btn_frame,
            text="Để sau",
            font=("SF Pro Display", 12),
            width=120,
            height=40,
            corner_radius=10,
            fg_color="#374151",
            hover_color="#4b5563",
            command=self.on_later
        )
        self.btn_later.pack(side="left")
        
        self.btn_update = ctk.CTkButton(
            btn_frame,
            text="🚀 Cập nhật ngay",
            font=("SF Pro Display", 12, "bold"),
            width=180,
            height=40,
            corner_radius=10,
            fg_color="#6366f1",
            hover_color="#5855eb",
            command=self.on_update
        )
        self.btn_update.pack(side="right")
        
        # Handle close button
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_later)
    
    def on_later(self):
        if self.is_downloading:
            if not messagebox.askyesno("Xác nhận", "Đang tải xuống! Bạn có chắc muốn hủy?"):
                return
        
        self.dialog.destroy()
        if self.on_close:
            self.on_close()
    
    def on_update(self):
        if self.is_downloading:
            return
        
        self.is_downloading = True
        self.btn_update.configure(state="disabled", text="Đang tải...")
        self.btn_later.configure(state="disabled")
        
        # Show progress
        self.progress_label.configure(text="Đang tải xuống...")
        self.progress_bar.pack(fill="x", pady=(5, 0))
        
        # Start download in thread
        threading.Thread(target=self.download_and_apply, daemon=True).start()
    
    def update_progress(self, percent):
        self.dialog.after(0, lambda: self._update_progress_ui(percent))
    
    def _update_progress_ui(self, percent):
        self.progress_bar.set(percent / 100)
        self.progress_label.configure(text=f"Đang tải xuống... {percent}%")
    
    def download_and_apply(self):
        # Download
        success, file_path, error = self.updater.download_update(
            progress_callback=self.update_progress
        )
        
        if not success:
            self.dialog.after(0, lambda: self.show_error(error))
            return
        
        self.dialog.after(0, lambda: self.progress_label.configure(text="Đang cài đặt..."))
        
        # Apply update
        success, error = self.updater.apply_update(file_path)
        
        if not success:
            self.dialog.after(0, lambda: self.show_error(error))
            return
        
        # Success - quit app
        self.dialog.after(0, self.on_update_success)
    
    def show_error(self, error):
        self.is_downloading = False
        self.btn_update.configure(state="normal", text="🚀 Cập nhật ngay")
        self.btn_later.configure(state="normal")
        self.progress_bar.pack_forget()
        self.progress_label.configure(text="")
        messagebox.showerror("Lỗi", error)
    
    def on_update_success(self):
        messagebox.showinfo("Cập nhật", "Cập nhật thành công! Ứng dụng sẽ tự khởi động lại.")
        # Exit application
        self.dialog.destroy()
        self.parent.destroy()


def check_for_updates_async(parent, on_update_available=None, silent=False):
    """
    Check for updates in background thread.
    If update available, show dialog.
    
    Args:
        parent: Parent window (CTk root)
        on_update_available: Callback when update is available
        silent: If True, don't show "no update" message
    """
    from app.services.updater_service import UpdaterService
    
    def check():
        updater = UpdaterService()
        has_update, version, notes, error = updater.check_for_updates()
        
        if error and not silent:
            parent.after(0, lambda: messagebox.showwarning("Kiểm tra cập nhật", error))
            return
        
        if has_update:
            parent.after(0, lambda: UpdateDialog(parent, updater, version, notes))
            if on_update_available:
                parent.after(0, on_update_available)
        elif not silent:
            parent.after(0, lambda: messagebox.showinfo(
                "Kiểm tra cập nhật", 
                f"Bạn đang dùng phiên bản mới nhất (v{updater.get_current_version()})"
            ))
    
    threading.Thread(target=check, daemon=True).start()
