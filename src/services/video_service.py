import cv2
from pathlib import Path
from PIL import Image
from src.models.video import Video
from src.utils.logger import get_logger

logger = get_logger(__name__)

class VideoService:
    """Service responsible for reading video metadata and extracting frames."""

    @staticmethod
    def get_video_metadata(video_path: Path) -> Video:
        """Reads video metadata using OpenCV and returns a Video model."""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error(f"Failed to open video file: {video_path}")
            raise ValueError(f"Could not open video file: {video_path.name}")

        try:
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Fallback for FPS if OpenCV returns 0 (common in some containers)
            if fps <= 0:
                logger.warning(f"FPS returned 0 for {video_path.name}. Defaulting to 30.0 for duration calculation.")
                fps = 30.0 
                
            duration = frame_count / fps if fps > 0 else 0.0
            
            file_size = video_path.stat().st_size
            format_ext = video_path.suffix.lower().lstrip('.')

            video = Video(
                path=video_path,
                filename=video_path.name,
                duration=duration,
                width=width,
                height=height,
                fps=fps,
                frame_count=frame_count,
                file_size=file_size,
                format=format_ext
            )
            logger.info(f"Successfully loaded metadata for {video_path.name} ({video.resolution}, {video.formatted_duration})")
            return video
        finally:
            cap.release()

    @staticmethod
    def get_preview_frame(video_path: Path, timestamp: float = 0.0) -> Image.Image:
        """Extracts a single frame from the video as a PIL Image."""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video file for preview: {video_path.name}")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            if timestamp > 0 and fps > 0:
                frame_number = int(timestamp * fps)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            if not ret:
                # Fallback to first frame if seeking fails
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    raise ValueError("Could not read any frames from the video.")

            # Convert BGR (OpenCV default) to RGB (PIL requirement)
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame_rgb)
        finally:
            cap.release()