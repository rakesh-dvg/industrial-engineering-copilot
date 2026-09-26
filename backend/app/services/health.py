from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.schemas.health import ApiHealthResponse, DependencyHealth, HealthStatus


async def check_database(session: AsyncSession) -> DependencyHealth:
    try:
        await session.execute(text("SELECT 1"))
        return DependencyHealth(status="ok")
    except Exception as exc:  # noqa: BLE001 - health check should capture all failures
        return DependencyHealth(status="unavailable", message=str(exc))


def build_health_status(settings: Settings) -> HealthStatus:
    return HealthStatus(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )


async def build_api_health(settings: Settings, session: AsyncSession) -> ApiHealthResponse:
    database = await check_database(session)
    overall_status = "ok" if database.status == "ok" else "degraded"

    return ApiHealthResponse(
        status=overall_status,
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        dependencies={"database": database},
    )
