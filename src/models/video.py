from dataclasses import dataclass
from pathlib import Path

@dataclass
class Video:
    """Data model representing an imported video file."""
    path: Path
    filename: str
    duration: float       # in seconds
    width: int
    height: int
    fps: float
    frame_count: int
    file_size: int        # in bytes
    format: str

    @property
    def formatted_duration(self) -> str:
        """Returns duration formatted as HH:MM:SS or MM:SS."""
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def formatted_file_size(self) -> str:
        """Returns file size formatted as MB or GB."""
        size_mb = self.file_size / (1024 * 1024)
        if size_mb >= 1024:
            return f"{size_mb / 1024:.2f} GB"
        return f"{size_mb:.2f} MB"

    @property
    def resolution(self) -> str:
        """Returns resolution formatted as WxH."""
        return f"{self.width}x{self.height}"