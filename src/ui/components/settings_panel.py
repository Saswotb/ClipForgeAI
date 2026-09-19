import customtkinter as ctk
from src.config.settings import WHISPER_MODEL, MIN_CLIP_DURATION, MAX_CLIP_DURATION

class SettingsPanel(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        
        self.title_label = ctk.CTkLabel(self, text="SETTINGS", font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")
        
        self.ai_highlights_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self, text="AI Highlight Detection", variable=self.ai_highlights_var).grid(row=1, column=0, padx=20, pady=5, sticky="w")
        
        self.auto_captions_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self, text="Automatic Captions", variable=self.auto_captions_var).grid(row=2, column=0, padx=20, pady=5, sticky="w")
        
        self.vertical_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self, text="Vertical 9:16", variable=self.vertical_var).grid(row=3, column=0, padx=20, pady=5, sticky="w")
        
        self.thumbnail_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(self, text="Generate Thumbnail", variable=self.thumbnail_var).grid(row=4, column=0, padx=20, pady=5, sticky="w")
        
        ctk.CTkLabel(self, text="Clip Duration", font=ctk.CTkFont(weight="bold")).grid(row=5, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.min_duration_entry = ctk.CTkEntry(self, placeholder_text=f"Min: {MIN_CLIP_DURATION}s", width=100)
        self.min_duration_entry.insert(0, str(MIN_CLIP_DURATION))
        self.min_duration_entry.grid(row=6, column=0, padx=20, pady=5, sticky="w")
        
        self.max_duration_entry = ctk.CTkEntry(self, placeholder_text=f"Max: {MAX_CLIP_DURATION}s", width=100)
        self.max_duration_entry.insert(0, str(MAX_CLIP_DURATION))
        self.max_duration_entry.grid(row=7, column=0, padx=20, pady=5, sticky="w")
        
        ctk.CTkLabel(self, text="Whisper Model", font=ctk.CTkFont(weight="bold")).grid(row=8, column=0, padx=20, pady=(20, 5), sticky="w")
        
        self.model_dropdown = ctk.CTkOptionMenu(self, values=["tiny", "base", "small", "medium", "large"])
        self.model_dropdown.set(WHISPER_MODEL)
        self.model_dropdown.grid(row=9, column=0, padx=20, pady=5, sticky="ew")