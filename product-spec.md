# Product Specification — Industrial Engineering Copilot

**Tagline:** From Engineering Requirements to Product Decisions

## Problem

Application engineers and sales engineers spend significant time translating unstructured customer RFQs into structured technical requirements, validating product specifications, and preparing evidence-backed recommendations. Manual catalog lookup is slow, error-prone, and difficult to audit.

## Solution

Industrial Engineering Copilot provides a structured workflow from RFQ intake to engineer-reviewed BOM and proposal draft. Technical validation is deterministic; LLM assistance is limited to extraction, explanation, and drafting with clear evidence links.

## Users

- Application engineers
- Sales engineers
- Panel builders and integrators
- Technical reviewers
- Catalog administrators
- Organization administrators

## Core workflow (target state)

1. Upload or create an RFQ
2. Extract and review structured requirements
3. Search and recommend products with PASS/FAIL/UNKNOWN validation
4. Validate compatibility across selected products
5. Build and approve a preliminary BOM
6. Generate and review a proposal draft
7. Audit all decisions with evidence

## Phase 1 deliverable

Phase 1 delivers the engineering foundation only:

- Runnable backend and frontend shells
- Tenant-ready organization/user/membership models
- PostgreSQL + pgvector infrastructure
- Health endpoints and CI
- Groq-only backend LLM foundation for future extraction and drafting workflows

No product catalog, RFQ analysis, or recommendation engine is included in Phase 1.

## LLM provider

Industrial Engineering Copilot uses **Groq only** for LLM capabilities. The backend reads `GROQ_API_KEY` from environment configuration; the frontend never receives the key. LLM output supports extraction and drafting, but deterministic specification validation and product decisions remain non-LLM.

## Non-goals

- Autonomous engineering sign-off
- ERP/CRM replacement
- Real manufacturer catalog licensing

## Branding

This application is branded exclusively as **Industrial Engineering Copilot**.
