from fastapi import APIRouter

from app.api.v1 import (
    catalog,
    communication,
    documents,
    evidence,
    health,
    quotations,
    recommendations,
    rfq,
    sales,
    validation,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(catalog.router)
api_router.include_router(rfq.router)
api_router.include_router(validation.router)
api_router.include_router(recommendations.router)
api_router.include_router(documents.router)
api_router.include_router(evidence.router)
api_router.include_router(quotations.router)
api_router.include_router(communication.router)
api_router.include_router(sales.router)
