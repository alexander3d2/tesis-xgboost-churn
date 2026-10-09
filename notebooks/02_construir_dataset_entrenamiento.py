from datetime import date, timedelta

import pandas as pd
import psycopg

from app.config import get_admin_db_settings, get_source_db_settings
from app.core.horizon import HORIZONTE_PREDICCION_DIAS
from app.exceptions import AffiliateNotFoundError, PagosInsuficientesError, SinPagosRegistradosError
from app.repositories.affiliate_data_repository import AffiliateDataRepository
from app.repositories.referral_repository import ReferralRepository
from app.repositories.subscription_expiration_repository import SubscriptionExpirationRepository
from app.repositories.wallet_activity_repository import WalletActivityRepository
from app.training.dataset_builder import TrainingExampleBuilder
from app.training.feature_vector import FEATURE_COLUMNS, to_feature_vector
from app.training.monthly_cutoffs import generar_fechas_de_corte_mensuales

ULTIMA_FECHA_CORTE_VALIDA = date.today() - timedelta(days=HORIZONTE_PREDICCION_DIAS)


def _connect(settings) -> psycopg.Connection:
    return psycopg.connect(
        host=settings.host,
        port=settings.port,
        dbname=settings.name,
        user=settings.user,
        password=settings.password,
        sslmode=settings.sslmode,
    )


def obtener_usuarios_con_pagos_validos(source_conn: psycopg.Connection) -> list[tuple[int, date]]:
    with source_conn.cursor() as cursor:
        cursor.execute(
            """
            SELECT u.id, u.createdate
            FROM bo_account.user u
            JOIN bo_membership.suscription s ON s.iduser = u.id
            JOIN bo_membership.payment p ON p.idsuscription = s.idsuscription
            WHERE p.paydate > '2000-01-01'
            GROUP BY u.id, u.createdate
            """
        )
        return [(row[0], _a_date(row[1])) for row in cursor.fetchall()]


def _a_date(valor) -> date:
    return valor.date() if hasattr(valor, "date") else valor


def construir_fila(builder: TrainingExampleBuilder, affiliate_id: int, fecha_corte: date) -> dict | None:
    try:
        features = builder.build_features(affiliate_id, fecha_corte)
    except (SinPagosRegistradosError, PagosInsuficientesError, AffiliateNotFoundError):
        return None

    label = builder.build_label(affiliate_id, fecha_corte)
    fila = dict(zip(FEATURE_COLUMNS, to_feature_vector(features)))
    fila["affiliate_id"] = affiliate_id
    fila["fecha_corte"] = fecha_corte
    fila["desercion"] = label
    return fila


def construir_dataset(builder: TrainingExampleBuilder, usuarios: list[tuple[int, date]]) -> pd.DataFrame:
    filas = []
    for affiliate_id, fecha_creacion in usuarios:
        for fecha_corte in generar_fechas_de_corte_mensuales(fecha_creacion, ULTIMA_FECHA_CORTE_VALIDA):
            fila = construir_fila(builder, affiliate_id, fecha_corte)
            if fila is not None:
                filas.append(fila)
    return pd.DataFrame(filas)


def main():
    source_conn = _connect(get_source_db_settings())
    admin_conn = _connect(get_admin_db_settings())

    builder = TrainingExampleBuilder(
        affiliate_data_repository=AffiliateDataRepository(source_conn),
        wallet_activity_repository=WalletActivityRepository(source_conn),
        referral_repository=ReferralRepository(admin_conn),
        subscription_expiration_repository=SubscriptionExpirationRepository(source_conn),
    )

    usuarios = obtener_usuarios_con_pagos_validos(source_conn)
    dataset = construir_dataset(builder, usuarios)
    dataset.to_csv("dataset_entrenamiento.csv", index=False)

    source_conn.close()
    admin_conn.close()


if __name__ == "__main__":
    main()
