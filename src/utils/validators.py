import os
from pathlib import Path
from src.config.settings import SUPPORTED_FORMATS
from src.utils.logger import get_logger

logger = get_logger(__name__)


def validate_video_file(video_path: Path) -> None:
    """
    Validate a video file before processing.

    Checks that the file exists, is readable, has a supported extension,
    and is not empty. Raises ValueError with a clear message on failure.
    """
    if video_path is None:
        raise ValueError("No video file was provided.")

    if not video_path.exists():
        raise ValueError(f"File does not exist: {video_path}")

    if not video_path.is_file():
        raise ValueError(f"Path is not a file: {video_path}")

    if not os.access(video_path, os.R_OK):
        raise ValueError(f"File is not readable (check permissions): {video_path}")

    if video_path.suffix.lower() not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format '{video_path.suffix}'. "
            f"Supported: {', '.join(SUPPORTED_FORMATS)}"
        )

    if video_path.stat().st_size == 0:
        raise ValueError(f"File is empty: {video_path}")

    logger.info(f"Validation passed for: {video_path.name}")


def validate_output_directory(directory: Path) -> None:
    """Ensure an output directory exists and is writable."""
    directory.mkdir(parents=True, exist_ok=True)
    if not os.access(directory, os.W_OK):
        raise ValueError(f"Output directory is not writable: {directory}")