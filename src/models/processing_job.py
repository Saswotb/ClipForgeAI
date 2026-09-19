import uuid
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingJob:
    """Represents a single processing operation on a source video."""

    source_video: Path
    job_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    current_stage: str = ""
    progress: float = 0.0
    status: JobStatus = JobStatus.PENDING
    error_message: str = ""
    generated_clips: List[Path] = field(default_factory=list)

    def mark_running(self, stage: str) -> None:
        self.status = JobStatus.RUNNING
        self.current_stage = stage

    def mark_completed(self) -> None:
        self.status = JobStatus.COMPLETED
        self.progress = 1.0

    def mark_failed(self, message: str) -> None:
        self.status = JobStatus.FAILED
        self.error_message = message

    def mark_cancelled(self) -> None:
        self.status = JobStatus.CANCELLED