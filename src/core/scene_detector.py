import cv2
from pathlib import Path
from typing import List, Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)

class SceneDetector:
    """
    Detects scene changes in a video using OpenCV.
    Uses frame differencing to identify visual cuts or significant changes.
    """

    def __init__(self, threshold: float = 30.0, sample_fps: float = 2.0):
        """
        Args:
            threshold: The mean absolute difference threshold to trigger a scene change.
            sample_fps: How many frames per second to analyze (saves processing time).
        """
        self.threshold = threshold
        self.sample_fps = sample_fps

    def detect_scenes(self, video_path: Path) -> List[Tuple[float, float]]:
        """
        Analyzes the video and returns a list of scene boundaries.
        Returns a list of tuples: [(start_time, end_time), ...]
        """
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found for scene detection: {video_path}")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video for scene detection: {video_path.name}")

        try:
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            if video_fps <= 0:
                video_fps = 30.0
                
            frame_interval = max(1, int(video_fps / self.sample_fps))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            scenes: List[Tuple[float, float]] = []
            current_scene_start = 0.0
            
            prev_gray = None
            frame_idx = 0
            
            logger.info(f"Starting scene detection on '{video_path.name}' (sampling at {self.sample_fps} FPS)...")

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_idx % frame_interval == 0:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    if prev_gray is not None:
                        # Calculate mean absolute difference between frames
                        diff = cv2.absdiff(prev_gray, gray)
                        mean_diff = float(diff.mean())
                        
                        if mean_diff > self.threshold:
                            current_time = frame_idx / video_fps
                            scenes.append((current_scene_start, current_time))
                            current_scene_start = current_time
                            logger.debug(f"Scene change detected at {current_time:.2f}s (diff: {mean_diff:.2f})")
                            
                    prev_gray = gray
                    
                frame_idx += 1

            # Add the final scene
            if current_scene_start < (total_frames / video_fps):
                scenes.append((current_scene_start, total_frames / video_fps))

            logger.info(f"Scene detection complete. Found {len(scenes)} scenes.")
            return scenes
            
        finally:
            cap.release()