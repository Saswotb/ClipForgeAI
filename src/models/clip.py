from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

@dataclass
class HighlightCandidate:
    """Represents a scored candidate segment identified as a potential highlight."""
    start_time: float
    end_time: float
    score: float
    text_snippet: str
    reasons: List[str] = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

@dataclass
class Clip:
    """Represents a final generated short clip."""
    source_video: Path
    start_time: float
    end_time: float
    duration: float
    score: float
    title: str = ""
    output_path: Optional[Path] = None
    subtitle_path: Optional[Path] = None
    thumbnail_path: Optional[Path] = None
    metadata_path: Optional[Path] = None