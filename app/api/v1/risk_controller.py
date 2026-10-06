from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.api.v1.dependencies import get_risk_repository
from app.exceptions import AffiliateScoreNotFoundError
from app.repositories.risk_repository import RiskScoreRepository
from app.schemas.risk_score import RiskScoreListResponse, RiskScoreResponse

router = APIRouter(prefix="/risk", tags=["risk"])


@router.get("", response_model=RiskScoreListResponse)
def list_risk_scores(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    order: Literal["asc", "desc"] = "desc",
    repository: RiskScoreRepository = Depends(get_risk_repository),
) -> RiskScoreListResponse:
    items, total = repository.get_latest_scores(limit=limit, offset=offset, order=order)
    return RiskScoreListResponse(items=items, limit=limit, offset=offset, total=total)


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
