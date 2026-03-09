#!/usr/bin/env python3

import json
from pathlib import Path
from typing import Any

import dotenv
import pytest
import toml

from voecfg import BaseConfig, File, SubConfig, json_file, toml_file
from voecfg.utils import str_to_bool

# ruff: noqa: UP007

_voecfg__data = Path(__file__).parent / "voecfg_data"


@pytest.fixture(autouse=True)
def _env_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Load test env vars via monkeypatch so they're cleaned up after each test."""
    env_file = Path(__file__).parent / "voecfg_data" / "env"
    for key, value in dotenv.dotenv_values(env_file).items():
        if value is not None:
            monkeypatch.setenv(key, value)

# ruff: noqa: PLR2004, PLR6301, N801, S108, RUF043


class BrokenMockFile(File):
    def load(self) -> Any:
        return 2


def broken_mock_file(path: str | Path) -> Any:
    """Return a BrokenMockFile instance."""
    return BrokenMockFile(path)


def test_subcls_env_types() -> None:
    class FlaskConfig(SubConfig):
        _prefix = "sub"
        var_int: int
        var_str: str
        var_bool: bool
        var_bool_false: bool
        var_float: float
        var_dict: dict[str, int]
        var_list: list[int]
        var_bytes: bytes
        var_str_to_path: Path

    class voecfgTestConfig(BaseConfig):
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
    assert config.flask.var_bytes == "🐱".encode()
    assert config.flask.var_str_to_path == Path("/tmp/some_file.txt")


def test_raise_if_not_set1() -> None:
    class voecfgTestConfig1(BaseConfig):
        _prefix = "voecfg_rins"
        _config_path = json_file(Path(__file__).parent / "voecfg_data" / "rins.json")
        str1: str

    config = voecfgTestConfig1()
    assert config.str1 == "coffee"


def test_config_file_toml() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        _config_path = toml_file(Path(__file__).parent / "voecfg_data" / "config.toml")
        other_value: str

    config = voecfgTestConfig()
    assert config.other_value == "ferrari"

    class voecfgTestConfig2(BaseConfig):
        _prefix = "voecfg"
        _config_path = (
            Path(__file__).parent / "voecfg_data" / "config.toml"
        ).as_posix()
        other_value: str

    config2 = voecfgTestConfig2()
    assert config2.other_value == "ferrari"


def test_config_file_json() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        _config_path = json_file(Path(__file__).parent / "voecfg_data" / "config.json")
        another_value: str

    config = voecfgTestConfig()
    assert config.another_value == "porsche"

    class voecfgTestConfig2(BaseConfig):
        _prefix = "voecfg"
        _config_path = (
            Path(__file__).parent / "voecfg_data" / "config.json"
        ).as_posix()
        another_value: str

    config2 = voecfgTestConfig2()
    assert config2.another_value == "porsche"

    class voecfgTestConfig3(BaseConfig):
        _prefix = "voecfg"
        _config_path = Path(__file__).parent / "voecfg_data" / "config.json"
        another_value: str

    config3 = voecfgTestConfig3()
    assert config3.another_value == "porsche"


def test_ignore_property() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"

        @property
        def blah(self) -> int:
            return 1

    config = voecfgTestConfig()
    assert hasattr(config, "blah")


def test_load_json() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        devices: dict[str, Any] = json_file(_voecfg__data / "load_json.json")

    config = voecfgTestConfig()
    assert config.devices["a"] == 1


def test_load_toml() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        devices: dict[str, Any] = toml_file(_voecfg__data / "load_toml.toml")

    config = voecfgTestConfig()
    assert not config.devices["a"][0]
    assert config.devices["test"]["c"] == "d"


def test_export() -> None:
    class FlaskConfig(SubConfig):
        _prefix = "sub_export"
        var_int = 13
        var_str = "blah"

        def ignore_me(self) -> int:
            return 1

    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg_export"
        flask = FlaskConfig()

        @property
        def my_property(self) -> int:
            return 1 + 3

    config = voecfgTestConfig()
    assert config.flask.ignore_me is not None
    assert config.my_property is not None
    data = config.as_dict()
    assert data == {
        "voecfg_export": {
            "sub_export": {"var_int": 13, "var_str": "blah"},
        },
    }


