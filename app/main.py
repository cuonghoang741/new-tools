
import customtkinter as ctk
from app.ui.main_window import MainWindow

# Configure CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

if __name__ == "__main__":
    root = ctk.CTk()
    root.configure(fg_color="#0f0f23")
    app = MainWindow(root)
    root.mainloop()
