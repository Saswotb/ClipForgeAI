import shutil
import subprocess
from pathlib import Path
from typing import List, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)


class FFmpegNotFoundError(Exception):
    """Raised when the FFmpeg executable cannot be located."""
    pass


class FFmpegError(Exception):
    """Raised when FFmpeg exits with a non-zero return code."""
    pass


class FFmpegService:
    """
    Central abstraction around the FFmpeg command-line tool.

    All FFmpeg invocations in the project should go through this service
    rather than scattering raw subprocess calls throughout the codebase.
    """

    def __init__(self) -> None:
        self._ffmpeg_path: Optional[str] = None

    def check_ffmpeg(self) -> str:
        """
        Verify that FFmpeg is installed and available on the system PATH.

        Returns the resolved path to the ffmpeg executable.
        Raises FFmpegNotFoundError with a user-friendly message if missing.
        """
        if self._ffmpeg_path:
            return self._ffmpeg_path

        path = shutil.which("ffmpeg")
        if path is None:
            raise FFmpegNotFoundError(
                "FFmpeg was not found.\n\n"
                "Please install FFmpeg and add it to your system PATH."
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
        """
        Extract the audio track from a video into a WAV file.

        Uses 16kHz mono PCM, which is the preferred input format for
        speech transcription models such as Whisper.
        """
        self.check_ffmpeg()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd: List[str] = [
            self._ffmpeg_path,
            "-y",                      # overwrite output without asking
            "-i", str(video_path),     # input video
            "-vn",                     # strip video stream
            "-acodec", "pcm_s16le",    # 16-bit PCM WAV
            "-ar", str(sample_rate),   # sample rate
            "-ac", str(channels),      # channel count
            str(output_path),
        ]

        logger.info(f"Extracting audio from '{video_path.name}' -> '{output_path.name}'")
        self._run_command(cmd)

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise FFmpegError("Audio extraction produced no output file.")

        logger.info(f"Audio extracted successfully: {output_path}")
        return output_path

    def _run_command(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """
        Execute an FFmpeg command safely.

        Captures stdout/stderr, checks the return code, and raises a
        descriptive FFmpegError on failure.
        """
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
            raise FFmpegNotFoundError(
                "FFmpeg executable disappeared during execution."
            ) from exc

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