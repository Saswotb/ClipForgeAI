import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from queue import Queue
from typing import Optional

from src.config.paths import TEMP_AUDIO_DIR
from src.config.settings import WHISPER_MODEL
from src.models.processing_job import ProcessingJob, JobStatus
from src.services.ffmpeg_service import (
    FFmpegService,
    FFmpegNotFoundError,
    FFmpegError,
)
from src.core.transcriber import Transcriber
from src.utils.logger import get_logger
from src.utils.validators import validate_video_file, validate_output_directory

logger = get_logger(__name__)

class EngineStage(Enum):
    """All processing stages. Milestone 4 implements up to Transcribing."""
    VALIDATING = "Validating"
    EXTRACTING_AUDIO = "Extracting audio"
    TRANSCRIBING = "Transcribing"
    DETECTING_SCENES = "Detecting scenes"
    DETECTING_HIGHLIGHTS = "Finding highlights"
    GENERATING_CLIPS = "Generating clips"
    CONVERTING_VERTICAL = "Converting to vertical"
    GENERATING_SUBTITLES = "Generating subtitles"
    GENERATING_THUMBNAILS = "Generating thumbnails"
    GENERATING_METADATA = "Generating metadata"
    COMPLETED = "Completed"

@dataclass
class ProgressEvent:
    """A thread-safe message passed from the engine to the GUI."""
    stage: str
    progress: float
    message: str = ""
    error: Optional[str] = None
    is_finished: bool = False

class ProcessingEngine:
    """
    Central processing coordinator.
    Runs all long-running work on a background thread.
    """

    def __init__(self, event_queue: Queue) -> None:
        self.event_queue = event_queue
        self.ffmpeg = FFmpegService()
        self._cancel_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.current_job: Optional[ProcessingJob] = None

    # -- Public control API ------------------------------------------------

    def start(self, video_path: Path) -> None:
        if self.is_running():
            logger.warning("Engine is already running. Ignoring start request.")
            return

        self._cancel_event.clear()
        self.current_job = ProcessingJob(source_video=video_path)
        self._thread = threading.Thread(
            target=self._process, args=(video_path,), daemon=True
        )
        self._thread.start()
        logger.info(f"Engine started for job {self.current_job.job_id}")

    def cancel(self) -> None:
        logger.info("Cancellation requested.")
        self._cancel_event.set()

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # -- Internal helpers --------------------------------------------------

    def _emit(
        self,
        stage: str,
        progress: float,
        message: str = "",
        error: Optional[str] = None,
        finished: bool = False,
    ) -> None:
        self.event_queue.put(
            ProgressEvent(
                stage=stage,
                progress=progress,
                message=message,
                error=error,
                is_finished=finished,
            )
        )

    def _cancelled(self) -> bool:
        return self._cancel_event.is_set()

    # -- Main pipeline -----------------------------------------------------

    def _process(self, video_path: Path) -> None:
        job = self.current_job

        try:
            # --- Stage 1: Validation (0% - 10%) ---
            job.mark_running(EngineStage.VALIDATING.value)
            self._emit(EngineStage.VALIDATING.value, 0.05, "Validating video...")
            validate_video_file(video_path)
            validate_output_directory(TEMP_AUDIO_DIR)
            self.ffmpeg.check_ffmpeg()

            if self._cancelled():
                job.mark_cancelled()
                self._emit(EngineStage.VALIDATING.value, 0.0, "Cancelled.",
                           error="Cancelled by user.", finished=True)
                return

            # --- Stage 2: Audio Extraction (10% - 30%) ---
            job.mark_running(EngineStage.EXTRACTING_AUDIO.value)
            self._emit(EngineStage.EXTRACTING_AUDIO.value, 0.15, "Extracting audio...")

            audio_path = TEMP_AUDIO_DIR / f"{job.job_id}_{video_path.stem}.wav"
            self.ffmpeg.extract_audio(video_path, audio_path)

            if self._cancelled():
                job.mark_cancelled()
                self._emit(EngineStage.EXTRACTING_AUDIO.value, 0.0, "Cancelled.",
                           error="Cancelled by user.", finished=True)
                return

            # --- Stage 3: Transcription (30% - 80%) ---
            job.mark_running(EngineStage.TRANSCRIBING.value)
            self._emit(EngineStage.TRANSCRIBING.value, 0.35, "Loading AI model...")
            
            transcriber = Transcriber(model_name=WHISPER_MODEL)
            
            self._emit(EngineStage.TRANSCRIBING.value, 0.45, "Transcribing audio...")
            transcript = transcriber.transcribe(audio_path, job.job_id)

            if self._cancelled():
                job.mark_cancelled()
                self._emit(EngineStage.TRANSCRIBING.value, 0.0, "Cancelled.",
                           error="Cancelled by user.", finished=True)
                return

            # --- Milestone 4 Complete ---
            job.mark_completed()
            self._emit(
                EngineStage.COMPLETED.value,
                1.0,
                f"Transcription complete ({len(transcript.segments)} segments).",
                finished=True,
            )
            logger.info(f"Job {job.job_id} completed Milestone 4 pipeline.")

        except FFmpegNotFoundError as exc:
            job.mark_failed(str(exc))
            logger.error(f"FFmpeg not found: {exc}")
            self._emit(EngineStage.VALIDATING.value, 0.0, "FFmpeg not found.",
                       error=str(exc), finished=True)

        except ValueError as exc:
            job.mark_failed(str(exc))
            logger.error(f"Validation failed: {exc}")
            self._emit(EngineStage.VALIDATING.value, 0.0, "Validation failed.",
                       error=str(exc), finished=True)

        except FFmpegError as exc:
            job.mark_failed(str(exc))
            logger.error(f"FFmpeg error: {exc}")
            self._emit(EngineStage.EXTRACTING_AUDIO.value, 0.0, "FFmpeg error.",
                       error=str(exc), finished=True)
                       
        except Exception as exc:  # noqa: BLE001
            job.mark_failed(str(exc))
            logger.error(f"Unexpected engine error: {exc}", exc_info=True)
            self._emit(EngineStage.VALIDATING.value, 0.0, "Unexpected error.",
                       error=str(exc), finished=True)