import customtkinter as ctk
from src.config.app_config import APP_NAME, APP_VERSION


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, on_browse, on_process, on_settings, on_cancel, **kwargs):
        super().__init__(parent, **kwargs)
        self.grid_columnconfigure(0, weight=1)

        self.on_browse = on_browse
        self.on_process = on_process
        self.on_settings = on_settings
        self.on_cancel = on_cancel

        # Logo / Title
        self.title_label = ctk.CTkLabel(
            self, text=f"🎬 {APP_NAME}", font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        # Browse Button
        self.browse_btn = ctk.CTkButton(
            self, text="📂 Browse Video", command=self.on_browse, height=40
        )
        self.browse_btn.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # Process Button
        self.process_btn = ctk.CTkButton(
            self, text="▶ Start Process", command=self.on_process, height=40, state="disabled"
        )
        self.process_btn.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

        # Cancel Button
        self.cancel_btn = ctk.CTkButton(
            self, text="✕ Cancel", command=self.on_cancel, height=40,
            fg_color="#b3261e", hover_color="#8c1d18", state="disabled"
        )
        self.cancel_btn.grid(row=3, column=0, padx=20, pady=10, sticky="ew")

        # Settings Button
        self.settings_btn = ctk.CTkButton(
            self, text="⚙ Settings", command=self.on_settings, height=40,
            fg_color="transparent", border_width=1
        )
        self.settings_btn.grid(row=4, column=0, padx=20, pady=10, sticky="ew")

        # Selected File Label
        self.file_label = ctk.CTkLabel(
            self, text="No video selected", text_color="gray", wraplength=180
        )
        self.file_label.grid(row=5, column=0, padx=20, pady=(20, 10))

        # Spacer
        self.grid_rowconfigure(6, weight=1)

        # Version Label
        self.version_label = ctk.CTkLabel(self, text=f"v{APP_VERSION}", text_color="gray")
        self.version_label.grid(row=7, column=0, padx=20, pady=20)

    # -- State helpers -----------------------------------------------------

    def set_selected_file(self, filename: str) -> None:
        self.file_label.configure(text=filename, text_color=("gray10", "gray90"))
        self.process_btn.configure(state="normal")

    def set_idle_state(self) -> None:
        """Default state: browse enabled, process depends on selection, cancel disabled."""
        self.browse_btn.configure(state="normal")
        self.settings_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        has_video = self.file_label.cget("text") != "No video selected"
        self.process_btn.configure(state="normal" if has_video else "disabled")

    def set_processing_state(self) -> None:
        """During processing: browse/process/settings disabled, cancel enabled."""
        self.browse_btn.configure(state="disabled")
        self.process_btn.configure(state="disabled")
        self.settings_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")