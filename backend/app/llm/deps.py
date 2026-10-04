"""FastAPI dependencies for the LLM layer."""

from typing import Annotated

from fastapi import Depends

from app.llm import get_llm_client
from app.llm.groq_client import GroqLLMClient

LlmClient = Annotated[GroqLLMClient, Depends(get_llm_client)]
