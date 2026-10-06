from app.repositories.risk_repository import RiskScoreRepository


class RiskScoreService:
    """Application service for reading the latest risk scores."""

    def __init__(self, repository: RiskScoreRepository) -> None:
        self._repository = repository

    def list_latest_scores(
        self, limit: int, offset: int, order: str
    ) -> tuple[list[dict], int]:
        return self._repository.get_latest_scores(
            limit=limit,
            offset=offset,
            order=order,
        )
