import sys
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.horizon import HORIZONTE_PREDICCION_DIAS
from app.exceptions import AffiliateNotFoundError, PagosInsuficientesError, SinPagosRegistradosError
from app.training.csv_adapters import (
    CsvAffiliateDataRepository,
    CsvReferralRepository,
    CsvSubscriptionExpirationRepository,
    CsvWalletActivityRepository,
)
from app.training.dataset_builder import TrainingExampleBuilder
from app.training.feature_vector import FEATURE_COLUMNS, to_feature_vector
from app.training.monthly_cutoffs import generar_fechas_de_corte_mensuales

DATASHEET_DIR = "Datasheet"
ULTIMA_FECHA_CORTE_VALIDA = date.today() - timedelta(days=HORIZONTE_PREDICCION_DIAS)


def cargar_payments() -> pd.DataFrame:
    payments = pd.read_csv(
        f"{DATASHEET_DIR}/payments.csv",
        header=None,
        names=["idsuscription", "paydate", "quoteusd", "nextexpirationdate", "positiononschedule"],
    )
    payments["paydate"] = pd.to_datetime(payments["paydate"], errors="coerce")
    payments["nextexpirationdate"] = pd.to_datetime(payments["nextexpirationdate"], errors="coerce")
    return payments


def cargar_suscripciones() -> pd.DataFrame:
    return pd.read_csv(f"{DATASHEET_DIR}/suscripciones.csv", header=None, names=["idsuscription", "iduser"])


def cargar_usuarios() -> pd.DataFrame:
    usuarios = pd.read_csv(f"{DATASHEET_DIR}/usuarios.csv", header=None, names=["iduser", "createdate"])
    usuarios["createdate"] = pd.to_datetime(usuarios["createdate"], errors="coerce")
    return usuarios


def cargar_wallets() -> pd.DataFrame:
    return pd.read_csv(f"{DATASHEET_DIR}/wallets.csv", header=None, names=["idwallet", "iduser"])


def cargar_wallet_transacciones() -> pd.DataFrame:
    wallet_transacciones = pd.read_csv(
        f"{DATASHEET_DIR}/wallet_transacciones.csv", header=None, names=["idwallet", "initialdate"]
    )
    wallet_transacciones["initialdate"] = pd.to_datetime(wallet_transacciones["initialdate"], errors="coerce")
    return wallet_transacciones


def cargar_affiliate() -> pd.DataFrame:
    return pd.read_csv(f"{DATASHEET_DIR}/affiliate.csv", header=None, names=["idsponsor", "idson"])


def cargar_usercustomer() -> pd.DataFrame:
    return pd.read_csv(f"{DATASHEET_DIR}/usercustomer.csv", header=None, names=["iduser", "idstate"])


def construir_builder() -> TrainingExampleBuilder:
    payments = cargar_payments()
    suscripciones = cargar_suscripciones()
    usuarios = cargar_usuarios()
    wallets = cargar_wallets()
    wallet_transacciones = cargar_wallet_transacciones()
    affiliate = cargar_affiliate()
    usercustomer = cargar_usercustomer()

    return TrainingExampleBuilder(
        affiliate_data_repository=CsvAffiliateDataRepository(payments, suscripciones, usuarios),
        wallet_activity_repository=CsvWalletActivityRepository(wallets, wallet_transacciones),
        referral_repository=CsvReferralRepository(affiliate, usercustomer),
        subscription_expiration_repository=CsvSubscriptionExpirationRepository(payments, suscripciones),
    ), usuarios


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


INTERVALO_REPORTE_AVANCE = 500


def reportar_avance(usuarios_procesados: int, total_usuarios: int, inicio: float) -> None:
    transcurrido = time.time() - inicio
    porcentaje = usuarios_procesados / total_usuarios * 100
    por_usuario = transcurrido / usuarios_procesados
    restante_segundos = por_usuario * (total_usuarios - usuarios_procesados)
    print(
        f"{usuarios_procesados}/{total_usuarios} usuarios ({porcentaje:.1f}%) — "
        f"transcurrido {transcurrido / 60:.1f} min, restante estimado {restante_segundos / 60:.1f} min"
    )


def construir_dataset(builder: TrainingExampleBuilder, usuarios: pd.DataFrame) -> pd.DataFrame:
    filas = []
    inicio = time.time()
    total_usuarios = len(usuarios)
    for indice, (_, usuario) in enumerate(usuarios.iterrows(), start=1):
        affiliate_id = int(usuario["iduser"])
        fecha_creacion = usuario["createdate"].date()
        for fecha_corte in generar_fechas_de_corte_mensuales(fecha_creacion, ULTIMA_FECHA_CORTE_VALIDA):
            fila = construir_fila(builder, affiliate_id, fecha_corte)
            if fila is not None:
                filas.append(fila)
        if indice % INTERVALO_REPORTE_AVANCE == 0:
            reportar_avance(indice, total_usuarios, inicio)
    return pd.DataFrame(filas)


def main():
    builder, usuarios = construir_builder()
    dataset = construir_dataset(builder, usuarios)
    dataset.to_csv("dataset_entrenamiento.csv", index=False)
    print(f"Dataset generado: {len(dataset)} filas")


if __name__ == "__main__":
    main()
