from tkinter import filedialog
from pathlib import Path
from src.config.settings import SUPPORTED_FORMATS
from src.utils.logger import get_logger

logger = get_logger(__name__)

class FileService:
    @staticmethod
    def open_video_dialog() -> Path | None:
        filetypes = [
            ("Video Files", " ".join(SUPPORTED_FORMATS)),
            ("All Files", "*.*")
        ]
        
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=filetypes
        )
        
        if not file_path:
            logger.info("File dialog cancelled by user.")
            return None
            
        path = Path(file_path)
        
        if path.suffix.lower() not in SUPPORTED_FORMATS:
            logger.error(f"Unsupported file format selected: {path.suffix}")
            return None
            
        if not path.exists() or path.stat().st_size == 0:
            logger.error(f"Invalid or empty file selected: {path}")
            return None
            
        logger.info(f"Valid video file selected: {path.name}")
        return path