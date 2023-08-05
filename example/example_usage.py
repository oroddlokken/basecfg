#!/usr/bin/env python3

"""Example usage of basecfg."""

# ruff: noqa: T201, T203

import os
from pathlib import Path
from pprint import pprint

from basecfg import BaseConfig, Required, SubConfig, toml_file


class DeepConfig(SubConfig):
    """A deeply nested class."""

    # The environment variable prefix for this class.
    # Since this class is nested under NestedConfig, which is
    # nested under Config, the final environment variable
    # prefix will be rendered as MYAPP_NESTED_DEEP_
    _prefix = "deep"

    # Read the environment variables as described in the comments
    # and parse them as JSON
    some_dict: dict  # MYAPP_NESTED_DEEP_SOME_DICT
    some_dict_empty: dict  # MYAPP_NESTED_DEEP_SOME_DICT_EMPTY
    some_list: list  # MYAPP_NESTED_DEEP_SOME_LIST

    # We set this value in example/example_usage.json, which is loaded
    # in the Config class below.
    another_string: str

    def my_method(self):
        """Return a list of values."""
        return [self.some_dict_empty]


class NestedConfig(SubConfig):
    """A class to hold configuration values for something."""

    # The environment variable prefix for this class.
    # Since this class is nested under Config, the final
    # environment variable prefix will be rendered as MYAPP_NESTED_
    _prefix = "nested"

    # Require the environment variable MYAPP_NESTED_SECRET_KEY to be set,
    # and if it is not set, raise an exception. We don't want to set a default
    # value for this variable, as it is a secret, so we set it to Required.
    # That way, if it is not set in the environment or config file,
    # an exception will still be raised.
    secret_key: str = Required

    # Read the environment MYAPP_NESTED_DEBUG_MODE,
    # but if it is not defined, default to False
    debug_mode = False

    auto_reload: bool

    # Read the environment MYAPP_NESTED_SOME_BYTES
    # and decode it as UTF-8 bytes.
    some_bytes: bytes = Required

    # Calling cfg_cls(DeepConfig) is not strictly necessary, but it is a convenience
    # wrapper that makes IDEs think it is a instance of DeepConfig and not just
    # the DeepConfig class itself. Useful if your nested class has methods.
    deep = DeepConfig()

    lottery_number = 42

    # We override this value in example/example_usage.json, which is loaded
    # in the Config class below.
    some_string: str = "katt"


class Config(BaseConfig):
    """MyApp Config."""

    # The environment variable prefix for this app,
    # rendered as MYAPP_
    _prefix = "myapp"

    # Read default values from a JSON file in the same directory as this file.
    _config_path = Path(__file__).parent / "config.json"

    # Note we don't use cfg_cls(SubConfig) here, as it will work just fine
    # without it.
    nested = NestedConfig()

    # This is loaded from the JSON file.
    numbers: list

    # @property works as expected
    @property
    def numbers_sum(self):
        """Return the sum of some numbers."""
        return sum([self.nested.lottery_number, 13])

    # Load a TOML file from the same directory as this file.
    # We include a type hint that tells the IDE that this is a dict.
    parameters: dict = toml_file(Path(__file__).parent / "parameters.toml")


# Set the required environment variables,
# usually we would do this in a .env file or setting in the environment beforehand
# but for demonstration purposes we set them at runtime.
os.environ["MYAPP_NESTED_SECRET_KEY"] = "secret"
os.environ["MYAPP_NESTED_AUTO_RELOAD"] = "true"
os.environ["MYAPP_NESTED_SOME_BYTES"] = "🐱"
os.environ["MYAPP_NESTED_DEEP_SOME_DICT"] = '{"a": 1}'
os.environ["MYAPP_NESTED_DEEP_SOME_DICT_EMPTY"] = "{}"
os.environ["MYAPP_NESTED_DEEP_SOME_LIST"] = "[1, 2, 3]"

# Make sure MYAPP_NESTED_DEBUG_MODE is not set to anything
assert os.environ.get("MYAPP_NESTED_DEBUG_MODE") is None

# Get an initialized config, including the subclasses.
# Note that we call the classmethod load() on the Config class.
config = Config()

# Make sure the values are correct
assert config.numbers == [4, 8, 15, 16, 23, 42]
assert config.numbers_sum == 55
assert isinstance(config.parameters, dict)
assert config.parameters["x"] == "y"

assert config.nested.auto_reload is True
assert config.nested.debug_mode is False
assert config.nested.secret_key == "secret"
assert config.nested.some_bytes == "🐱".encode("utf-8")
assert config.nested.some_string == "The quick brown fox jumps over the lazy dog."

assert config.nested.deep.another_string == "Lorem ipsum dolor sit amet"
assert config.nested.deep.my_method() == [{}]
assert config.nested.deep.some_dict == {"a": 1}
assert config.nested.deep.some_dict_empty == {}
assert config.nested.deep.some_list == [1, 2, 3]

pprint(config.export_config())
