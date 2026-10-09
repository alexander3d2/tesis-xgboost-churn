from datetime import date

from app.core.wallet_activity_features import WalletActivityRawData, build_wallet_activity_features


def test_build_wallet_activity_features_computes_days_since_last_transaction():
    raw_data = WalletActivityRawData(
        last_transaction_date=date(2026, 8, 15),
        reference_date=date(2026, 9, 1),
    )

    features = build_wallet_activity_features(raw_data)

    assert features.dias_desde_ultima_transaccion_billetera == 17


def test_build_wallet_activity_features_returns_none_when_no_transactions():
    raw_data = WalletActivityRawData(
        last_transaction_date=None,
        reference_date=date(2026, 9, 1),
    )

    features = build_wallet_activity_features(raw_data)

    assert features.dias_desde_ultima_transaccion_billetera is None
