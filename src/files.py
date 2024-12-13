import os
import pathlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable


class Cmd(ABC):
    """Command"""

    @property
    @abstractmethod
    def operation_description(self) -> str:
        """User-level description of the operation performed by this command execution"""

    @abstractmethod
    def execute(self) -> None:
        """Executes the command"""


class FileCmdGetter(ABC):
    """Perform actions on files"""

    @abstractmethod
    def get_command(self, file: pathlib.Path) -> Cmd | None:
        """Returns a command to be executed against this file. Returns None if there is no operation to be performed"""


class RenameFileCmdGetter(FileCmdGetter):
    """Formats file names"""

    @dataclass(frozen=True)
    class CmdRenameFile(Cmd):
        """Command to rename a file"""

        file: pathlib.Path
        """Corresponding File"""

        file_new: pathlib.Path
        """New name"""

        @property
        def operation_description(self) -> str:
            return f"Rename '{self.file}' -> '{self.file_new.name}'"

        def execute(self):
            """Applies the rename"""
            os.rename(str(self.file), str(self.file_new))

    def __init__(self, chain: list[Callable[[str], str]]) -> None:
        self._chain = chain

    def get_command(self, file: pathlib.Path) -> CmdRenameFile | None:
        file_new = file.with_name(file.name)
        for fn in self._chain:
            file_new = file.with_name(fn(file_new))

        if file_new.name != file.name:
            return RenameFileCmdGetter.CmdRenameFile(file=file, file_new=file_new)
        return None


class TitleCaseSanitizerFormatter:
    """Sanitizes and normalizes the file name"""

    def __call__(self, file: pathlib.Path) -> str:
        """Converts to Title Case and replaces special characters with white spaces"""
        stem = re.sub("[^0-9a-zA-Z]+", " ", file.stem).strip().title()
        suffix = file.suffix.lower().strip() if file.suffix else ""
        return stem + suffix


class RegexReplaceFileNameFormatter:
    """Renames the file that matches regex patterns"""

    def __init__(self, patterns: dict[re.Pattern, str]) -> None:
        self._patterns = patterns

    def __call__(self, file: pathlib.Path) -> str:
        stem_new = next(
            (
                pattern.sub(stem_re, file.name)
                for pattern, stem_re in self._patterns.items()
                if pattern.search(file.name)
            ),
            None,
        )

        counter = 0

        def bump_file_name():
            nonlocal counter
            counter += 1
            stem = stem_new.format(count=counter)
            suffix = file.suffix.lower().strip() if file.suffix else ""
            name = stem if stem.endswith(suffix) else (stem + suffix)
            return file.with_name(name)

        file_new: pathlib.Path | None = None
        if stem_new:
            file_new = bump_file_name()
            while file_new.exists():
                file_new = bump_file_name()

        return (file_new or file).name


def update_files(
    root_dir: str, predicate: Callable[[pathlib.Path], bool], cmd_getter: FileCmdGetter
):
    """Iterates files recursively and apply the handler"""
    commands: list[Cmd] = []

    for root, _, files in os.walk(root_dir):
        for file_path in files:
            file = pathlib.Path(os.path.join(root, file_path))
            if predicate(file):
                cmd = cmd_getter.get_command(file)
                if cmd:
                    commands.append(cmd)

    if commands:
        print("The following operations will be performed : ")

        for cmd in commands:
            print(cmd.operation_description)

        answer = input(
            "The operation is not reversible. Do you wish to continue ? (y/N): "
        )

        if answer.lower().strip() == "y":
            for cmd in commands:
                cmd.execute()
                print(f"DONE : {cmd.operation_description}")

            print(f"{len(commands)} operations was performed with success.")

        else:
            print("The operation was aborted")
    else:
        print("There is no operation to be performed")
