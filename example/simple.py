#!/usr/bin/env python3

"""Example usage of voecfg."""

# ruff: noqa: T201

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
