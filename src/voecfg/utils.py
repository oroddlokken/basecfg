#!/usr/bin/env python3

"""Voecfg utils."""

import json
import os
from typing import Any, get_origin

_TRUE_STRINGS = {"true", "1", "yes", "y"}
_FALSE_STRINGS = {"false", "0", "no", "n"}


def str_to_bool(val: str) -> bool:
    """Return True for 'true', '1', 'yes', 'y'; False for 'false', '0', 'no', 'n'.

    Raises ValueError for unrecognized input.
    """
    val = str(val).lower()

    if val in _TRUE_STRINGS:
        return True
    if val in _FALSE_STRINGS:
        return False

    accepted = sorted(_TRUE_STRINGS | _FALSE_STRINGS)
    msg = f"Cannot convert {val!r} to bool. Accepted values: {accepted}"
    raise ValueError(msg)


def load_from_environment(member_type: Any, env_key: str) -> Any:
    """Load a value from the environment and coerce it to the expected type."""
    env_value = os.environ[env_key]

    origin = get_origin(member_type) or member_type

    if origin is bool:
        return str_to_bool(env_value)
    if origin is int:
        return int(env_value)
    if origin is float:
        return float(env_value)
    if origin is bytes:
        return env_value.encode("utf-8")
    if origin in (list, dict):
        try:
            return json.loads(env_value)
        except json.JSONDecodeError as e:
            msg = f"Could not parse {env_key} as JSON: {e}"
            raise ValueError(msg) from e

    # Fallback: return as string
    return env_value
