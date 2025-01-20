# audio-samples-organizer

Converts samples to an audio format supported by the Alesis Strike Multipad and normalizes the files names. The implementation itself is very naive.

⚠️ IMPORTANT : These scripts changes files recursively. That said, make sure to back up your files before running them.

```python
from src import alesis

ROOT_DIR = r"C:\path\to\folder\that\contains\samples"

# Create a standard for your files names
alesis.normalize_audio_filenames(ROOT_DIR)

# Removes metadata associated to the files
alesis.remove_audio_files_metadata(ROOT_DIR)

# Converts audio files to a format supported by the Alesis Strike Multipad
alesis.convert_audio_files(ROOT_DIR)
```