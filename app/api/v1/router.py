from fastapi import APIRouter

from app.api.v1 import risk_controller

router = APIRouter(prefix="/api/v1")
router.include_router(risk_controller.router)
