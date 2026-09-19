from pathlib import Path
from typing import List

from src.config.paths import OUTPUT_CLIPS_DIR
from src.models.clip import Clip, HighlightCandidate
from src.services.ffmpeg_service import FFmpegService
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ClipGenerator:
    """
    Generates actual video files from highlight candidates.
    """

    def __init__(self, ffmpeg_service: FFmpegService):
        self.ffmpeg = ffmpeg_service

    def generate_clips(
        self, 
        video_path: Path, 
        candidates: List[HighlightCandidate], 
        job_id: str
    ) -> List[Clip]:
        """
        Cuts the source video into individual clips based on the candidates.
        """
        if not candidates:
            logger.warning("No candidates provided to generate clips.")
            return []

        OUTPUT_CLIPS_DIR.mkdir(parents=True, exist_ok=True)
        generated_clips: List[Clip] = []

        logger.info(f"Generating {len(candidates)} clips from '{video_path.name}'...")

        for i, candidate in enumerate(candidates):
            clip_filename = f"{job_id}_clip_{i+1:03d}.mp4"
            output_path = OUTPUT_CLIPS_DIR / clip_filename

            try:
                self.ffmpeg.cut_clip(
                    video_path=video_path,
                    start_time=candidate.start_time,
                    duration=candidate.duration,
                    output_path=output_path
                )

                clip = Clip(
                    source_video=video_path,
                    start_time=candidate.start_time,
                    end_time=candidate.end_time,
                    duration=candidate.duration,
                    score=candidate.score,
                    title=f"Clip {i+1}",
                    output_path=output_path
                )
                generated_clips.append(clip)
                logger.info(f"Successfully generated: {clip_filename} (Score: {candidate.score})")

            except Exception as e:
                logger.error(f"Failed to generate clip {i+1}: {e}")
                # Continue to the next clip instead of failing the whole job

        logger.info(f"Clip generation complete. {len(generated_clips)} clips created.")
        return generated_clips