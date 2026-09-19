import re
from typing import List
from src.models.transcript import Transcript, TranscriptSegment
from src.models.clip import HighlightCandidate
from src.config.settings import MIN_CLIP_DURATION, MAX_CLIP_DURATION
from src.utils.logger import get_logger

logger = get_logger(__name__)

class HighlightDetector:
    """
    Identifies potentially engaging moments in the transcript.
    Uses heuristic scoring based on text content, punctuation, pacing, 
    and visual scene changes.
    """

    # Simple heuristic keywords that often indicate high-engagement moments
    ENGAGEMENT_KEYWORDS = {
        "secret", "never", "always", "crazy", "insane", "huge", "mistake", 
        "best", "worst", "first", "last", "shocking", "truth", "lie", 
        "exactly", "literally", "actually", "wait", "look"
    }

    def __init__(self, min_duration: float = MIN_CLIP_DURATION, max_duration: float = MAX_CLIP_DURATION):
        self.min_duration = min_duration
        self.max_duration = max_duration

    def find_candidates(
        self, 
        transcript: Transcript, 
        scenes: List[tuple], 
        top_n: int = 5
    ) -> List[HighlightCandidate]:
        """
        Analyzes the transcript and scenes to find the top N highlight candidates.
        """
        if not transcript.segments:
            logger.warning("Transcript is empty. Cannot detect highlights.")
            return []

        logger.info(f"Analyzing {len(transcript.segments)} transcript segments for highlights...")
        
        candidates = []
        
        # We use a sliding window approach to group segments into clip-sized chunks
        for i in range(len(transcript.segments)):
            for j in range(i + 1, len(transcript.segments) + 1):
                chunk_segments = transcript.segments[i:j]
                if not chunk_segments:
                    continue
                
                start_time = chunk_segments[0].start
                end_time = chunk_segments[-1].end
                duration = end_time - start_time
                
                # Filter by duration constraints
                if duration < self.min_duration or duration > self.max_duration:
                    continue

                # Calculate score and reasons
                score, reasons = self._score_chunk(chunk_segments, scenes)
                
                text_snippet = " ".join([s.text for s in chunk_segments])
                
                candidates.append(HighlightCandidate(
                    start_time=start_time,
                    end_time=end_time,
                    score=score,
                    text_snippet=text_snippet,
                    reasons=reasons
                ))

        # Sort by score descending
        candidates.sort(key=lambda c: c.score, reverse=True)
        
        # Remove overlapping candidates (keep the highest scoring one)
        final_candidates = self._remove_overlaps(candidates)
        
        logger.info(f"Highlight detection complete. Selected top {len(final_candidates[:top_n])} candidates.")
        return final_candidates[:top_n]

    def _score_chunk(self, segments: List[TranscriptSegment], scenes: List[tuple]) -> tuple[float, List[str]]:
        """Calculates a heuristic score for a chunk of transcript segments."""
        score = 0.0
        reasons = []
        
        full_text = " ".join([s.text.lower() for s in segments])
        duration = segments[-1].end - segments[0].start
        
        # 1. Punctuation & Emotion (Questions, Exclamations)
        question_count = full_text.count("?")
        exclamation_count = full_text.count("!")
        
        if question_count > 0:
            score += question_count * 0.15
            reasons.append("Contains questions")
        if exclamation_count > 0:
            score += exclamation_count * 0.1
            reasons.append("High energy/exclamations")

        # 2. Keyword Density
        keyword_hits = sum(1 for word in self.ENGAGEMENT_KEYWORDS if word in full_text)
        if keyword_hits > 0:
            score += keyword_hits * 0.2
            reasons.append(f"Contains {keyword_hits} engagement keywords")

        # 3. Pacing (Words per minute)
        word_count = len(full_text.split())
        wpm = (word_count / duration) * 60 if duration > 0 else 0
        
        # Ideal speaking rate for shorts is often 130-160 WPM
        if 130 <= wpm <= 170:
            score += 0.3
            reasons.append("Ideal pacing")
        elif wpm > 170:
            score += 0.15
            reasons.append("Fast pacing")

        # 4. Scene Change Overlap
        start_t = segments[0].start
        end_t = segments[-1].end
        
        scene_changes_inside = sum(1 for s_start, s_end in scenes if start_t < s_end and end_t > s_start)
        if scene_changes_inside > 0:
            score += 0.25
            reasons.append("Visual scene changes detected")

        # 5. Duration Sweet Spot (Closer to 30-45s is often better for Shorts/Reels)
        if 30 <= duration <= 45:
            score += 0.2
            reasons.append("Optimal duration")

        # Normalize score to roughly 0.0 - 1.0 range (though it can technically exceed 1.0)
        return round(score, 2), reasons

    def _remove_overlaps(self, candidates: List[HighlightCandidate]) -> List[HighlightCandidate]:
        """Removes overlapping candidates, keeping the highest-scoring ones."""
        final = []
        for candidate in candidates:
            overlaps = False
            for selected in final:
                # Check if time ranges overlap
                if not (candidate.end_time <= selected.start_time or candidate.start_time >= selected.end_time):
                    overlaps = True
                    break
            
            if not overlaps:
                final.append(candidate)
                
        return final