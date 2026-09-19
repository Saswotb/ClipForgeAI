from pathlib import Path
from typing import List

from src.config.paths import OUTPUT_SUBTITLES_DIR
from src.models.clip import Clip
from src.models.transcript import Transcript, TranscriptSegment
from src.services.ffmpeg_service import FFmpegService
from src.utils.logger import get_logger

logger = get_logger(__name__)

class SubtitleGenerator:
    """
    Generates SRT subtitle files from transcript segments and burns them into the video.
    """

    def __init__(self, ffmpeg_service: FFmpegService):
        self.ffmpeg = ffmpeg_service

    def generate_and_burn(self, clips: List[Clip], transcript: Transcript) -> List[Clip]:
        """
        Iterates through clips, generates an SRT file for each, and burns it into the video.
        """
        OUTPUT_SUBTITLES_DIR.mkdir(parents=True, exist_ok=True)
        
        for clip in clips:
            if not clip.output_path or not clip.output_path.exists():
                continue

            try:
                # 1. Filter and adjust transcript segments for this specific clip
                clip_segments = self._filter_segments(transcript.segments, clip.start_time, clip.end_time)
                if not clip_segments:
                    logger.warning(f"No transcript segments found for clip {clip.title}")
                    continue
                
                # 2. Generate SRT file
                srt_path = self._generate_srt(clip, clip_segments)
                clip.subtitle_path = srt_path
                
                # 3. Burn subtitles into the video
                burned_path = clip.output_path.with_name(clip.output_path.stem + "_captioned.mp4")
                self.ffmpeg.burn_subtitles(clip.output_path, srt_path, burned_path)
                
                # Update the clip's output path to the newly captioned version
                clip.output_path = burned_path
                logger.info(f"Successfully burned subtitles for {clip.title}")
                
            except Exception as e:
                logger.error(f"Failed to generate/burn subtitles for {clip.title}: {e}")
                
        return clips

    def _filter_segments(self, segments: List[TranscriptSegment], start: float, end: float) -> List[TranscriptSegment]:
        """Filters segments that overlap with the clip and adjusts their timestamps to start at 0.0."""
        filtered = []
        for seg in segments:
            # Check for overlap
            if seg.end > start and seg.start < end:
                # Adjust times relative to the clip's start time
                new_start = max(0.0, seg.start - start)
                new_end = min(end - start, seg.end - start)
                filtered.append(TranscriptSegment(start=new_start, end=new_end, text=seg.text))
        return filtered

    def _generate_srt(self, clip: Clip, segments: List[TranscriptSegment]) -> Path:
        """Writes the segments to a standard .srt file."""
        srt_filename = f"{clip.output_path.stem}.srt"
        srt_path = OUTPUT_SUBTITLES_DIR / srt_filename
        
        with open(srt_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                start_time = self._format_srt_time(seg.start)
                end_time = self._format_srt_time(seg.end)
                f.write(f"{i}\n{start_time} --> {end_time}\n{seg.text.strip()}\n\n")
                
        logger.info(f"Generated SRT: {srt_path.name}")
        return srt_path

    def _format_srt_time(self, seconds: float) -> str:
        """Converts seconds to SRT time format: HH:MM:SS,mmm"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"