from dataclasses import dataclass


@dataclass(frozen=True)
class ReferralRawData:
    referidos_directos_activos: int
    referidos_directos_inactivos: int


@dataclass(frozen=True)
class ReferralFeatures:
    referidos_directos_activos: int
    referidos_directos_inactivos: int
    referidos_directos_totales: int


def build_referral_features(raw_data: ReferralRawData) -> ReferralFeatures:
    return ReferralFeatures(
        referidos_directos_activos=raw_data.referidos_directos_activos,
        referidos_directos_inactivos=raw_data.referidos_directos_inactivos,
        referidos_directos_totales=_referidos_directos_totales(raw_data),
    )


def _referidos_directos_totales(raw_data: ReferralRawData) -> int:
    return raw_data.referidos_directos_activos + raw_data.referidos_directos_inactivos
