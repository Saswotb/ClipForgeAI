import customtkinter as ctk

class ProgressPanel(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        
        self.progress_bar = ctk.CTkProgressBar(self, width=300)
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(self, text="0%", font=ctk.CTkFont(size=14))
        self.progress_label.grid(row=0, column=1, padx=(10, 0))
        
    def set_progress(self, value: float, stage: str = ""):
        self.progress_bar.set(value)
        self.progress_label.configure(text=f"{stage} {int(value * 100)}%")