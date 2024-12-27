from __future__ import annotations

import pathlib
from dataclasses import dataclass

from mutagen.wave import WAVE
from pydub import AudioSegment

from src import files

AUDIO_TARGET_FORMAT = "wav"
AUDIO_MAX_SAMPLE_RATE_HERTZ = 44100
AUDIO_MAX_SAMPLE_WIDTH_BYTES = 2  # 16-bit corresponds to 2 bytes


@dataclass(frozen=True)
class AudioScaling:
    """Audio Data"""

    audio: AudioSegment
    """Sound file info"""

    @property
    def target_sample_rate_hertz(self):
        """Desired sample rate"""
        return min(self.audio.frame_rate, AUDIO_MAX_SAMPLE_RATE_HERTZ)

    @property
    def target_sample_width_bytes(self):
        """Desired sample with"""
        return min(self.audio.sample_width, AUDIO_MAX_SAMPLE_WIDTH_BYTES)

    @property
    def needs_rescaling(self):
        """Returns True if audio needs to be converted to be supported in Alesis Strike Multipad. Otherwise, returns False"""
        return (
            self.target_sample_width_bytes != self.audio.sample_width
            or self.target_sample_rate_hertz != self.audio.frame_rate
        )

    def __str__(self):
        return f"{self.audio.sample_width * 8}-bit|{self.audio.frame_rate}Hz -> {self.target_sample_width_bytes * 8}-bit|{self.target_sample_rate_hertz}Hz"


class AlesisAudioConversionCmdGetter(files.FileCmdGetter):
    """
    The Alesis Strike Multipad natively supports 16-bit/44.1kHz samples.
        See https://support.alesis.com/en/support/solutions/articles/69000824218-alesis-strike-multipad-what-file-format-should-i-use-for-my-samples-
    """

    @dataclass(frozen=True)
    class CmdConvertAudioFile(files.Cmd):
        """Command to convert or rescale an audio file, if needed, to a format supported by the Alesis Strike Multipad"""

        file: pathlib.Path
        """Corresponding File"""

        audio_scaling: AudioScaling
        """Audio Data"""

        @property
        def operation_description(self) -> str:
            return f"Convert audio : {self.audio_scaling} ({self.file.name})"

        def execute(self):
            """Rewrites the audio file, applying the conversion"""
            audio = self.audio_scaling.audio
            audio = audio.set_frame_rate(self.audio_scaling.target_sample_rate_hertz)
            audio = audio.set_sample_width(self.audio_scaling.target_sample_width_bytes)
            audio.export(str(self.file), format=AUDIO_TARGET_FORMAT)

    def get_command(self, file: pathlib.Path):
        """
        Converts or rescale the audio file, if needed, to a format supported by the Alesis Strike Multipad
        """

        # Read the original audio file
        audio: AudioSegment = AudioSegment.from_wav(str(file))

        audio_scaling = AudioScaling(audio=audio)

        if audio_scaling.needs_rescaling:
            return AlesisAudioConversionCmdGetter.CmdConvertAudioFile(
                file=file, audio_scaling=audio_scaling
            )

        return None


class AudioMetadataDeleteCmdGetter(files.FileCmdGetter):

    @dataclass(frozen=True)
    class CmdDeleteAudioMetadata(files.Cmd):
        """Command to delete all the metadata of an audio file"""

        file: pathlib.Path
        """Corresponding File"""

        audio: WAVE
        """Audio Metadata"""

        @property
        def operation_description(self) -> str:
            return f"Delete metadata : {self.audio.items()} ({self.file.name})"

        def execute(self):
            """Rewrites the audio file, applying the conversion"""
            self.audio.delete()
            self.audio.tags.clear()
            self.audio.save()

    def get_command(self, file: pathlib.Path):
        audio = WAVE(str(file))

        if audio.items():
            return AudioMetadataDeleteCmdGetter.CmdDeleteAudioMetadata(file, audio)

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
        cmd_getter=AlesisAudioConversionCmdGetter(),
    )


def remove_audio_files_metadata(root_dir: str):
    """Removes all the metadata from files"""
    files.update_files(
        root_dir,
        predicate=_is_supported_audio_file,
        cmd_getter=AudioMetadataDeleteCmdGetter(),
    )


def _is_supported_audio_file(file: pathlib.Path):
    """Returns True if the file is considered to be a supported audio file"""
    return (
        file.is_file() and file.suffix.lower().strip().strip(".") == AUDIO_TARGET_FORMAT
    )
