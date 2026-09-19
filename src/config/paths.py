from pathlib import Path

# Base directory is the root of the project (where app.py is)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Asset directories
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
FONTS_DIR = ASSETS_DIR / "fonts"

# Data directories
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "output"
TEMP_DIR = DATA_DIR / "temp"
LOGS_DIR = DATA_DIR / "logs"
MODELS_DIR = BASE_DIR / "models"

# Output subdirectories
OUTPUT_CLIPS_DIR = OUTPUT_DIR / "clips"
OUTPUT_THUMBNAILS_DIR = OUTPUT_DIR / "thumbnails"
OUTPUT_SUBTITLES_DIR = OUTPUT_DIR / "subtitles"
OUTPUT_METADATA_DIR = OUTPUT_DIR / "metadata"
OUTPUT_PREVIEWS_DIR = OUTPUT_DIR / "previews"

# Temp subdirectories
TEMP_AUDIO_DIR = TEMP_DIR / "audio"
TEMP_FRAMES_DIR = TEMP_DIR / "frames"
TEMP_TRANSCRIPT_DIR = TEMP_DIR / "transcript"
TEMP_SCENES_DIR = TEMP_DIR / "scenes"
TEMP_CLIPS_DIR = TEMP_DIR / "clips"
TEMP_CACHE_DIR = TEMP_DIR / "cache"

# Ensure all required directories exist at runtime
_ALL_DIRECTORIES = [
    INPUT_DIR, OUTPUT_DIR, TEMP_DIR, LOGS_DIR, MODELS_DIR,
    OUTPUT_CLIPS_DIR, OUTPUT_THUMBNAILS_DIR, OUTPUT_SUBTITLES_DIR,
    OUTPUT_METADATA_DIR, OUTPUT_PREVIEWS_DIR,
    TEMP_AUDIO_DIR, TEMP_FRAMES_DIR, TEMP_TRANSCRIPT_DIR,
    TEMP_SCENES_DIR, TEMP_CLIPS_DIR, TEMP_CACHE_DIR,
]

for directory in _ALL_DIRECTORIES:
    directory.mkdir(parents=True, exist_ok=True)