from pydantic import BaseModel, ConfigDict, Field


class RiskScoreResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    affiliate_id: int = Field(..., description="Identificador del afiliado")
    risk_score: float = Field(..., ge=0, le=1, description="Probabilidad de deserción estimada por el modelo")
    risk_level: str = Field(..., description="Alto, Medio o Bajo")
    model_version: str
    scored_at: str
