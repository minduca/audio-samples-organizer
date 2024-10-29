# audio-samples-organizer

Converts samples to an audio format supported by the Alesis Strike Multipad and organizes the files names.

⚠️ IMPORTANT : These scripts changes files recursively. Make sure to back up your files before running these scripts.

```python
from src import alesis

ROOT_DIR = r"C:\path\to\folder\that\contains\samples"

# Create a standard for your files names
alesis.normalize_audio_filenames(ROOT_DIR)

# Converts audio files to a format supported by the Alesis Strike Multipad
alesis.convert_audio_files(ROOT_DIR)
```