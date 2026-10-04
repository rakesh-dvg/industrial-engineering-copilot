from fastapi import APIRouter

from app.auth.deps import DbSession
from app.config import get_settings
from app.schemas.health import ApiHealthResponse
from app.services.health import build_api_health

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=ApiHealthResponse)
async def api_health(session: DbSession) -> ApiHealthResponse:
    settings = get_settings()
    return await build_api_health(settings, session)
