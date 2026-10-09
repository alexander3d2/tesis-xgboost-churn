import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.environ["DB_HOST"],
    "port": os.environ["DB_PORT"],
    "dbname": os.environ["DB_NAME"],
    "user": os.environ["DB_USER"],
    "password": os.environ["DB_PASSWORD"],
    "sslmode": os.environ.get("DB_SSLMODE", "disable"),
}

ESQUEMAS_DE_INTERES = ["bo_account", "bo_membership", "bo_commissions", "bo_wallet"]


def listar_tablas_y_columnas(conn, esquema):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            ORDER BY table_name
            """,
            (esquema,),
        )
        tablas = [row[0] for row in cur.fetchall()]

        for tabla in tablas:
            cur.execute(
                """
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
                """,
                (esquema, tabla),
            )
            columnas = cur.fetchall()

            cur.execute(f'SELECT COUNT(*) FROM "{esquema}"."{tabla}"')
            (conteo,) = cur.fetchone()

            print(f"\n  {esquema}.{tabla}  ({conteo} filas)")
            for nombre_columna, tipo in columnas:
                print(f"    - {nombre_columna}: {tipo}")


def main():
    with psycopg.connect(**DB_CONFIG) as conn:
        for esquema in ESQUEMAS_DE_INTERES:
            print(f"\n=== Esquema: {esquema} ===")
            listar_tablas_y_columnas(conn, esquema)


if __name__ == "__main__":
    main()
