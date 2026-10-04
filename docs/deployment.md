# Deployment overview

## Current state (reviewer default)

**Run locally with Docker Compose.** No AWS resources are provisioned for this submission.

```powershell
cp .env.example .env
docker compose up -d postgres redis minio
cd backend
pip install -e ".[dev]"
alembic upgrade head
python -m app.seed.catalog
python -m app.seed.followups
python -m app.seed.documents
uvicorn app.main:app --reload --port 8020
```

Or use `.\scripts\start-local.ps1` and the two-terminal flow in [README](../README.md).

Production-like containers locally:

```powershell
docker compose -f docker-compose.prod.yml up --build
```

Frontend production image uses **`frontend/nginx.conf.template`** (envsubst for `BACKEND_API_URL`).

---

## Historical AWS MVP (completed, then decommissioned)

> **AWS infrastructure used for the demonstration has been decommissioned.** The repository remains locally reproducible using Docker Compose.

The team previously deployed:

```text
Docker build
    ↓
Amazon ECR (backend + frontend images)
    ↓
Amazon ECS on Fargate (backend + frontend tasks)
    ↓
Application Load Balancer (single public URL)
    ↓
Amazon RDS PostgreSQL (+ pgvector)
    ↓
Amazon S3 (private documents)
    ↓
AWS Secrets Manager (GROQ_API_KEY, DATABASE_URL, …)
    ↓
IAM roles + security groups
    ↓
Amazon CloudWatch Logs
```

Step-by-step guide (for learning/reference only): **[aws-mvp-deployment.md](aws-mvp-deployment.md)**

Example task definitions: [deploy/aws/](../deploy/aws/)

Diagram: [architecture.md](architecture.md)

After a successful ~45 second mobile demo recording, project-specific AWS resources were removed (ECS, ECR, RDS, secrets, log groups, IAM deployment role, NAT/ALB/EIPs, etc.). Only the default VPC remains in the AWS account.

## CI/CD

No automated deploy to AWS. GitHub Actions runs tests and build — [cicd.md](cicd.md).

## Pre-deploy validation hook

```powershell
.\agent-hooks\pre-deploy-validation.ps1
```

Validates Compose config, OpenAPI paths, and a pytest subset — **does not deploy**.
