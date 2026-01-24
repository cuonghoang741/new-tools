
import tkinter as tk

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=100, height=30, corner_radius=10, 
                 bg_color="#ffffff", fg_color="#3498db", hover_color="#2980b9", text_color="#ffffff"):
        super().__init__(parent, width=width, height=height, bg=bg_color, highlightthickness=0)
        self.command = command
        self.fg_color = fg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.corner_radius = corner_radius
        self.text = text
        
        self.rect = self.create_rounded_rect(0, 0, width, height, corner_radius, fill=fg_color, outline=fg_color)
        self.text_item = self.create_text(width/2, height/2, text=text, fill=text_color, font=("Arial", 10, "bold"))
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

    def _on_click(self, event):
        if self.command:
            self.command()

    def _on_enter(self, event):
        self.itemconfig(self.rect, fill=self.hover_color, outline=self.hover_color)

    def _on_leave(self, event):
        self.itemconfig(self.rect, fill=self.fg_color, outline=self.fg_color)
