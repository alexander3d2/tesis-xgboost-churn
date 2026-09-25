from collections.abc import Generator

import psycopg

from app.config import ResultsDbSettings, SourceDbSettings, get_results_db_settings, get_source_db_settings


def _connect(settings: SourceDbSettings | ResultsDbSettings) -> psycopg.Connection:
    return psycopg.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.name,
        user=settings.user,
        password=settings.password,
        sslmode=settings.sslmode,
    )


def get_source_db() -> Generator[psycopg.Connection, None, None]:
    """Dependencia de FastAPI: conexión de solo lectura a la BD de origen (dev_inclub)."""
    conn = _connect(get_source_db_settings())
    try:
        yield conn
    finally:
        conn.close()


def get_results_db() -> Generator[psycopg.Connection, None, None]:
    """Dependencia de FastAPI: conexión a la BD de resultados propia del microservicio."""
    conn = _connect(get_results_db_settings())
    try:
        yield conn
    finally:
        conn.close()
