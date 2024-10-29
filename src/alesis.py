import pathlib

import soundfile

from src import files

AUDIO_SUFFIXES = {".wav"}
AUDIO_TARGET_SUBTYPE = "PCM_24"
AUDIO_SUPPORTED_SUBTYPES = {"PCM_S8", "PCM_U8", "PCM_16", AUDIO_TARGET_SUBTYPE}
AUDIO_MAX_SAMPLE_RATE = 48000


class AlesisAudioConversionHandler(files.FileHandler):
    """
    The Alesis Strike Multipad natively supports 16-bit/44.1kHz samples.
        See https://support.alesis.com/en/support/solutions/articles/69000824218-alesis-strike-multipad-what-file-format-should-i-use-for-my-samples-
    """

    def handle(self, file: pathlib.Path):
        """
        Converts or rescale the audio file, if needed, to a format supported by the Alesis Strike Multipad
        """

        info = soundfile.info(str(file))

        # Read the original audio file
        data, samplerate = soundfile.read(str(file))

        target_samplerate = min(samplerate, AUDIO_MAX_SAMPLE_RATE)

        audio_needs_rescaling = (
            info.subtype not in AUDIO_SUPPORTED_SUBTYPES
            or target_samplerate != samplerate
        )

        if audio_needs_rescaling:
            # Rewrite the audio file
            print(
                f"{info.subtype}|{samplerate} -> {AUDIO_TARGET_SUBTYPE}|{target_samplerate} ({file.name})"
            )
            soundfile.write(
                str(file), data, target_samplerate, subtype=AUDIO_TARGET_SUBTYPE
            )
            return True
        return False

    def close(self, count_files_changed: int) -> None:
        """Function called at the end of the processing"""


def normalize_audio_filenames(root_dir: str):
    """Normalizes audio files names"""
    files.update_files(
        root_dir,
        predicate=_is_supported_audio_file,
        handler=files.TitleCaseFileFormatter(),
    )


def convert_audio_files(root_dir: str):
    """Converts audio files to a format supported by the Alesis Strike Multipad"""
    files.update_files(
        root_dir,
        predicate=_is_supported_audio_file,
        handler=AlesisAudioConversionHandler(),
    )


def _is_supported_audio_file(file: pathlib.Path):
    """Returns True if the file is considered to be a supported audio file"""
    return file.is_file() and file.suffix.lower().strip() in AUDIO_SUFFIXES
