from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    status: str = Field(..., examples=["ok"])
    service: str
    version: str
    environment: str


class DependencyHealth(BaseModel):
    status: str = Field(..., examples=["ok", "degraded", "unavailable"])
    message: str | None = None


class ApiHealthResponse(BaseModel):
    status: str = Field(..., examples=["ok", "degraded"])
    service: str
    version: str
    environment: str
    dependencies: dict[str, DependencyHealth]
