#!/usr/bin/env python3

"""Voecfg base class."""

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional, Union, get_type_hints

from voecfg.file import File, json_file, toml_file
from voecfg.utils import str_to_bool


class _Required:
    def __init__(self, _type=None):
        self._type = _type


Required: Any = _Required()


class _Base:
    """Base class for config models."""

    _prefix: str = ""
    _config_path: Optional[Union[File, str, Path]] = None
    _strict: bool = True

    def __init__(self):
        self._prefixes: Optional[list] = None
        self._parent_dict: Optional[dict] = None
        self._names: Optional[list] = None

        self._cls_name = self.__class__.__name__

        if not self._prefix:
            raise ValueError(f"{self._cls_name}._prefix is not set")

        self._prefix = self._prefix.lower()

        self._members, self._type_hints = self._get_members()

    def _setup(  # noqa: PLR0912
        self,
        _parent_dict: Optional[dict] = None,
        _prefixes: Optional[list] = None,
        _names: Optional[list] = None,
    ):
        self._prefixes = _prefixes or []

        self._current_dict: Any = {}
        if _parent_dict:
            self._current_dict = _parent_dict.get(self._prefix, {})

        self._names = _names or []
        self._names.append(self._cls_name)

        for member in self._members:
            member_type = None

            if (
                getattr(self, member, None) is None
            ):  # noqa: SIM114, We want to test these two separately in /tests
                member_type = self._type_hints.get(member)
                value = None
            elif getattr(self, member) is Required:
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
                # setattr(self, member, cls)
            elif isinstance(value, File):
                setattr(self, member, value.load())
            else:
                # Try to get the value from the config file
                dict_value = self._current_dict.get(member)
                if dict_value:
                    setattr(self, member, dict_value)

                if env_key in os.environ:
                    env_value = self._load_from_environment(member_type, env_key)
                    setattr(self, member, env_value)

            var_path = ".".join([*self._names, member])
            # Do a final check to see if the value is set
            if getattr(self, member, None) in [None, Required]:
                raise ValueError(f"Value for {var_path} / {env_key} not set.")

            if self._strict and not isinstance(getattr(self, member), _Base):
                actual = type(getattr(self, member))
                expected = self._type_hints.get(member)
                if actual != expected:
                    raise TypeError(
                        f"{var_path} / {env_key} is {actual}, expected {expected}"
                    )

    def _load_from_environment(self, member_type, env_key):
        """Load a value from the environment."""
        env_value = os.environ[env_key]

        v: Union[str, int, bool, float, bytes, list, dict]
        if member_type == bool:
            v = str_to_bool(env_value)
        elif member_type == int:
            v = int(env_value)
        elif member_type == float:
            v = float(env_value)
        elif member_type == bytes:
            v = bytes(env_value, "utf-8")
        elif member_type in [list, dict]:
            v = json.loads(env_value)
        else:
            v = env_value

        return v

    def _get_members(self):
        """Get all members of the class, including members with only type hints."""
        # Get all members of the class with values
        members = {}
        type_hints = {}
        for member in dir(self):
            # Ignore @property members
            if hasattr(self.__class__, member) and isinstance(
                getattr(self.__class__, member), property
            ):
                continue

            # Ignore private members
            if member.startswith("_"):
                continue

            members[member] = getattr(self, member)
            type_hints[member] = type(getattr(self, member))

        # Get all members of the class with type hints
        type_hints.update(get_type_hints(self))
        for member, hints in type_hints.items():
            # get_type_hints() behave differently in Python before
            # and after 3.10
            if sys.version_info.minor < 10 and member.startswith("_"):
                continue  # pragma: no cover

            # We only want members with no value
            if getattr(self, member, None) is None:
                members[member] = hints

        return members, type_hints

    def as_dict(self):
        """Export the config as a dict.

        Keep in mind that this will contain any secrets
        that were loaded from the environment.

        We also ignore any methods and callables.

        There are no guarantees that the config can be serialized
        to JSON or TOML, as the end result may contain any type of value.
        """
        data = {}

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

    def __init__(self):
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
                    raise ValueError(
                        f"{self._cls_name}: {config_path} did not return a dict"
                    )

            # If the path is a string, try to load it as a JSON or TOML file
            elif isinstance(config_path, str):
                if config_path.endswith(".json"):
                    parent_dict = json_file(config_path).load()
                elif config_path.endswith(".toml"):
                    parent_dict = toml_file(config_path).load()
                else:
                    raise ValueError(
                        f"{self._cls_name}: Unknown file type: {config_path}"
                    )

            else:
                raise ValueError(
                    (
                        f"{self._cls_name}: Unsupported _config_path "
                        f"type: {type(config_path)}"
                    )
                )

        self._setup(
            # TODO: Find out why pyright is complaining about this
            _parent_dict=parent_dict,  # pyright: ignore [reportGeneralTypeIssues]
        )
