#!/usr/bin/env python3

"""Voecfg utils."""


import json
import os
from typing import Any, Union


def str_to_bool(val: str) -> bool:
    """Return True if input is either true or 1."""
    val = str(val).lower()

    if val in {"true", "1", "yes", "y"}:
        return True

    return False


def _load_from_environment(member_type: Any, env_key: str) -> Any:
    """Load a value from the environment."""
    env_value = os.environ[env_key]

    v: Union[str, int, bool, float, bytes, list, dict]
    if member_type is bool:
        v = str_to_bool(env_value)
    elif member_type is int:
        v = int(env_value)
    elif member_type is float:
        v = float(env_value)
    elif member_type is bytes:
        v = bytes(env_value, "utf-8")
    elif member_type in set({list, dict}):
        v = json.loads(env_value)
    else:
        v = env_value

    return v
