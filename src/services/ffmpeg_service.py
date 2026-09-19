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
        self, video_path: Path, output_path: Path, 
        sample_rate: int = 16000, channels: int = 1
    ) -> Path:
        self.check_ffmpeg()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd: List[str] = [
            self._ffmpeg_path, "-y", "-i", str(video_path), "-vn",
            "-acodec", "pcm_s16le", "-ar", str(sample_rate), "-ac", str(channels),
            str(output_path),
        ]

        logger.info(f"Extracting audio: '{video_path.name}' -> '{output_path.name}'")
        self._run_command(cmd)
        return output_path

    def cut_clip(
        self, video_path: Path, start_time: float, duration: float, output_path: Path
    ) -> Path:
        self.check_ffmpeg()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd: List[str] = [
            self._ffmpeg_path, "-y", "-ss", str(start_time), "-i", str(video_path),
            "-t", str(duration), "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k", str(output_path),
        ]

        logger.info(f"Cutting clip: '{video_path.name}' -> '{output_path.name}'")
        self._run_command(cmd)
        return output_path

    def convert_to_vertical(
        self, clip_path: Path, output_path: Path, width: int = 1080, height: int = 1920
    ) -> Path:
        self.check_ffmpeg()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        video_filter = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
        cmd: List[str] = [
            self._ffmpeg_path, "-y", "-i", str(clip_path), "-vf", video_filter,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "copy",
            str(output_path),
        ]

        logger.info(f"Converting to vertical: '{clip_path.name}' -> '{output_path.name}'")
        self._run_command(cmd)
        return output_path

    def burn_subtitles(self, video_path: Path, subtitle_path: Path, output_path: Path) -> Path:
        """
        Burns an SRT file into the video. 
        Includes specific path escaping required for FFmpeg on Windows.
        """
        self.check_ffmpeg()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # FFmpeg requires escaping for Windows paths in the subtitles filter
        # 1. Convert to absolute path
        # 2. Replace backslashes with forward slashes (as_posix)
        # 3. Escape the colon in the drive letter (e.g., C\: )
        sub_path_str = str(subtitle_path.resolve().as_posix()).replace(':', '\\:')
        
        # Style override: White text, black outline, bottom margin
        vf = (
            f"subtitles='{sub_path_str}':force_style="
            "'Fontsize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,MarginV=40'"
        )

        cmd: List[str] = [
            self._ffmpeg_path, "-y", "-i", str(video_path), "-vf", vf,
            "-c:v", "libx264", "-preset", "fast", "-crf", "23", "-c:a", "copy",
            str(output_path),
        ]

        logger.info(f"Burning subtitles: '{video_path.name}' -> '{output_path.name}'")
        self._run_command(cmd)
        return output_path

    def _run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        logger.debug(f"FFmpeg command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace", check=False,
            )
        except FileNotFoundError as exc:
            raise FFmpegNotFoundError("FFmpeg executable disappeared.") from exc

        if result.returncode != 0:
            stderr_tail = (result.stderr or "").strip()[-800:]
            logger.error(f"FFmpeg exited with code {result.returncode}.\nstderr: {stderr_tail}")
            raise FFmpegError(f"FFmpeg exited with code {result.returncode}. See logs.")

        return result