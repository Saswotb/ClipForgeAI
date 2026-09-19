import json
from pathlib import Path
from typing import List

from src.config.paths import OUTPUT_METADATA_DIR
from src.models.clip import Clip
from src.models.transcript import Transcript, TranscriptSegment
from src.utils.logger import get_logger

logger = get_logger(__name__)

class MetadataGenerator:
    """
    Generates titles, descriptions, and hashtags for the clips based on the transcript.
    """

    def generate_metadata(self, clips: List[Clip], transcript: Transcript) -> List[Clip]:
        OUTPUT_METADATA_DIR.mkdir(parents=True, exist_ok=True)
        
        for clip in clips:
            try:
                # Get the full text for this specific clip
                clip_text = self._get_clip_text(transcript.segments, clip.start_time, clip.end_time)
                
                # Generate heuristic metadata
                title = self._generate_title(clip_text)
                description = self._generate_description(clip_text)
                hashtags = self._generate_hashtags()
                
                metadata = {
                    "title": title,
                    "description": description,
                    "hashtags": hashtags,
                    "source_start": clip.start_time,
                    "source_end": clip.end_time
                }
                
                meta_path = OUTPUT_METADATA_DIR / f"{clip.output_path.stem}.json"
                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=4, ensure_ascii=False)
                    
                clip.metadata_path = meta_path
                logger.info(f"Generated metadata: {meta_path.name}")
                
            except Exception as e:
                logger.error(f"Failed to generate metadata for {clip.title}: {e}")
                
        return clips

    def _get_clip_text(self, segments: List[TranscriptSegment], start: float, end: float) -> str:
        text = []
        for seg in segments:
            if seg.end > start and seg.start < end:
                text.append(seg.text.strip())
        return " ".join(text)

    def _generate_title(self, text: str) -> str:
        # Simple heuristic: take the first sentence, capped at 80 characters
        sentences = text.split('.')
        title = sentences[0].strip() if sentences else text[:60].strip()
        return title[:80] + "..." if len(title) > 80 else title

    def _generate_description(self, text: str) -> str:
        return text[:200] + "..." if len(text) > 200 else text

    def _generate_hashtags(self) -> List[str]:
        # In the future, this could analyze the text for keywords
        return ["#shorts", "#viral", "#fyp", "#clipforge"]