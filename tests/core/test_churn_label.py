from app.core.churn_label import is_subscription_churned, is_user_churned


def test_is_subscription_churned_true_beyond_180_days():
    assert is_subscription_churned(dias_desde_vencimiento=181) is True


def test_is_subscription_churned_false_at_exactly_180_days():
    assert is_subscription_churned(dias_desde_vencimiento=180) is False


def test_is_subscription_churned_false_when_not_overdue():
    assert is_subscription_churned(dias_desde_vencimiento=-10) is False


def test_is_subscription_churned_false_when_no_expiration_info():
    assert is_subscription_churned(dias_desde_vencimiento=None) is False


def test_is_user_churned_true_when_at_least_one_subscription_churned():
    assert is_user_churned([10, 200, None]) is True


def test_is_user_churned_false_when_no_subscription_churned():
    assert is_user_churned([10, None, 90]) is False


def test_is_user_churned_false_when_no_subscriptions():
    assert is_user_churned([]) is False
