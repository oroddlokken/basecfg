#!/usr/bin/env python3

import json
import unittest
from pathlib import Path
from typing import Any, Union

import toml
from dotenv import load_dotenv

from voecfg import BaseConfig, File, SubConfig, json_file, toml_file

load_dotenv(Path(__file__).parent / "voecfg_data" / "env")

# ruff: noqa: PLR2004, PLR6301, N801


class BrokenMockFile(File):
    def load(self) -> Any:
        return 2


def broken_mock_file(path: Union[str, Path]) -> Any:
    """Return a BrokenMockFile instance."""
    return BrokenMockFile(path)


class SuccessTest(unittest.TestCase):
    def test_subcls_env_types(self):
        """Test that subclasses and env work as expected."""

        class FlaskConfig(SubConfig):
            """A class to hold configuration values for the database."""

            _prefix = "sub"

            var_int: int
            var_str: str
            var_bool: bool
            var_bool_false: bool
            var_float: float
            var_dict: dict
            var_list: list
            var_bytes: bytes

        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            flask = FlaskConfig()

        config = voecfgTestConfig()

        assert config.flask.var_int == 1
        assert config.flask.var_str == "blah"
        assert config.flask.var_bool is True
        assert config.flask.var_bool_false is False
        assert config.flask.var_float == 0.4
        assert config.flask.var_dict == {"a": 1}
        assert config.flask.var_list == [1, 2, 3]
        assert config.flask.var_bytes == "🐱".encode("utf-8")

    def test_raise_if_not_set1(self):
        """Test that raise_if_not_set() works."""

        class voecfgTestConfig1(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg_rins"

            _config_path = json_file(
                Path(__file__).parent / "voecfg_data" / "rins.json",
            )

            str1: str

        config = voecfgTestConfig1()
        assert config.str1 == "coffee"

    def test_config_file_toml(self):
        """Test that config.toml is loaded."""

        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            _config_path = toml_file(
                Path(__file__).parent / "voecfg_data" / "config.toml",
            )

            other_value: str

        config = voecfgTestConfig()
        assert config.other_value == "ferrari"

        class voecfgTestConfig2(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            _config_path = (
                Path(__file__).parent / "voecfg_data" / "config.toml"
            ).as_posix()

            other_value: str

        config2 = voecfgTestConfig2()
        assert config2.other_value == "ferrari"

    def test_config_file_json(self):
        """Test that config.json is loaded."""

        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            _config_path = json_file(
                Path(__file__).parent / "voecfg_data" / "config.json",
            )

            another_value: str

        config = voecfgTestConfig()
        assert config.another_value == "porsche"

        class voecfgTestConfig2(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            _config_path = (
                Path(__file__).parent / "voecfg_data" / "config.json"
            ).as_posix()

            another_value: str

        config2 = voecfgTestConfig2()
        assert config2.another_value == "porsche"

        class voecfgTestConfig3(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            _config_path = Path(__file__).parent / "voecfg_data" / "config.json"

            another_value: str

        config3 = voecfgTestConfig3()
        assert config3.another_value == "porsche"

    def test_ignore_property(self):
        """Test that properties are ignored."""

        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            @property
            def blah(self):
                return 1 + 3

        config = voecfgTestConfig()
        assert config.blah == 4

    def test_load_json(self):
        """Test that load_json works."""

        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            devices: dict = json_file("voecfg_data/load_json.json")

        config = voecfgTestConfig()
        assert config.devices["a"] == 1
        assert config.devices["b"][1] == 2

    def test_load_toml(self):
        """Test that load_toml works."""

        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            devices: dict = toml_file("voecfg_data/load_toml.toml")

        config = voecfgTestConfig()
        self.assertFalse(config.devices["a"][0])
        assert config.devices["test"]["c"] == "d"

    def test_export(self):
        """Test that as_dict works."""

        class FlaskConfig(SubConfig):
            """A class to hold configuration values for the database."""

            _prefix = "sub_export"

            var_int = 13
            var_str = "blah"

            def ignore_me(self):
                return 1

        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg_export"

            flask = FlaskConfig()

            @property
            def my_property(self):
                """Test that properties are included."""
                return 1 + 3

        config = voecfgTestConfig()
        # Make Vulture shut up
        assert config.flask.ignore_me is not None
        assert config.my_property is not None
        data = config.as_dict()
        assert data == {
            "voecfg_export": {
                "sub_export": {"var_int": 13, "var_str": "blah"},
            },
        }


class OrderTest(unittest.TestCase):
    def test_env_over_class_value(self):
        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            # 959 in .env
            env1 = "911"

        config = voecfgTestConfig()
        assert config.env1 == "959"

    def test_env_over_file_value(self):
        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            # F50 in config.json, F40 in .env
            value2: str

            _config_path = json_file(
                Path(__file__).parent / "voecfg_data" / "config.json",
            )

        config = voecfgTestConfig()
        assert config.value2 == "F40"

    def test_file_over_class_value(self):
        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            value3: str = "P1"

            _config_path = json_file(
                Path(__file__).parent / "voecfg_data" / "config.json",
            )

        config = voecfgTestConfig()
        assert config.value3 == "F1"


class FailureTest(unittest.TestCase):
    def test_missing_value(self):
        """Test that a missing value raises an error."""

        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            var_int_missing: int

        with self.assertRaises(ValueError):
            voecfgTestConfig()

    def test_load_json_invalid(self):
        """Test that load_json fails on invalid JSON."""

        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            devices: dict = json_file("voecfg_data/load_json_invalid.json")

        with self.assertRaises(json.decoder.JSONDecodeError):
            voecfgTestConfig()

    def test_load_toml_invalid(self):
        """Test that load_toml works."""

        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            devices: dict = toml_file("voecfg_data/load_toml_invalid.toml")

        with self.assertRaises(toml.decoder.TomlDecodeError):
            voecfgTestConfig()

    def test_file_load_error(self):
        """Test that File() raises an error."""
        with self.assertRaises(NotImplementedError):
            File("somepath").load()

    def test_required_fail(self):
        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            env_required_int: int

        with self.assertRaises(ValueError):
            voecfgTestConfig()
            # Make vulture shut up
            assert voecfgTestConfig.env_required_int is not None

    def test_exception_message(self):
        class DeepNestedConfig(SubConfig):
            """A class to hold configuration values for the database."""

            _prefix = "subsub"

            var_int: int

        class NestedConfig(SubConfig):
            """A class to hold configuration values for the database."""

            _prefix = "sub"

            something = "something"

            subsub = DeepNestedConfig()

        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            sub = NestedConfig()

        excepted = "DeepNestedConfig.var_int / " "VOECFG_SUB_SUBSUB_VAR_INT"
        try:
            c = voecfgTestConfig()
            # Make vulture shut up
            assert c.sub.subsub is not None
            assert c.sub.something is not None
        except ValueError as e:
            assert excepted in str(e)

    def test_no_prefix(self):
        """Test that a missing _prefix raises an error."""

        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

        try:
            voecfgTestConfig()
        except ValueError as e:
            assert "voecfgTestConfig._prefix is not set" in str(e)

    def test_unknown_file_type(self):
        """Test that unknown file types raises an error."""

        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"
            _config_path = "config.unknown"

        try:
            voecfgTestConfig()
        except ValueError as e:
            assert "Unknown file type" in str(e)

        class voecfgTestConfig2(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"
            _config_path = float(1.0)  # type: ignore

        try:
            voecfgTestConfig2()
        except ValueError as e:
            assert (
                "voecfgTestConfig2: Unsupported _config_path type: <class 'float'>"
                in str(e)
            )

    def test_broken_mock_file(self):
        """Test that a random File subclass works."""

        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            _config_path = broken_mock_file("something.json")

        with self.assertRaises(ValueError):
            voecfgTestConfig()

    def test_wrong_type(self):
        class voecfgTestConfig(BaseConfig):
            """Test config for voecfg."""

            _prefix = "voecfg"

            some_str_we_pretend_is_int: int = 1

            _config_path = json_file(
                Path(__file__).parent / "voecfg_data" / "config.json",
            )

        with self.assertRaises(TypeError):
            voecfgTestConfig()
            # Make vulture shut up
            assert voecfgTestConfig.some_str_we_pretend_is_int is not None


if __name__ == "__main__":
    unittest.main()
