from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.v1.router import api_router
from app.config import get_settings
from app.schemas.health import HealthStatus
from app.services.health import build_health_status


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="From Engineering Requirements to Product Decisions.",
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    root_router = APIRouter()

    @root_router.get("/health", response_model=HealthStatus, tags=["Health"])
    async def root_health() -> HealthStatus:
        return build_health_status(settings)

    app.include_router(root_router)
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
