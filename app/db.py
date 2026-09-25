from collections.abc import Generator

import psycopg

from app.config import get_settings


def get_db() -> Generator[psycopg.Connection, None, None]:
    """Dependencia de FastAPI: entrega una conexión a la BD de resultados y la cierra al terminar."""
    settings = get_settings()
    conn = psycopg.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.name,
        user=settings.user,
        password=settings.password,
        sslmode=settings.sslmode,
    )
    try:
        yield conn
    finally:
        conn.close()
