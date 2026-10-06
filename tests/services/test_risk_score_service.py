from unittest.mock import Mock

from app.services.risk_score_service import RiskScoreService


def test_list_latest_scores_delegates_to_repository():
    repository = Mock()
    expected = ([{"affiliate_id": 1}], 1)
    repository.get_latest_scores.return_value = expected
    service = RiskScoreService(repository)

    result = service.list_latest_scores(limit=10, offset=2, order="asc")

    assert result == expected
    repository.get_latest_scores.assert_called_once_with(limit=10, offset=2, order="asc")
