from pathlib import Path
from typing import List

from src.config.settings import OUTPUT_WIDTH, OUTPUT_HEIGHT
from src.models.clip import Clip
from src.services.ffmpeg_service import FFmpegService
from src.utils.logger import get_logger

logger = get_logger(__name__)

class VerticalConverter:
    """
    Converts generated landscape/square clips into vertical 9:16 format.
    """

    def __init__(self, ffmpeg_service: FFmpegService):
        self.ffmpeg = ffmpeg_service

    def convert_clips(self, clips: List[Clip]) -> List[Clip]:
        """
        Iterates through the generated clips and converts them to vertical format.
        Updates the Clip model with the new vertical file path.
        """
        if not clips:
            return []

        logger.info(f"Converting {len(clips)} clips to vertical format ({OUTPUT_WIDTH}x{OUTPUT_HEIGHT})...")
        
        converted_clips = []

        for clip in clips:
            if clip.output_path is None or not clip.output_path.exists():
                logger.warning(f"Skipping vertical conversion for clip with missing source: {clip.title}")
                continue

            # Create vertical filename (e.g., clip_001_vertical.mp4)
            vertical_path = clip.output_path.with_name(
                clip.output_path.stem + "_vertical.mp4"
            )

            try:
                self.ffmpeg.convert_to_vertical(
                    clip_path=clip.output_path,
                    output_path=vertical_path,
                    width=OUTPUT_WIDTH,
                    height=OUTPUT_HEIGHT
                )
                
                # Update the clip model to point to the final vertical version
                clip.output_path = vertical_path
                converted_clips.append(clip)
                logger.info(f"Successfully converted to vertical: {vertical_path.name}")

            except Exception as e:
                logger.error(f"Failed to convert clip to vertical {clip.output_path.name}: {e}")
                # Keep the original horizontal clip if vertical conversion fails
                converted_clips.append(clip)

        logger.info(f"Vertical conversion complete. {len(converted_clips)} clips processed.")
        return converted_clips