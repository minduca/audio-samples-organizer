import os
import pathlib
import re
from abc import ABC, abstractmethod
from typing import Callable


class FileHandler(ABC):
    """Perform actions on files"""

    @abstractmethod
    def handle(self, file: pathlib.Path) -> bool:
        """Returns True if any change was applies to the file. Otherwise, returns False"""

    @abstractmethod
    def close(self, count_files_changed: int) -> None:
        """Function called at the end of the processing"""


class TitleCaseFileFormatter(FileHandler):
    """Sanitizes and normalizes the file name"""

    def handle(self, file: pathlib.Path) -> bool:
        file_new = file.with_name(self._normalise_filename(file))

        if file_new.name != file.name:
            print(f"{file.name} -> {file_new.name}")
            os.rename(str(file), str(file_new))
            return True
        return False

    def close(self, count_files_changed: int):
        print(f"{count_files_changed} files renamed")

    def _normalise_filename(self, file: pathlib.Path):
        """Sanitizes and normalizes the file name"""
        stem = re.sub("[^0-9a-zA-Z]+", " ", file.stem).strip().title()
        suffix = file.suffix.lower().strip() if file.suffix else ""
        return stem + suffix


def update_files(
    root_dir: str, predicate: Callable[[pathlib.Path], bool], handler: FileHandler
):
    """Iterates files recursively and apply the handler"""
    count_files_changed = 0

    for root, _, files in os.walk(root_dir):
        for file_path in files:
            file = pathlib.Path(os.path.join(root, file_path))
            if predicate(file) and handler.handle(file):
                count_files_changed += 1

    handler.close(count_files_changed)
