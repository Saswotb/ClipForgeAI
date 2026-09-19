import cv2
from pathlib import Path
from typing import List, Optional
from PIL import Image

from src.config.paths import OUTPUT_THUMBNAILS_DIR
from src.models.clip import Clip
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ThumbnailGenerator:
    """
    Extracts a representative frame from the clip and saves it as a PNG thumbnail.
    """

    def generate_thumbnails(self, clips: List[Clip]) -> List[Clip]:
        OUTPUT_THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)
        
        for clip in clips:
            if not clip.output_path or not clip.output_path.exists():
                continue
                
            try:
                # Extract a frame from the middle of the clip
                mid_time = clip.duration / 2.0
                frame = self._extract_frame(clip.output_path, mid_time)
                
                if frame is not None:
                    thumb_path = OUTPUT_THUMBNAILS_DIR / f"{clip.output_path.stem}.png"
                    Image.fromarray(frame).save(thumb_path)
                    clip.thumbnail_path = thumb_path
                    logger.info(f"Generated thumbnail: {thumb_path.name}")
                    
            except Exception as e:
                logger.error(f"Failed to generate thumbnail for {clip.title}: {e}")
                
        return clips

    def _extract_frame(self, video_path: Path, timestamp: float) -> Optional[any]:
        """Extracts a single frame at the given timestamp using OpenCV."""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return None
            
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0: 
                fps = 30.0
                
            frame_num = int(timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            
            ret, frame = cap.read()
            if ret:
                # Convert BGR to RGB for Pillow
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return None
        finally:
            cap.release()