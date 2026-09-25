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
    """BD de origen (dev_inclub / equivalente en producción). Solo lectura.

    Nunca se ejecutan migraciones (Alembic) contra esta base: es propiedad
    de InClub World, no del microservicio de esta tesis.
    """

    model_config = SettingsConfigDict(env_file=".env", env_prefix="SOURCE_DB_", extra="ignore")


class ResultsDbSettings(_DbSettings):
    """BD de resultados: propia del microservicio, lectura y escritura."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="RESULTS_DB_", extra="ignore")


@lru_cache
def get_source_db_settings() -> SourceDbSettings:
    """Se valida contra el entorno solo la primera vez que se usa, no al
    importar el módulo — así los endpoints que no tocan la BD (ej. /health)
    no requieren variables de conexión configuradas para poder ejecutarse."""
    return SourceDbSettings()


@lru_cache
def get_results_db_settings() -> ResultsDbSettings:
    return ResultsDbSettings()
