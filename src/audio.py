from __future__ import annotations

import pathlib
from dataclasses import dataclass

from mutagen.wave import WAVE
from pydub import AudioSegment

from src import files


@dataclass(frozen=True)
class AudioTargetOutput:
    """Audio convertion target output"""

    format: str
    """Audio format"""
    max_sample_rate_hertz: int
    """Max sample rate"""
    max_sample_width_bytes: int
    """Max sample width"""


ALESIS_STRIKE_MULTIPAD_TARGET_OUTPUT = AudioTargetOutput(
    format="wav",
    max_sample_rate_hertz=44100,
    max_sample_width_bytes=2,  # 16-bit corresponds to 2 bytes
)
"""
Alesis Strike Multipad Supported File Type: 16-bit, mono or stereo .WAV files, 44.1 KHz Sample Rate.
    Source : https://cdn.inmusicbrands.com/alesis/StrikeMultipad/StrikeMultiPad-UserGuide-v1.2.pdf
"""


@dataclass(frozen=True)
class AudioScaling:
    """Audio Data"""

    audio: AudioSegment
    """Sound file info"""

    target_output: AudioTargetOutput
    """Audio convertion target output"""

    @property
    def target_sample_rate_hertz(self):
        """Desired sample rate"""
        return min(self.audio.frame_rate, self.target_output.max_sample_rate_hertz)

    @property
    def target_sample_width_bytes(self):
        """Desired sample with"""
        return min(self.audio.sample_width, self.target_output.max_sample_width_bytes)

    @property
    def needs_rescaling(self):
        """Returns True if audio needs to be converted. Otherwise, returns False"""
        return (
            self.target_sample_width_bytes != self.audio.sample_width
            or self.target_sample_rate_hertz != self.audio.frame_rate
        )

    def __str__(self):
        return f"{self.audio.sample_width * 8}-bit|{self.audio.frame_rate}Hz -> {self.target_sample_width_bytes * 8}-bit|{self.target_sample_rate_hertz}Hz"


class AudioConversionCmdGetter(files.FileCmdGetter):

    def __init__(self, target_output: AudioTargetOutput):
        super().__init__()
        self._target_output = target_output

    @dataclass(frozen=True)
    class CmdConvertAudioFile(files.Cmd):
        """Command to convert or rescale an audio file."""

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
            audio.export(str(self.file), format=self.audio_scaling.target_output.format)

    def get_command(self, file: pathlib.Path):
        """
        Converts or rescale the audio file, if needed.
        """

        # Read the original audio file
        audio: AudioSegment = AudioSegment.from_wav(str(file))

        audio_scaling = AudioScaling(audio=audio, target_output=self._target_output)

        if audio_scaling.needs_rescaling:
            return AudioConversionCmdGetter.CmdConvertAudioFile(
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

        if not files.file_has_format(file, "wav"):
            raise NotImplementedError("Only 'wav' files are supported at the moment.")

        audio = WAVE(str(file))

        if audio.items():
            return AudioMetadataDeleteCmdGetter.CmdDeleteAudioMetadata(file, audio)

        return None


def normalize_audio_filenames(
    root_dir: str, formatter: files.RenameFileCmdGetter, file_format: str
):
    """Normalizes audio files names"""
    print("File name normalization")
    files.update_files(
        root_dir,
        predicate=lambda file: files.file_has_format(file, file_format),
        cmd_getter=formatter,
    )


def convert_audio_files(root_dir: str, target_output: AudioTargetOutput):
    """Converts audio files to a different format"""

    print("Audio file conversion")
    files.update_files(
        root_dir,
        predicate=lambda file: files.file_has_format(file, target_output.format),
        cmd_getter=AudioConversionCmdGetter(target_output),
    )


def remove_audio_files_metadata(root_dir: str, file_format: str):
    """Removes all the metadata from files"""
    print("Audio file metadata suppression")
    files.update_files(
        root_dir,
        predicate=lambda file: files.file_has_format(file, file_format),
        cmd_getter=AudioMetadataDeleteCmdGetter(),
    )
