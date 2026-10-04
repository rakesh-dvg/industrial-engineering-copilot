# AI data policy (Groq)

## What is sent to Groq

- RFQ **raw text** for structured requirement extraction (`POST /api/v1/rfqs/extract`)
- Prompt context defined in `app/llm/prompts/` for extraction and communication **drafting**

Groq is configured **backend-only** via `GROQ_API_KEY`, `GROQ_MODEL`, `GROQ_BASE_URL`.

## What must NOT be sent

- Production database credentials or JWT secrets
- Unnecessary personal data beyond what the RFQ already contains
- Full datasheet corpora in a single prompt (use retrieval/evidence APIs instead)
- Instructions that ask the model to override PASS/FAIL/UNKNOWN

## Customer-sensitive handling

- Treat RFQ and uploaded documents as **untrusted input** (prompt injection aware).
- Simulated email in MVP — no external SMTP; still avoid logging full PII in CloudWatch in production.
- Historical AWS deployment stored `GROQ_API_KEY` in Secrets Manager, not in images.

## Output validation

- LLM JSON for extraction is parsed and validated with Pydantic schemas.
- Validation, recommendation, and quotation **never** trust model text for compliance — see `app/services/validation.py` and architecture invariant tests.

## Human approval

Sales reviews extracted requirements, selects products, approves quotations, and confirms send.
