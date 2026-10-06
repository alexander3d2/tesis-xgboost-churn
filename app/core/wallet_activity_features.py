from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class WalletActivityRawData:
    last_transaction_date: date | None
    reference_date: date


@dataclass(frozen=True)
class WalletActivityFeatures:
    dias_desde_ultima_transaccion_billetera: int | None


def build_wallet_activity_features(raw_data: WalletActivityRawData) -> WalletActivityFeatures:
    return WalletActivityFeatures(
        dias_desde_ultima_transaccion_billetera=_dias_desde_ultima_transaccion(raw_data)
    )


def _dias_desde_ultima_transaccion(raw_data: WalletActivityRawData) -> int | None:
    if raw_data.last_transaction_date is None:
        return None
    return (raw_data.reference_date - raw_data.last_transaction_date).days
