from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración centralizada, cargada desde variables de entorno (.env)."""

    model_config = SettingsConfigDict(env_file=".env", env_prefix="DB_", extra="ignore")

    host: str
    port: int
    name: str
    user: str
    password: str
    sslmode: str = "disable"


@lru_cache
def get_settings() -> Settings:
    """Se valida contra el entorno solo la primera vez que se usa, no al
    importar el módulo — así los endpoints que no tocan la BD (ej. /health)
    no requieren variables de conexión configuradas para poder ejecutarse."""
    return Settings()
