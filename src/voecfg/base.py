#!/usr/bin/env python3

"""Voecfg base class."""

import os
from pathlib import Path
from types import GenericAlias
from typing import Any, get_origin, get_type_hints

from voecfg.file import File, json_file, toml_file
from voecfg.utils import load_from_environment


class _Base:
    """Base class for config models."""

    _prefix: str = ""
    _config_path: File | str | Path | None = None
    _strict: bool = True

    def __init__(self) -> None:
        self._prefixes: list[str] | None = None
        self._parent_dict: dict[str, Any] | None = None
        self._names: list[str] | None = None

        self._cls_name = self.__class__.__name__

        if not self._prefix:
            msg = f"{self._cls_name}._prefix is not set"
            raise ValueError(msg)

        self._prefix = self._prefix.lower()

        self._members, self._type_hints = self._get_members()

    def _setup(  # noqa: PLR0912, C901
        self,
        _parent_dict: dict[str, Any] | None = None,
        _prefixes: list[str] | None = None,
        _names: list[str] | None = None,
    ) -> None:
        self._prefixes = _prefixes or []

        self._current_dict: Any = {}
        if _parent_dict:
            self._current_dict = _parent_dict.get(self._prefix, {})

        self._names = _names or []
        self._names.append(self._cls_name)

        for member in self._members:
            member_type: None | type = None

            if (
                getattr(self, member, None) is None
            ):  # noqa: SIM114, We want to test these two separately in /tests
                member_type = self._type_hints.get(member)
                value = None
            else:
                value = getattr(self, member)
                member_type = type(getattr(self, member))

            # Ignore instantiated classes
            if getattr(value, "__self__", None):
                continue

            # Format the environment variable name
            env_key = "_".join([*self._prefixes, self._prefix, member]).upper()

            # Check if the value is a subclass of BaseConfig
            if isinstance(value, _Base):
                new_prefixes = [*self._prefixes, self._prefix]
                new_names = [*self._names]

                value._setup(  # noqa: SLF001
                    _prefixes=new_prefixes,
                    _parent_dict=self._current_dict,
                    _names=new_names,
                )
            elif isinstance(value, File):
                setattr(self, member, value.load())
            else:
                # Try to get the value from the config file
                dict_value = self._current_dict.get(member)
                if dict_value:
                    setattr(self, member, dict_value)

                if env_key in os.environ:
                    env_value = load_from_environment(member_type, env_key)
                    setattr(self, member, env_value)

            var_path = ".".join([*self._names, member])
            # Do a final check to see if the value is set
            if getattr(self, member, None) is None:  # noqa: PLR6201
                msg = f"Value for {var_path} / {env_key} not set."
                raise ValueError(msg)

            if self._strict and not isinstance(getattr(self, member), _Base):
                value = getattr(self, member)
                actual: type = type(value)
                expected = self._type_hints.get(member)
                expected_origin = get_origin(expected) or expected

                # Special case: cast str to Path if expected is Path
                if expected_origin is Path and isinstance(value, str):
                    casted_value = Path(value)
                    setattr(self, member, casted_value)
                    value = casted_value
                    actual = Path

                if expected_origin is not None and not isinstance(
                    value,
                    expected_origin,
                ):
                    msg = (
                        f"{var_path} / {env_key} is {actual}, "
                        f"expected {expected_origin}"
                    )
                    raise TypeError(msg)

    def _get_members(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """Get all members of the class, including members with only type hints."""
        # Get all members of the class with values
        members: dict[str, Any] = {}
        type_hints: dict[str, Any] = {}
        for member in dir(self):
            # Ignore @property members
            if hasattr(self.__class__, member) and isinstance(
                getattr(self.__class__, member),
                property,
            ):
                continue

            # Ignore private members
            if member.startswith("_"):
                continue

            members[member] = getattr(self, member)
            type_hints[member] = type(getattr(self, member))

        # Get all members of the class with type hints
        type_hints.update(get_type_hints(self))
        for member, hint in type_hints.items():
            # get_type_hints behave different in 3.10+
            if member.startswith("_"):
                # the ignore below is needed for 3.10+ to make coverage happy
                continue  # pragma: no cover

            # We only want members with no value at all
            if getattr(self, member, None) is None:
                members[member] = hint
            elif isinstance(hint, GenericAlias):
                type_hints[member] = hint.__origin__

        return members, type_hints

    def as_dict(self) -> dict[str, Any]:
        """Export the config as a dict.

        Keep in mind that this will contain any secrets
        that were loaded from the environment.

        We also ignore any methods and callables.

        There are no guarantees that the config can be serialized
        to JSON or TOML, as the end result may contain any type of value.
        """
        data: dict[str, Any] = {}

        for member in self._members:
            value = getattr(self, member)

            if isinstance(value, _Base):
                data[value._prefix] = value.as_dict()  # noqa: SLF001
            elif callable(value):
                continue
            else:
                data[member] = value

        if isinstance(self, BaseConfig):
            data = {self._prefix: data}

        return data


class SubConfig(_Base):
    """A class to hold configuration values for nested config classes.

    This class is meant to be subclassed.

    Class variables:
        _prefix: str, the prefix to use for environment variables
    """


class BaseConfig(_Base):
    """A class to hold configuration values.

    This class is meant to be subclassed.

    Class variables:
        _prefix: str, the prefix to use for environment variables
        _config_path: None | str | Path | File, the path to the config file
        _strict: bool, raise if the type of a value does not match the type hint
    """

    def __init__(self) -> None:
        super().__init__()

        parent_dict: Any = {}

        config_path = self._config_path
        if isinstance(config_path, Path):
            config_path = str(config_path.resolve().absolute())

        if config_path:
            # If the path is a File object, load it
            if isinstance(config_path, File):
                parent_dict = config_path.load()
                if not isinstance(parent_dict, (dict, list)):
                    msg = f"{self._cls_name}: {config_path} did not return a dict"
                    raise TypeError(msg)

            # If the path is a string, try to load it as a JSON or TOML file
            elif isinstance(
                config_path,
                str,
            ):  # pyright: ignore[reportUnnecessaryIsInstance]
                if config_path.endswith(".json"):
                    parent_dict = json_file(config_path).load()
                elif config_path.endswith(".toml"):
                    parent_dict = toml_file(config_path).load()
                else:
                    msg = f"{self._cls_name}: Unknown file type: {config_path}"
                    raise ValueError(msg)

            else:
                _clsn = self._cls_name
                _tcp = type(config_path)
                msg = f"{_clsn}: Unsupported _config_path type: {_tcp}"
                raise ValueError(msg)

        self._setup(
            # TODO: Find out why pyright is complaining about this
            _parent_dict=parent_dict,  # pyright: ignore [reportArgumentType]
        )
