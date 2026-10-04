# Technical Decisions

## PostgreSQL is the source of structured product truth

Manufacturers, categories, products, specifications, and pricing live in PostgreSQL. The catalog is queryable, org-scoped, and validated against canonical spec keys. LLM output never becomes the product record.

## Deterministic validation is authoritative

Engineering compliance is computed as **PASS**, **FAIL**, or **UNKNOWN** from structured requirements and normalized units. Groq extracts requirements; it does not decide compliance.

## LLM is used for extraction, explanation, and drafting

Groq handles RFQ understanding, communication drafts, and natural-language tasks. It is not the decision engine for validation, recommendation eligibility, or quotation approval.

## RAG provides evidence, not overrides

Datasheet chunks are embedded and retrieved to support recommendations and sales review. Evidence supplements structured specs; it does not replace PASS/FAIL/UNKNOWN rules.

## Recommendation is deterministic

Only PASS products are eligible. Ranking uses transparent factors (evidence coverage, price, lead time). Human sales selects the product before quotation.

## Quotation requires PASS

FAIL and UNKNOWN products are blocked at quotation creation. Commercial calculation uses catalog pricing snapshots deterministically.

## Email is simulated in the MVP

Customer sends are recorded in the database without external delivery. This preserves the demo workflow without CRM or SMTP integration.

## AWS deployment is intentionally minimal

The CEO demo requires a credible public URL, not enterprise infrastructure. One ALB, two Fargate services, one RDS instance, one S3 bucket, and Secrets Manager keep cost and complexity low.

## ECS Fargate instead of Kubernetes

Fargate removes cluster management overhead for a two-container MVP. EKS would add cost and operational burden without improving the demo story.

## RDS instead of PostgreSQL in ECS

Managed PostgreSQL provides durable storage, backups (AWS defaults), and pgvector support without operating database containers on Fargate.

## S3 for document storage

The existing MinIO-compatible client works with AWS S3 via environment configuration. Documents and ingested datasheets use a private bucket — no public object access.

## Alembic for all deployed schema changes

Local tests may use `create_all()` in pytest fixtures, but local, Docker, and AWS environments apply schema through `alembic upgrade head`. Seeds never create tables.

## Frontend same-origin API calls on AWS

The production frontend build uses an empty `VITE_API_BASE_URL`. The ALB routes `/api/*` to the backend so the CEO opens one URL.
