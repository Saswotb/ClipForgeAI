import customtkinter as ctk

class StatusBar(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)
        
        self.status_label = ctk.CTkLabel(self, text="Status: Ready", font=ctk.CTkFont(size=14), anchor="w")
        self.status_label.grid(row=0, column=0, sticky="ew")
        
    def set_status(self, status: str):
        self.status_label.configure(text=f"Status: {status}")