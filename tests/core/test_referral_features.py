from app.core.referral_features import ReferralRawData, build_referral_features


def test_build_referral_features_computes_total_from_active_and_inactive():
    raw_data = ReferralRawData(referidos_directos_activos=3, referidos_directos_inactivos=2)

    features = build_referral_features(raw_data)

    assert features.referidos_directos_activos == 3
    assert features.referidos_directos_inactivos == 2
    assert features.referidos_directos_totales == 5


def test_build_referral_features_handles_no_referrals():
    raw_data = ReferralRawData(referidos_directos_activos=0, referidos_directos_inactivos=0)

    features = build_referral_features(raw_data)

    assert features.referidos_directos_totales == 0
