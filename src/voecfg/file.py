#!/usr/bin/env python3

"""Load files."""

import contextlib
import json
from pathlib import Path
from types import ModuleType
from typing import Any

toml: ModuleType | None = None
with contextlib.suppress(ImportError):
    import toml


class File:
    """A file."""

    def __init__(self, path: str | Path):
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

    def __init__(self, path: str | Path):
        if not toml:
            msg = "The toml package is required for toml_file to work."
            raise ImportError(msg)
        super().__init__(path)

    def load(self) -> Any:
        """Load the file."""
        data: Any = None
        if toml:
            with Path(self.path).open() as f:
                data = toml.load(f)

        return data


# The factories return Any rather than JSONFile/TOMLFile because the value a caller
# ends up holding is the file's contents, not the File: _setup() swaps the attribute
# for load()'s result. Annotating the real return type makes the documented
# `devices: dict[str, Any] = json_file(...)` fail every type checker.
def json_file(path: str | Path) -> Any:
    """Return a JSONFile instance."""
    return JSONFile(path)


def toml_file(path: str | Path) -> Any:
    """Return a TOMLFile instance."""
    return TOMLFile(path)
