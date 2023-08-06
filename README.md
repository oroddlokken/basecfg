# voecfg / basecfg [0]
Minimal configuration management library for Python. Written in pure Python with no* dependencies. Runs on Python 3.6+.

`*`but it is supercharged with [python-dotenv](https://pypi.org/project/python-dotenv/) and [toml](https://pypi.org/project/toml/), and is tested with them.

## Features

Values are read in the following order (first to last):
- Defined in the class, useful for defaults.
- Defined in the config file provided to the class, useful for per-environment settings.
- Defined as environment variables. Use this for passwords and other sensitive values.

## Example usage
See [example/example_usage.py](example/example_usage.py) for a detailed example on how to use it.

But here is a simple example, with a nested config class (using SubConfig) with default and required values of various types.
```python
#!/usr/bin/env python3

"""Example usage of voecfg."""

from voecfg import BaseConfig, SubConfig


# Notice how we are inheriting from SubConfig instead of BaseConfig.
class DBConfig(SubConfig):
    """Database config."""

    # The environment variable prefix for this app,
    # rendered as DB_
    _prefix = "db"

    # This will read the environment variables as described in the comments below.
    host = "127.0.0.1"  # APP_DB_HOST
    port = 5432  # APP_DB_PORT
    user: str  # APP_DB_USER
    password: str  # APP_DB_PASSWORD
    database: str  # APP_DB_DATABASE
    tls = False  # APP_DB_TLS
    auto_commit: bool  # APP_DB_AUTOCOMMIT


class AppConfig(BaseConfig):
    """App config."""

    _prefix = "app"

    base_url = "http://localhost:8000"  # APP_BASE_URL

    db = DBConfig()


# Get an initialized config, including the subclasses.
app_config = AppConfig()
print(
    f"base_url: {app_config.base_url}, "
    f"host: {app_config.db.host}, port: {app_config.db.port}, "
    f"user: {app_config.db.user}, password: {app_config.db.password}, "
    f"database: {app_config.db.database}, tls: {app_config.db.tls}, "
    f"auto_commit: {app_config.db.auto_commit}"
)
```

Running the above file like  
 `APP_BASEURL="https://example.com" APP_DB_USER="test" APP_DB_PASSWORD="test" APP_DB_DATABASE="test" APP_DB_TLS=true APP_DB_AUTO_COMMIT=false python3 example/simple.py`  
will print  
`base_url: http://localhost:8000, host: 127.0.0.1, port: 5432, user: test, password: test, database: test, tls: True, auto_commit: False`.  
However, omitting one of the required environment variables will result in an error like `ValueError: Value for AppConfig.DBConfig.user / APP_DB_USER not set.`

Alternatively, install [python-dotenv](https://pypi.org/project/python-dotenv/), put the values in a .env file and have them loaded automatically with `from dotenv import load_dotenv` and `load_dotenv()`.

## Development
Setting up a dev environment locally with virtualenv:
```
virtualenv .venv
source .venv/bin/activate
pip3 install -r dev-requirements.txt -r requirements.txt
add2virtualenv .
```

Running black, isort and tox:
```
bash format_and_tox.sh # Runs black, isort and tox (black-check, isort-check, pydocstyle, mypy, ruff, vulture and bandit)
```

Running tests and coverage:
```
cd tests
make
```

Running tests, tox and setup.py in Python 3.6+ using Docker:
```
docker build -f Dockerfile.test -t voecfg-build-test .
```

##### [0] The library was originally called basecfg, but was later renamed since there is a similar project with that name.
