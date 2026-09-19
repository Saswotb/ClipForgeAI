import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

class FFmpegNotFoundError(Exception):
    pass

class FFmpegError(Exception):
    pass

class FFmpegService:
    """Central abstraction around the FFmpeg command-line tool."""

    def __init__(self) -> None:
        self._ffmpeg_path: Optional[str] = None

    def check_ffmpeg(self) -> str:
        if self._ffmpeg_path:
            return self._ffmpeg_path

        path = shutil.which("ffmpeg")
        if path is None:
            raise FFmpegNotFoundError(
                "FFmpeg was not found.\n\nPlease install FFmpeg and add it to your system PATH."
            )

        self._ffmpeg_path = path
        logger.info(f"FFmpeg found at: {path}")
        return path

    def extract_audio(
        self,
        video_path: Path,
        output_path: Path,
        sample_rate: int = 16000,
        channels: int = 1,
    ) -> Path:
        self.check_ffmpeg()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd: List[str] = [
            self._ffmpeg_path, "-y",
            "-i", str(video_path),
            "-vn",
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", str(channels),
            str(output_path),
        ]

        logger.info(f"Extracting audio: '{video_path.name}' -> '{output_path.name}'")
        self._run_command(cmd)

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise FFmpegError("Audio extraction produced no output file.")

        return output_path

    def cut_clip(
        self,
        video_path: Path,
        start_time: float,
        duration: float,
        output_path: Path
    ) -> Path:
        """
        Cuts a specific segment from a video.
        Re-encodes to ensure frame-accurate start and end times.
        """
        self.check_ffmpeg()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd: List[str] = [
            self._ffmpeg_path, "-y",
            "-ss", str(start_time),      # Fast seek to start time
            "-i", str(video_path),       # Input
            "-t", str(duration),         # Duration of the clip
            "-c:v", "libx264",           # Re-encode video for exact cuts
            "-preset", "fast",
            "-crf", "23",                # Standard quality
            "-c:a", "aac",               # Re-encode audio
            "-b:a", "192k",
            str(output_path),
        ]

        logger.info(f"Cutting clip: '{video_path.name}' ({start_time:.2f}s to {start_time + duration:.2f}s) -> '{output_path.name}'")
        self._run_command(cmd)

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise FFmpegError(f"Clip generation failed for {output_path.name}")

        return output_path

    def convert_to_vertical(
        self,
        clip_path: Path,
        output_path: Path,
        width: int = 1080,
        height: int = 1920
    ) -> Path:
        """
        Converts a clip to vertical 9:16 format.
        Uses a center-crop strategy that scales the video to fill the frame 
        without stretching, preserving the original aspect ratio of the content.
        """
        self.check_ffmpeg()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Filter explanation:
        # 1. scale=...:increase -> Scales the video so the smaller dimension fits the target, 
        #    ensuring the video completely covers the 1080x1920 area.
        # 2. crop=1080:1920 -> Crops the excess edges to exactly 1080x1920.
        video_filter = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"

        cmd: List[str] = [
            self._ffmpeg_path, "-y",
            "-i", str(clip_path),
            "-vf", video_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "copy",             # Copy audio stream (no need to re-encode)
            str(output_path),
        ]

        logger.info(f"Converting to vertical ({width}x{height}): '{clip_path.name}' -> '{output_path.name}'")
        self._run_command(cmd)

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise FFmpegError(f"Vertical conversion failed for {output_path.name}")

        return output_path

    def _run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
        except FileNotFoundError as exc:
            raise FFmpegNotFoundError("FFmpeg executable disappeared during execution.") from exc

        if result.returncode != 0:
            stderr_tail = (result.stderr or "").strip()[-800:]
            logger.error(
                f"FFmpeg exited with code {result.returncode}.\n"
                f"Command: {' '.join(cmd)}\n"
                f"stderr: {stderr_tail}"
            )
            raise FFmpegError(
                f"FFmpeg exited with code {result.returncode}. See logs for details."
            )

        return result