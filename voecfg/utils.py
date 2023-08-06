#!/usr/bin/env python3

"""Voecfg utils."""


def str_to_bool(val) -> bool:
    """Return True if input is either true or 1."""
    val = str(val).lower()

    if val in ["true", "1", "yes", "y"]:
        return True

    return False
