import threading
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from queue import Queue
from typing import Optional, List

from src.config.paths import TEMP_AUDIO_DIR
from src.config.settings import WHISPER_MODEL, MIN_CLIP_DURATION, MAX_CLIP_DURATION
from src.models.clip import Clip
from src.models.processing_job import ProcessingJob, JobStatus
from src.services.ffmpeg_service import (
    FFmpegService,
    FFmpegNotFoundError,
    FFmpegError,
)
from src.core.transcriber import Transcriber
from src.core.scene_detector import SceneDetector
from src.core.highlight_detector import HighlightDetector
from src.core.clip_generator import ClipGenerator
from src.core.vertical_converter import VerticalConverter
from src.utils.logger import get_logger
from src.utils.validators import validate_video_file, validate_output_directory

logger = get_logger(__name__)

class EngineStage(Enum):
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
    stage: str
    progress: float
    message: str = ""
    error: Optional[str] = None
    is_finished: bool = False

class ProcessingEngine:
    def __init__(self, event_queue: Queue) -> None:
        self.event_queue = event_queue
        self.ffmpeg = FFmpegService()
        self._cancel_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self.current_job: Optional[ProcessingJob] = None

    def start(self, video_path: Path) -> None:
        if self.is_running():
            logger.warning("Engine is already running.")
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

    def _emit(
        self, stage: str, progress: float, message: str = "", 
        error: Optional[str] = None, finished: bool = False
    ) -> None:
        self.event_queue.put(
            ProgressEvent(stage=stage, progress=progress, message=message, 
                          error=error, is_finished=finished)
        )

    def _cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def _process(self, video_path: Path) -> None:
        job = self.current_job

        try:
            # --- Stage 1: Validation (0% - 5%) ---
            job.mark_running(EngineStage.VALIDATING.value)
            self._emit(EngineStage.VALIDATING.value, 0.02, "Validating video...")
            validate_video_file(video_path)
            validate_output_directory(TEMP_AUDIO_DIR)
            self.ffmpeg.check_ffmpeg()

            if self._cancelled(): return self._handle_cancel(EngineStage.VALIDATING.value)

            # --- Stage 2: Audio Extraction (5% - 15%) ---
            job.mark_running(EngineStage.EXTRACTING_AUDIO.value)
            self._emit(EngineStage.EXTRACTING_AUDIO.value, 0.08, "Extracting audio...")
            audio_path = TEMP_AUDIO_DIR / f"{job.job_id}_{video_path.stem}.wav"
            self.ffmpeg.extract_audio(video_path, audio_path)

            if self._cancelled(): return self._handle_cancel(EngineStage.EXTRACTING_AUDIO.value)

            # --- Stage 3: Transcription (15% - 45%) ---
            job.mark_running(EngineStage.TRANSCRIBING.value)
            self._emit(EngineStage.TRANSCRIBING.value, 0.20, "Loading AI model...")
            transcriber = Transcriber(model_name=WHISPER_MODEL)
            
            self._emit(EngineStage.TRANSCRIBING.value, 0.25, "Transcribing audio...")
            transcript = transcriber.transcribe(audio_path, job.job_id)

            if self._cancelled(): return self._handle_cancel(EngineStage.TRANSCRIBING.value)

            # --- Stage 4: Scene Detection (45% - 55%) ---
            job.mark_running(EngineStage.DETECTING_SCENES.value)
            self._emit(EngineStage.DETECTING_SCENES.value, 0.48, "Analyzing visual scenes...")
            scene_detector = SceneDetector()
            scenes = scene_detector.detect_scenes(video_path)

            if self._cancelled(): return self._handle_cancel(EngineStage.DETECTING_SCENES.value)

            # --- Stage 5: Highlight Detection (55% - 65%) ---
            job.mark_running(EngineStage.DETECTING_HIGHLIGHTS.value)
            self._emit(EngineStage.DETECTING_HIGHLIGHTS.value, 0.58, "Finding highlight candidates...")
            highlight_detector = HighlightDetector(min_duration=MIN_CLIP_DURATION, max_duration=MAX_CLIP_DURATION)
            candidates = highlight_detector.find_candidates(transcript, scenes, top_n=5)

            if self._cancelled(): return self._handle_cancel(EngineStage.DETECTING_HIGHLIGHTS.value)

            # --- Stage 6: Clip Generation (65% - 85%) ---
            job.mark_running(EngineStage.GENERATING_CLIPS.value)
            self._emit(EngineStage.GENERATING_CLIPS.value, 0.68, "Generating video clips...")
            clip_generator = ClipGenerator(self.ffmpeg)
            generated_clips: List[Clip] = clip_generator.generate_clips(video_path, candidates, job.job_id)
            job.generated_clips = generated_clips

            if self._cancelled(): return self._handle_cancel(EngineStage.GENERATING_CLIPS.value)

            # --- Stage 7: Vertical Conversion (85% - 95%) ---
            job.mark_running(EngineStage.CONVERTING_VERTICAL.value)
            self._emit(EngineStage.CONVERTING_VERTICAL.value, 0.88, "Converting to 9:16 vertical...")
            vertical_converter = VerticalConverter(self.ffmpeg)
            final_clips = vertical_converter.convert_clips(generated_clips)
            job.generated_clips = final_clips # Update with vertical paths

            if self._cancelled(): return self._handle_cancel(EngineStage.CONVERTING_VERTICAL.value)

            # --- Milestone 6 Complete ---
            job.mark_completed()
            self._emit(
                EngineStage.COMPLETED.value, 1.0, 
                f"Successfully generated {len(final_clips)} vertical clips!", 
                finished=True
            )
            logger.info(f"Job {job.job_id} completed Milestone 6 pipeline.")

        except FFmpegNotFoundError as exc:
            self._handle_error(EngineStage.VALIDATING.value, exc)
        except ValueError as exc:
            self._handle_error(EngineStage.VALIDATING.value, exc)
        except FFmpegError as exc:
            self._handle_error(EngineStage.GENERATING_CLIPS.value, exc)
        except Exception as exc:
            self._handle_error(EngineStage.VALIDATING.value, exc, is_unexpected=True)

    def _handle_cancel(self, stage: str):
        if self.current_job:
            self.current_job.mark_cancelled()
        self._emit(stage, 0.0, "Cancelled.", error="Cancelled by user.", finished=True)

    def _handle_error(self, stage: str, exc: Exception, is_unexpected: bool = False):
        if self.current_job:
            self.current_job.mark_failed(str(exc))
        
        if is_unexpected:
            logger.error(f"Unexpected engine error: {exc}", exc_info=True)
        else:
            logger.error(f"Engine error at {stage}: {exc}")
            
        self._emit(stage, 0.0, "Processing failed.", error=str(exc), finished=True)