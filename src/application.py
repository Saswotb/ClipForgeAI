import customtkinter as ctk
from src.config import app_config, ui_config
from src.utils.logger import setup_logger, get_logger
from src.ui.windows.main_window import MainWindow

class Application:
    def __init__(self):
        setup_logger()
        self.logger = get_logger(__name__)
        self.logger.info(f"Initializing {app_config.APP_NAME} v{app_config.APP_VERSION}...")
        
        ctk.set_appearance_mode(ui_config.THEME)
        ctk.set_default_color_theme(ui_config.COLOR_THEME)
        
        self.main_window = MainWindow()
        
    def run(self):
        self.logger.info("Starting GUI event loop.")
        try:
            self.main_window.mainloop()
        except KeyboardInterrupt:
            self.logger.info("Application closed by user.")
        except Exception as e:
            self.logger.critical(f"Fatal error in main loop: {e}", exc_info=True)