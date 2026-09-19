import json
from pathlib import Path
import whisper  # type: ignore

from src.models.transcript import Transcript, TranscriptSegment
from src.config.paths import TEMP_TRANSCRIPT_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)

class Transcriber:
    """
    Core module for transcribing audio using OpenAI Whisper.
    Designed to be replaceable in the future if a different 
    transcription backend is required.
    """

    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self._model = None

    def _load_model(self) -> None:
        """Lazy-loads the Whisper model into memory."""
        if self._model is None:
            logger.info(f"Loading Whisper model: '{self.model_name}'...")
            # fp16=False ensures it runs on CPU if CUDA is not available
            self._model = whisper.load_model(self.model_name, device="cpu") 
            logger.info("Whisper model loaded successfully.")

    def transcribe(self, audio_path: Path, job_id: str) -> Transcript:
        """
        Transcribes the given audio file and returns a structured Transcript.
        Also saves the raw transcript data to the temp directory.
        """
        self._load_model()
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"Starting transcription for '{audio_path.name}'...")
        
        # Run transcription
        result = self._model.transcribe(str(audio_path), fp16=False)

        full_text = result.get("text", "").strip()
        language = result.get("language", "en")

        segments = []
        for seg in result.get("segments", []):
            segments.append(TranscriptSegment(
                start=seg["start"],
                end=seg["end"],
                text=seg["text"].strip(),
                # Whisper provides 'avg_logprob', we can map it or leave default
            ))

        transcript = Transcript(
            full_text=full_text,
            segments=segments,
            language=language
        )

        # Save to temp directory for debugging/inspection
        self._save_transcript(transcript, job_id)
        
        logger.info(f"Transcription complete. {len(segments)} segments extracted.")
        return transcript

    def _save_transcript(self, transcript: Transcript, job_id: str) -> None:
        """Saves the transcript to a JSON file in the temp directory."""
        TEMP_TRANSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = TEMP_TRANSCRIPT_DIR / f"{job_id}_transcript.json"

        data = {
            "full_text": transcript.full_text,
            "language": transcript.language,
            "segments": [
                {
                    "start": s.start, 
                    "end": s.end, 
                    "text": s.text, 
                    "confidence": s.confidence
                }
                for s in transcript.segments
            ]
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Transcript saved to: {output_path}")