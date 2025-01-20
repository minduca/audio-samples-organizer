# audio-samples-organizer

Converts samples to a different audio format. This repository is unofficial and has neither affiliation nor support from any manufacturer whatsoever.

⚠️ IMPORTANT : These scripts changes files recursively. That said, make sure to back up your files before running them. In addition, the implementation itself is very naive. That said, please be cautious.


```python
from src import audio

ROOT_DIR = r"C:\path\to\folder\that\contains\samples"

# Converts audio files to a format supported by the Alesis Strike Multipad
target_output = audio.ALESIS_STRIKE_MULTIPAD_TARGET_OUTPUT

# Create a standard for your files names (TODO provide examples)
audio.normalize_audio_filenames(ROOT_DIR, target_output.format)

# Removes metadata associated to the files
audio.remove_audio_files_metadata(ROOT_DIR, target_output.format)

# Converts the audio files to the specified format
audio.convert_audio_files(ROOT_DIR, target_output)
```