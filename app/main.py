from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import router as api_v1_router
from app.exceptions import AffiliateScoreNotFoundError

app = FastAPI(
    title="Detección temprana de deserción — InClub World",
    description=(
        "Prototipo de investigación (Seminario de Investigación II, UCSS). "
        "No es un servicio comercial ni procesa datos reales de producción."
    ),
    version="0.1.0",
)

app.include_router(api_v1_router)


@app.exception_handler(AffiliateScoreNotFoundError)
def handle_affiliate_score_not_found(request: Request, exc: AffiliateScoreNotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.get("/health", tags=["health"])
def health_check() -> dict:
    return {"status": "ok"}
