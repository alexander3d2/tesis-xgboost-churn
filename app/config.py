from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class _DbSettings(BaseSettings):
    host: str
    port: int
    name: str
    user: str
    password: str
    sslmode: str = "disable"


class SourceDbSettings(_DbSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SOURCE_DB_", extra="ignore")


class AdminDbSettings(_DbSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="ADMIN_DB_", extra="ignore")


class ResultsDbSettings(_DbSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="RESULTS_DB_", extra="ignore")


@lru_cache
def get_source_db_settings() -> SourceDbSettings:
    return SourceDbSettings()


@lru_cache
def get_admin_db_settings() -> AdminDbSettings:
    return AdminDbSettings()


@lru_cache
def get_results_db_settings() -> ResultsDbSettings:
    return ResultsDbSettings()
