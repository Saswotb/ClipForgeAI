from dataclasses import dataclass, field
from typing import List

@dataclass
class TranscriptSegment:
    """Represents a single timestamped segment of transcribed text."""
    start: float      # Start time in seconds
    end: float        # End time in seconds
    text: str         # The transcribed text
    confidence: float = 0.0  # Optional confidence score

@dataclass
class Transcript:
    """Represents the complete transcription of an audio/video file."""
    full_text: str
    segments: List[TranscriptSegment] = field(default_factory=list)
    language: str = "en"