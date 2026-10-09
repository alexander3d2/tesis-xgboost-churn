from collections.abc import Generator

import psycopg

from app.config import (
    AdminDbSettings,
    ResultsDbSettings,
    SourceDbSettings,
    get_admin_db_settings,
    get_results_db_settings,
    get_source_db_settings,
)


def _connect(settings: SourceDbSettings | AdminDbSettings | ResultsDbSettings) -> psycopg.Connection:
    return psycopg.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.name,
        user=settings.user,
        password=settings.password,
        sslmode=settings.sslmode,
    )


def get_source_db() -> Generator[psycopg.Connection, None, None]:
    conn = _connect(get_source_db_settings())
    try:
        yield conn
    finally:
        conn.close()


def get_admin_db() -> Generator[psycopg.Connection, None, None]:
    conn = _connect(get_admin_db_settings())
    try:
        yield conn
    finally:
        conn.close()


def get_results_db() -> Generator[psycopg.Connection, None, None]:
    conn = _connect(get_results_db_settings())
    try:
        yield conn
    finally:
        conn.close()
