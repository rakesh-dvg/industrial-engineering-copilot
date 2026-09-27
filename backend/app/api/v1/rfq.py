from fastapi import APIRouter

from app.llm.deps import LlmClient
from app.schemas.rfq import RfqExtractRequest, RfqExtractResponse
from app.services.rfq_extraction import extract_rfq_requirements

router = APIRouter(tags=["RFQ"])


@router.post("/rfqs/extract", response_model=RfqExtractResponse)
def extract_rfq(request: RfqExtractRequest, llm_client: LlmClient) -> RfqExtractResponse:
    return extract_rfq_requirements(request.raw_text, llm_client)
