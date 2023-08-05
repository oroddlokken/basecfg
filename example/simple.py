#!/usr/bin/env python3

"""Example usage of basecfg."""

# ruff: noqa: T201

from basecfg import BaseConfig, SubConfig


# Notice how we are inheriting from SubConfig instead of BaseConfig.
class DBConfig(SubConfig):
    """Database config."""

    # The environment variable prefix for this app,
    # rendered as DB_
    _prefix = "db"

    # This will read the environment variables as described in the comments below.
    host = "127.0.0.1"  # DB_HOST
    port = 5432  # DB_PORT
    user: str  # DB_USER
    password: str  # DB_PASSWORD
    database: str  # DB_DATABASE
    tls = False  # DB_TLS
    auto_commit: bool  # DB_AUTOCOMMIT


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
