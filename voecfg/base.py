#!/usr/bin/env python3

"""Voecfg base class."""

import json
import os
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

    _ignore_members = [  # noqa: RUF012
        "_config_path",
        "_current_dict",
        "_names",
        "_parent_dict",
        "_prefix",
        "_prefixes",
        "_cls_name",
        "export_config",
    ]

    def __init__(self):
        self._prefixes: Optional[list] = None
        self._parent_dict: Optional[dict] = None
        self._names: Optional[list] = None

        self._cls_name = self.__class__.__name__

        if not self._prefix:
            raise ValueError(f"{self._cls_name}._prefix is not set")

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

        members, type_hints = self._get_members()

        for member in members:
            member_type = None

            # Ignore dunder methods
            if member.startswith("__"):
                continue

            # Ignore private members belonging to BaseModel
            if member in self._ignore_members:
                continue

            if (
                getattr(self, member, None) is None
            ):  # noqa: SIM114, We want to these two separately in /tests
                member_type = type_hints.get(member)
                value = None
            elif getattr(self, member) is Required:
                member_type = type_hints.get(member)
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

            # Do a final check to see if the value is set
            if getattr(self, member, None) in [None, Required]:
                var_path = ".".join([*self._names, member])

                raise ValueError(f"Value for {var_path} / {env_key} not set.")

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
            # print(env_key, member_type, True)
            v = env_value

        return v

    def _get_members(self):
        """Get all members of the class, including members with only type hints."""
        # Get all members of the class with values
        members = {}
        for member in dir(self):
            members[member] = getattr(self, member)

        # Get all members of the class with type hints
        type_hints = get_type_hints(self)
        for member, hints in type_hints.items():
            # We only want members with no value
            if getattr(self, member, None) is None:
                members[member] = hints

        return members, type_hints

    def export_config(self):
        """Export the config as a dict.

        Keep in mind that this will contain secrets that were
        loaded from the environment.

        We also ignore any methods and callables.

        There are no guarantees that the config can be serialized
        to JSON or TOML.
        """
        # TODO: It should be nested under the key of the base class
        data = {}
        for member in dir(self):
            if member.startswith("_"):
                continue

            if member in self._ignore_members:
                continue

            value = getattr(self, member)

            if isinstance(value, _Base):
                data[member] = value.export_config()
            elif callable(value):
                continue
            else:
                data[member] = value

        return data


class SubConfig(_Base):
    """A class to hold configuration values for nested config classes.

    This class is meant to be subclassed.

    Class variables:
        _prefix: str, the prefix to use for environment variables
    """

    def __init__(self):
        super().__init__()


class BaseConfig(_Base):
    """A class to hold configuration values.

    This class is meant to be subclassed.

    Class variables:
        _prefix: str, the prefix to use for environment variables
        _config_path: None | str | Path | File, the path to the config file
    """

    def __init__(self):
        super().__init__()

        parent_dict: Any = {}

        config_path = self._config_path
        if isinstance(config_path, Path):
            config_path = str(config_path.resolve().absolute())

        # TODO: Include name of the class in the error message
        if config_path:
            # If the path is a File object, load it
            if isinstance(config_path, File):
                parent_dict = config_path.load()
                if not isinstance(parent_dict, (dict, list)):
                    raise ValueError(f"{config_path} did not return a dict")
            # If the path is a string, try to load it as a JSON or TOML file
            elif isinstance(config_path, str):
                if config_path.endswith(".json"):
                    parent_dict = json_file(config_path).load()
                elif config_path.endswith(".toml"):
                    parent_dict = toml_file(config_path).load()
                else:
                    raise ValueError(f"Unknown file type: {config_path}")
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