def test_env_over_class_value() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        env1 = "911"

    config = voecfgTestConfig()
    assert config.env1 == "959"


def test_env_over_file_value() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        value2: str
        _config_path = json_file(Path(__file__).parent / "voecfg_data" / "config.json")

    config = voecfgTestConfig()
    assert config.value2 == "F40"


def test_file_over_class_value() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        value3: str = "P1"
        _config_path = json_file(Path(__file__).parent / "voecfg_data" / "config.json")

    config = voecfgTestConfig()
    assert config.value3 == "F1"


def test_missing_value() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        var_int_missing: int

    with pytest.raises(
        ValueError,
        match="Class path: voecfgTestConfig.var_int_missing",
    ):
        voecfgTestConfig()


def test_load_json_invalid() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        devices: dict[str, Any] = json_file(_voecfg__data / "load_json_invalid.json")

    with pytest.raises(json.decoder.JSONDecodeError):
        voecfgTestConfig()


def test_load_toml_invalid() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        devices: dict[str, Any] = toml_file(_voecfg__data / "load_toml_invalid.toml")

    with pytest.raises(toml.decoder.TomlDecodeError):
        voecfgTestConfig()


def test_file_load_error() -> None:
    with pytest.raises(NotImplementedError):
        File("somepath").load()


def test_required_fail() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        env_required_int: int

    with pytest.raises(
        ValueError,
        match="Environment variable: VOECFG_ENV_REQUIRED_INT",
    ):
        voecfgTestConfig()


def test_exception_message() -> None:
    class DeepNestedConfig(SubConfig):
        _prefix = "subsub"
        var_int: int

    class NestedConfig(SubConfig):
        _prefix = "sub"
        something = "something"
        subsub = DeepNestedConfig()

    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        sub = NestedConfig()

    with pytest.raises(
        ValueError,
        match="Class path: voecfgTestConfig.NestedConfig.DeepNestedConfig.var_int",
    ):
        voecfgTestConfig()


def test_no_prefix() -> None:
    class voecfgTestConfig(BaseConfig):
        pass

    with pytest.raises(
        ValueError,
        match="voecfgTestConfig._prefix is not set",
    ):
        voecfgTestConfig()


def test_unknown_file_type() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        _config_path = "config.unknown"

    with pytest.raises(
        ValueError,
        match="voecfgTestConfig: Unknown file type: config.unknown",
    ):
        voecfgTestConfig()

    class voecfgTestConfig2(BaseConfig):
        _prefix = "voecfg"
        _config_path = 1.0  # type: ignore

    with pytest.raises(
        ValueError,
        match="voecfgTestConfig2: Unsupported _config_path type: <class 'float'>",
    ):
        voecfgTestConfig2()


def test_broken_mock_file() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        _config_path = broken_mock_file("something.json")

    with pytest.raises(
        TypeError,
        match="did not return a dict",
    ):
        voecfgTestConfig()


def test_wrong_type() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        some_str_we_pretend_is_int: int = 1
        _config_path = json_file(Path(__file__).parent / "voecfg_data" / "config.json")

    with pytest.raises(
        TypeError,
        match="is <class 'str'>, expected <class 'int'>",
    ):
        voecfgTestConfig()


def test_str_to_bool_valid_values() -> None:
    for val in ("true", "True", "1", "yes", "y", "YES", "Y"):
        assert str_to_bool(val) is True
    for val in ("false", "False", "0", "no", "n", "NO", "N"):
        assert str_to_bool(val) is False


def test_str_to_bool_rejects_unrecognized() -> None:
    for val in ("tru", "fals", "nope", "2", "maybe", ""):
        with pytest.raises(ValueError, match="Cannot convert"):
            str_to_bool(val)


