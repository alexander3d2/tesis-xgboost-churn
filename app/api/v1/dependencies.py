from fastapi import Depends

from app.db import get_results_db, get_source_db
from app.repositories.affiliate_data_repository import AffiliateDataRepository
from app.repositories.risk_repository import RiskScoreRepository


def get_risk_repository(connection=Depends(get_results_db)) -> RiskScoreRepository:
    return RiskScoreRepository(connection)


def get_affiliate_data_repository(connection=Depends(get_source_db)) -> AffiliateDataRepository:
    return AffiliateDataRepository(connection)
