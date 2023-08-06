#!/usr/bin/env python3

"""Load files."""

import json
from pathlib import Path
from typing import Any, Union

missing_toml = False
try:
    import toml
except ImportError:
    missing_toml = True


class File:
    """A file."""

    def __init__(self, path: Union[str, Path]):
        self.path = path

    def load(self) -> Any:
        """Load the file."""
        raise NotImplementedError


class JSONFile(File):
    """A JSON file."""

    def load(self) -> Any:
        """Load the file."""
        with Path(self.path).open() as f:
            return json.load(f)


class TOMLFile(File):
    """A TOML file."""

    def load(self) -> Any:
        """Load the file."""
        with Path(self.path).open() as f:
            return toml.load(f)


def json_file(path: Union[str, Path]) -> Any:
    """Return a JSONFile instance."""
    return JSONFile(path)


def toml_file(path: Union[str, Path]) -> Any:
    """Return a TOMLFile instance."""
    if missing_toml:
        raise ImportError("The toml package is required for toml_file to work.")
    return TOMLFile(path)