def test_falsy_config_file_values() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        _strict = False
        _config_path = json_file(Path(__file__).parent / "voecfg_data" / "falsy_values.json")
        count: int = 99
        debug: bool = True
        label: str = "default"
        items: list[int] = [1, 2, 3]

    config = voecfgTestConfig()
    assert config.count == 0
    assert config.debug is False
    assert config.label == ""
    assert config.items == []


def test_optional_field_not_set() -> None:
    from typing import Optional

    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg_opt"
        required_val: str = "hello"
        optional_val: Optional[str] = None

    config = voecfgTestConfig()
    assert config.required_val == "hello"
    assert config.optional_val is None


def test_optional_field_with_pipe_syntax() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg_opt2"
        required_val: str = "hello"
        optional_val: str | None = None

    config = voecfgTestConfig()
    assert config.required_val == "hello"
    assert config.optional_val is None


def test_optional_field_set_from_config() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        _config_path = json_file(Path(__file__).parent / "voecfg_data" / "config.json")
        another_value: str | None = None

    config = voecfgTestConfig()
    assert config.another_value == "porsche"


def test_union_type_strict_mode() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg_union"
        value: str | int = "hello"

    config = voecfgTestConfig()
    assert config.value == "hello"


def test_union_type_strict_mode_int() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg_union2"
        value: str | int = 42

    config = voecfgTestConfig()
    assert config.value == 42


def test_union_type_strict_mode_rejects_wrong_type() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg_union3"
        value: str | int = 3.14

    with pytest.raises(TypeError, match="expected str | int"):
        voecfgTestConfig()


def test_as_dict_redact_secrets() -> None:
    class DbConfig(SubConfig):
        _prefix = "db"
        _secret_keys = {"password"}
        host = "localhost"
        password = "s3cret"

    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg_redact"
        _secret_keys = {"api_key"}
        api_key = "key123"
        db = DbConfig()

    config = voecfgTestConfig()

    # Without redact - secrets visible
    data = config.as_dict()
    assert data["voecfg_redact"]["api_key"] == "key123"
    assert data["voecfg_redact"]["db"]["password"] == "s3cret"

    # With redact - secrets masked
    data = config.as_dict(redact=True)
    assert data["voecfg_redact"]["api_key"] == "**REDACTED**"
    assert data["voecfg_redact"]["db"]["password"] == "**REDACTED**"
    assert data["voecfg_redact"]["db"]["host"] == "localhost"


def test_optional_union_type() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg_union4"
        value: str | int | None = None

    config = voecfgTestConfig()
    assert config.value is None


def test_unknown_config_keys_warns() -> None:
    import warnings

    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg"
        _strict = False
        _config_path = json_file(Path(__file__).parent / "voecfg_data" / "config.json")
        another_value: str

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        config = voecfgTestConfig()
        assert config.another_value == "porsche"
        unknown_warnings = [x for x in w if "unknown config keys" in str(x.message)]
        assert len(unknown_warnings) == 1
        assert "some_str_we_pretend_is_int" in str(unknown_warnings[0].message)


def test_no_validate_per_field() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg_noval"
        _no_validate = {"flexible_field"}
        strict_field: str = "hello"
        flexible_field: int = "not_an_int"  # type: ignore[assignment]

    # flexible_field skips validation despite _strict=True
    config = voecfgTestConfig()
    assert config.flexible_field == "not_an_int"
    assert config.strict_field == "hello"


def test_no_validate_still_validates_others() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg_noval2"
        _no_validate = {"other"}
        wrong_type: int = "oops"  # type: ignore[assignment]
        other: str = "fine"

    with pytest.raises(TypeError, match="expected <class 'int'>"):
        voecfgTestConfig()


def test_custom_coercion() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "voecfg_coerce"
        _coercions = {
            **BaseConfig._coercions,
            (str, int): int,
        }
        count: int = "42"  # type: ignore[assignment]

    config = voecfgTestConfig()
    assert config.count == 42
    assert isinstance(config.count, int)


def test_runtime_prefix_override() -> None:
    class voecfgTestConfig(BaseConfig):
        _prefix = "default"
        env1 = "fallback"

    config = voecfgTestConfig(prefix="voecfg")
    assert config.env1 == "959"
