#!/usr/bin/env python3

"""Voecfg base class."""

import os
import threading
import warnings
from pathlib import Path
from types import GenericAlias, NoneType, UnionType
from typing import Any, Union, cast, get_args, get_origin, get_type_hints

from voecfg.file import File, json_file, toml_file
from voecfg.utils import load_from_environment


def _is_optional_type(hint: Any) -> bool:
    """Check if a type hint is Optional (i.e., X | None or Optional[X])."""
    origin = get_origin(hint)
    if origin is Union or origin is UnionType:
        return NoneType in get_args(hint)
    return False


_REDACTED = "**REDACTED**"
_cache_lock = threading.Lock()


class _Base:
    """Base class for config models."""

    _prefix: str = ""
    _config_path: File | str | Path | None = None
    _strict: bool = True
    _secret_keys: set[str] = set()
    _no_validate: set[str] = set()
    _coercions: dict[tuple[type, type], Any] = {
        (str, Path): Path,
    }

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

    def _setup(
        self,
        _parent_dict: dict[str, Any] | None = None,
        _prefixes: list[str] | None = None,
        _names: list[str] | None = None,
    ) -> None:
        self._prefixes = _prefixes or []

        self._current_dict: Any = {}
        if _parent_dict:
            self._current_dict = _parent_dict.get(self._prefix, {})

        self._warn_unknown_keys()

        self._names = _names or []
        self._names.append(self._cls_name)

        for member in self._members:
            member_type: None | type = None

            if getattr(self, member, None) is None:  # noqa: SIM114, We want to test these two separately in /tests
                member_type = self._type_hints.get(member)
                value = None
            else:
                value = getattr(self, member)
                member_type = type(getattr(self, member))

            # Ignore instantiated classes
            if getattr(value, "__self__", None):
                continue

            env_key = "_".join([*self._prefixes, self._prefix, member]).upper()

            if isinstance(value, _Base):
                self._init_nested(value)
            elif isinstance(value, File):
                setattr(self, member, value.load())
            else:
                self._load_from_file(member)
                self._load_from_env(member, member_type, env_key)

            var_path = ".".join([*self._names, member])
            self._check_required(member, var_path, env_key)

            should_validate = self._strict and member not in self._no_validate
            if should_validate and not isinstance(getattr(self, member), _Base):
                self._validate_type(member, var_path, env_key)

    def _warn_unknown_keys(self) -> None:
        """Warn about unknown keys in the config file section."""
        if not isinstance(self._current_dict, dict):
            return
        known_keys = set(self._members.keys())
        for m in self._members:
            val = getattr(self, m, None)
            if isinstance(val, _Base):
                known_keys.add(val._prefix)  # noqa: SLF001
        unknown = set(self._current_dict.keys()) - known_keys
        if unknown:
            warnings.warn(
                f"{self._cls_name}: unknown config keys: {sorted(unknown)}",
                stacklevel=3,
            )

    def _init_nested(self, value: "_Base") -> None:
        """Initialize a nested SubConfig."""
        value._setup(  # noqa: SLF001
            _prefixes=[*self._prefixes, self._prefix],
            _parent_dict=self._current_dict,
            _names=[*self._names],
        )

    def _load_from_file(self, member: str) -> None:
        """Load a member value from the config file dict."""
        dict_value = self._current_dict.get(member)
        if dict_value is not None:
            setattr(self, member, dict_value)

    def _load_from_env(
        self, member: str, member_type: type | None, env_key: str
    ) -> None:
        """Load a member value from the environment, overriding file values."""
        if env_key in os.environ:
            env_value = load_from_environment(member_type, env_key)
            setattr(self, member, env_value)

    def _check_required(self, member: str, var_path: str, env_key: str) -> None:
        """Raise if a required (non-optional) field is still None."""
        hint = self._type_hints.get(member)
        is_optional = _is_optional_type(hint)
        if getattr(self, member, None) is None and not is_optional:  # noqa: PLR6201
            msg = (
                f"Configuration error:\n"
                f"  - Class path: {var_path}\n"
                f"  - Environment variable: {env_key}\n"
                f"  - Neither was set in config file or environment"
            )
            raise ValueError(msg)

    def _try_coerce(self, member: str, value: Any, target: type) -> tuple[Any, type]:
        """Try to coerce a value to the target type using _coercions registry."""
        actual_type = type(value)
        coercion = self._coercions.get((actual_type, target))
        if coercion is not None:
            value = coercion(value)
            setattr(self, member, value)
            return value, type(value)
        return value, actual_type

    def _validate_type(self, member: str, var_path: str, env_key: str) -> None:
        """Validate that the member value matches its type hint."""
        value = getattr(self, member)
        hint = self._type_hints.get(member)
        is_optional = _is_optional_type(hint)

        # Skip type check for None values on Optional fields
        if value is None and is_optional:
            return

        actual: type = type(value)
        expected = hint

        # Unwrap Optional[T] / T | None to get the inner type
        if _is_optional_type(expected):
            args = [a for a in get_args(expected) if a is not NoneType]
            expected = args[0] if len(args) == 1 else expected

        # Check if expected is a Union type (e.g. str | int)
        expected_origin = get_origin(expected)
        is_union = expected_origin is Union or expected_origin is UnionType
        if is_union:
            union_args = get_args(expected)
            # Try coercion to any of the union types
            for target in union_args:
                value, actual = self._try_coerce(member, value, target)
            if not isinstance(value, union_args):
                msg = (
                    f"{var_path} / {env_key} is {actual}, "
                    f"expected {expected}"
                )
                raise TypeError(msg)
            return

        expected_origin = expected_origin or expected

        # Try coercion via registry
        value, actual = self._try_coerce(member, value, expected_origin)

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
        cls = self.__class__

        # Check class-level cache
        cache_attr = "_cached_members_result"
        cached = getattr(cls, cache_attr, None)
        if cached is not None:
            return cached

        with _cache_lock:
            # Double-check after acquiring lock
            cached = getattr(cls, cache_attr, None)
            if cached is not None:
                return cached

            # Get all members from class vars (avoids full MRO walk via dir())
            members: dict[str, Any] = {}
            type_hints: dict[str, Any] = {}
            for klass in reversed(cls.__mro__):
                for member, val in vars(klass).items():
                    if member.startswith("_"):
                        continue
                    if isinstance(val, property):
                        members.pop(member, None)
                        continue
                    members[member] = val
                    type_hints[member] = type(val)

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

            result = (members, type_hints)
            setattr(cls, cache_attr, result)
            return result

    def as_dict(self, *, redact: bool = False) -> dict[str, Any]:
        """Export the config as a dict.

        Args:
            redact: If True, replace values of fields listed in
                _secret_keys with '**REDACTED**'.

        We also ignore any methods and callables.

        There are no guarantees that the config can be serialized
        to JSON or TOML, as the end result may contain any type of value.
        """
        data: dict[str, Any] = {}

        for member in self._members:
            value = getattr(self, member)

            if isinstance(value, _Base):
                data[value._prefix] = value.as_dict(redact=redact)  # noqa: SLF001
            elif callable(value):
                continue
            elif redact and member in self._secret_keys:
                data[member] = _REDACTED
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
        _strict: bool, raise if the type of a value does not match the type hint.
            Note: for generic types (e.g. list[str], dict[str, int]), only the
            origin type (list, dict) is checked, not the element types.
        _secret_keys: set[str], field names to redact when as_dict(redact=True)
        _no_validate: set[str], field names to skip type validation for
        _coercions: dict mapping (from_type, to_type) to a callable for
            automatic type coercion. Default: {(str, Path): Path}.
    """

    def __init__(self, *, prefix: str | None = None) -> None:
        if prefix is not None:
            self._prefix = prefix
        super().__init__()

        parent_dict: dict[str, Any] = {}

        config_path = self._config_path
        if isinstance(config_path, Path):
            config_path = str(config_path.resolve().absolute())

        if config_path:
            # If the path is a File object, load it
            if isinstance(config_path, File):
                loaded: Any = config_path.load()
                if not isinstance(loaded, dict):
                    msg = f"{self._cls_name}: {config_path} did not return a dict"
                    raise TypeError(msg)
                parent_dict = cast(dict[str, Any], loaded)

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
            _parent_dict=parent_dict,
        )
