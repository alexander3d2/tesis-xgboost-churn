from fastapi import APIRouter, Depends

from app.api.v1.dependencies import get_risk_repository
from app.exceptions import AffiliateScoreNotFoundError
from app.repositories.risk_repository import RiskScoreRepository
from app.schemas.risk_score import RiskScoreResponse

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("/{affiliate_id}", response_model=RiskScoreResponse)
def get_risk_score(
    affiliate_id: int,
    repository: RiskScoreRepository = Depends(get_risk_repository),
) -> RiskScoreResponse:
    """Consulta el score de riesgo más reciente de un afiliado.

    Lanza AffiliateScoreNotFoundError (mapeada a 404 en main.py) si el
    modelo todavía no calculó un score para este afiliado.
    """
    score = repository.get_latest_score(affiliate_id)
    if score is None:
        raise AffiliateScoreNotFoundError(affiliate_id)
    return RiskScoreResponse(**score)
