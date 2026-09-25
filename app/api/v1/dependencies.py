from fastapi import Depends

from app.db import get_db
from app.repositories.risk_repository import RiskScoreRepository


def get_risk_repository(connection=Depends(get_db)) -> RiskScoreRepository:
    return RiskScoreRepository(connection)
