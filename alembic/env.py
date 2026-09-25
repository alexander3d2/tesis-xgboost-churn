from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

from app.config import get_results_db_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _build_db_url() -> str:
    # Deliberadamente solo la BD DE RESULTADOS (propia del microservicio).
    # Alembic nunca debe correr migraciones contra la BD de origen
    # (dev_inclub / producción): esa base es propiedad de InClub World y
    # esta tesis solo la lee, nunca modifica su esquema.
    settings = get_results_db_settings()
    return (
        f"postgresql+psycopg://{settings.user}:{settings.password}"
        f"@{settings.host}:{settings.port}/{settings.name}"
    )


# La URL nunca se escribe en alembic.ini: se arma en tiempo de ejecución
# a partir de las variables de entorno (.env, no versionado).
config.set_main_option("sqlalchemy.url", _build_db_url())

target_metadata = None


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
