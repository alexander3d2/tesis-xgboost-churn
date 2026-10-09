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
    CsvSubscriptionExpirationRepository,
)
from app.training.dataset_builder import TrainingExampleBuilder
from app.training.feature_vector import FEATURE_COLUMNS, to_feature_vector
from app.training.monthly_cutoffs import generar_fechas_de_corte_mensuales

DEFAULT_DATASHEET_DIR = "Datasheet_anonimizado"
ULTIMA_FECHA_CORTE_VALIDA = date.today() - timedelta(days=HORIZONTE_PREDICCION_DIAS)


def cargar_payments(datasheet_dir: str) -> pd.DataFrame:
    payments = pd.read_csv(
        f"{datasheet_dir}/payments.csv",
        header=None,
        names=["idsuscription", "paydate", "quoteusd", "nextexpirationdate", "positiononschedule"],
        dtype={"idsuscription": str},
    )
    payments["paydate"] = pd.to_datetime(payments["paydate"], errors="coerce")
    payments["nextexpirationdate"] = pd.to_datetime(payments["nextexpirationdate"], errors="coerce")
    return payments


def cargar_suscripciones(datasheet_dir: str) -> pd.DataFrame:
    return pd.read_csv(
        f"{datasheet_dir}/suscripciones.csv",
        header=None,
        names=["idsuscription", "iduser"],
        dtype={"idsuscription": str, "iduser": str},
    )


def cargar_usuarios(datasheet_dir: str) -> pd.DataFrame:
    usuarios = pd.read_csv(
        f"{datasheet_dir}/usuarios.csv",
        header=None,
        names=["iduser", "createdate"],
        dtype={"iduser": str},
    )
    usuarios["createdate"] = pd.to_datetime(usuarios["createdate"], errors="coerce")
    return usuarios


def construir_builder(datasheet_dir: str) -> tuple[TrainingExampleBuilder, pd.DataFrame]:
    payments = cargar_payments(datasheet_dir)
    suscripciones = cargar_suscripciones(datasheet_dir)
    usuarios = cargar_usuarios(datasheet_dir)

    return TrainingExampleBuilder(
        affiliate_data_repository=CsvAffiliateDataRepository(payments, suscripciones, usuarios),
        subscription_expiration_repository=CsvSubscriptionExpirationRepository(payments, suscripciones),
    ), usuarios


def construir_fila(builder: TrainingExampleBuilder, affiliate_id: str, fecha_corte: date) -> dict | None:
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
        affiliate_id = usuario["iduser"]
        fecha_creacion = usuario["createdate"].date()
        for fecha_corte in generar_fechas_de_corte_mensuales(fecha_creacion, ULTIMA_FECHA_CORTE_VALIDA):
            fila = construir_fila(builder, affiliate_id, fecha_corte)
            if fila is not None:
                filas.append(fila)
        if indice % INTERVALO_REPORTE_AVANCE == 0:
            reportar_avance(indice, total_usuarios, inicio)
    return pd.DataFrame(filas)


def main(argv: list[str] | None = None):
    args = sys.argv[1:] if argv is None else argv
    datasheet_dir = args[0] if args else DEFAULT_DATASHEET_DIR
    builder, usuarios = construir_builder(datasheet_dir)
    dataset = construir_dataset(builder, usuarios)
    dataset.to_csv("dataset_entrenamiento.csv", index=False)
    print(f"Dataset generado: {len(dataset)} filas")


if __name__ == "__main__":
    main()
