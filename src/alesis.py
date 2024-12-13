from __future__ import annotations

import pathlib
from dataclasses import dataclass
from typing import Any

import soundfile
from numpy import dtype, float64, ndarray

from src import files

AUDIO_SUFFIXES = {".wav"}
AUDIO_TARGET_SUBTYPE = "PCM_24"
AUDIO_SUPPORTED_SUBTYPES = {"PCM_S8", "PCM_U8", "PCM_16", AUDIO_TARGET_SUBTYPE}
AUDIO_MAX_SAMPLE_RATE = 48000


@dataclass(frozen=True)
class AudioData:
    """Audio Data"""

    info: soundfile._SoundFileInfo
    """Sound file info"""

    data: ndarray[Any, dtype[float64]] | Any
    """Binary"""

    current_samplerate: int
    """Current sample rate"""

    @property
    def target_samplerate(self):
        """Desired sample rate"""
        return min(self.current_samplerate, AUDIO_MAX_SAMPLE_RATE)

    @property
    def needs_rescaling(self):
        """Returns True if audio needs to be converted to be supported in Alesis Strike Multipad. Otherwise, returns False"""
        return (
            self.info.subtype not in AUDIO_SUPPORTED_SUBTYPES
            or self.target_samplerate != self.current_samplerate
        )


class AlesisAudioConversionHandler(files.FileCmdGetter):
    """
    The Alesis Strike Multipad natively supports 16-bit/44.1kHz samples.
        See https://support.alesis.com/en/support/solutions/articles/69000824218-alesis-strike-multipad-what-file-format-should-i-use-for-my-samples-
    """

    @dataclass(frozen=True)
    class CmdConvertAudioFile(files.Cmd):
        """Command to convert or rescale an audio file, if needed, to a format supported by the Alesis Strike Multipad"""

        file: pathlib.Path
        """Corresponding File"""

        audio_data: AudioData
        """Audio Data"""

        @property
        def operation_description(self) -> str:
            return f"Convert audio : {self.audio_data.info.subtype}|{self.audio_data.current_samplerate} -> {AUDIO_TARGET_SUBTYPE}|{self.audio_data.target_samplerate} ({self.file.name})"

        def execute(self):
            """Rewrites the audio file, applying the conversion"""
            soundfile.write(
                str(self.file),
                self.audio_data.data,
                self.audio_data.target_samplerate,
                subtype=AUDIO_TARGET_SUBTYPE,
            )

    def get_command(self, file: pathlib.Path):
        """
        Converts or rescale the audio file, if needed, to a format supported by the Alesis Strike Multipad
        """

        # Read the original audio file
        data, current_samplerate = soundfile.read(str(file))

        audio_data = AudioData(
            info=soundfile.info(str(file)),
            data=data,
            current_samplerate=current_samplerate,
        )

        if audio_data.needs_rescaling:
            return AlesisAudioConversionHandler.CmdConvertAudioFile(
                file=file, audio_data=audio_data
            )

        return None


def normalize_audio_filenames(root_dir: str, formatter: files.RenameFileCmdGetter):
    """Normalizes audio files names"""
    files.update_files(
        root_dir,
        predicate=_is_supported_audio_file,
        cmd_getter=formatter,
    )


def convert_audio_files(root_dir: str):
    """Converts audio files to a format supported by the Alesis Strike Multipad"""
    files.update_files(
        root_dir,
        predicate=_is_supported_audio_file,
        cmd_getter=AlesisAudioConversionHandler(),
    )


def _is_supported_audio_file(file: pathlib.Path):
    """Returns True if the file is considered to be a supported audio file"""
    return file.is_file() and file.suffix.lower().strip() in AUDIO_SUFFIXES
