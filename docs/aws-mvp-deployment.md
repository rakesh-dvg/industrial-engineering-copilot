# AWS MVP Deployment Guide

> **AWS infrastructure used for the demonstration has been decommissioned.** The repository remains locally reproducible using Docker Compose. This guide is retained as evidence of the completed deployment learning objective — do **not** recreate resources unless you own the AWS account and accept the cost.

Minimum AWS deployment for the Industrial Engineering Copilot CEO demo.

**Goal:** one public URL where the CEO can run the full sales workflow.

**Not included:** Kubernetes, Terraform, CI/CD, CloudFront, Route 53, Multi-AZ, autoscaling.

---

## A. Architecture

Seven AWS services:

| Service | Role |
|---------|------|
| **ECR** | Store `industrial-engineering-copilot-backend` and `industrial-engineering-copilot-frontend` images |
| **ECS Fargate** | Run backend (FastAPI) and frontend (Nginx) tasks |
| **Application Load Balancer** | Single public HTTP entry point |
| **RDS PostgreSQL** | Database with pgvector extension |
| **S3** | Private bucket for datasheets/documents |
| **Secrets Manager** | `GROQ_API_KEY`, `DATABASE_URL`, S3 credentials |
| **CloudWatch Logs** | `/ecs/industrial-engineering-copilot/backend` and `/frontend` |

```text
Internet → ALB → Frontend (/) + Backend (/api/*)
                      Backend → RDS, S3, Secrets Manager, Groq API
                      ECS → CloudWatch Logs
```

See [architecture.md](architecture.md) for the Mermaid diagram.

Example task definitions: [deploy/aws/](../deploy/aws/).

---

## B. Prerequisites

- AWS account with permissions for ECR, ECS, EC2 (for ALB), RDS, S3, IAM, Secrets Manager, CloudWatch Logs
- [AWS CLI v2](https://aws.amazon.com/cli/) configured (`aws configure`)
- Docker Desktop (or Docker Engine)
- Git
- Groq API key (stored only in Secrets Manager — never in Git)

Verify credentials:

```powershell
aws sts get-caller-identity
```

---

## C. AWS region

Use **one region** consistently. Examples below use:

```text
AWS_REGION=us-east-1
```

Replace with your chosen region in every command.

```powershell
$env:AWS_REGION = "us-east-1"
$env:AWS_ACCOUNT_ID = (aws sts get-caller-identity --query Account --output text)
```

---

## D. ECR setup

Create two repositories:

```powershell
aws ecr create-repository --repository-name industrial-engineering-copilot-backend --region $env:AWS_REGION
aws ecr create-repository --repository-name industrial-engineering-copilot-frontend --region $env:AWS_REGION
```

Authenticate Docker to ECR:

```powershell
aws ecr get-login-password --region $env:AWS_REGION | docker login --username AWS --password-stdin "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com"
```

---

## E. Docker build

From the repository root:

**Backend:**

```powershell
docker build -t industrial-engineering-copilot-backend ./backend
```

**Frontend** (empty `VITE_API_BASE_URL`; nginx proxies `/api/*` to `BACKEND_API_URL`):

```powershell
docker build -t industrial-engineering-copilot-frontend --target production --build-arg VITE_API_BASE_URL= ./frontend
docker run --rm -p 8080:80 -e BACKEND_API_URL=http://<backend-host>:8000 industrial-engineering-copilot-frontend
```

With an ALB, route `/api/*` to the backend instead of setting `BACKEND_API_URL`. Direct ECS public IPs are ephemeral — update `BACKEND_API_URL` and restart the frontend when the backend address changes.

Verify locally (optional):

```powershell
docker run --rm -p 8000:8000 industrial-engineering-copilot-backend
curl http://localhost:8000/health
```

---

## F. Push images

```powershell
$BACKEND_URI = "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com/industrial-engineering-copilot-backend:latest"
$FRONTEND_URI = "$env:AWS_ACCOUNT_ID.dkr.ecr.$env:AWS_REGION.amazonaws.com/industrial-engineering-copilot-frontend:latest"

docker tag industrial-engineering-copilot-backend:latest $BACKEND_URI
docker tag industrial-engineering-copilot-frontend:latest $FRONTEND_URI

docker push $BACKEND_URI
docker push $FRONTEND_URI
```

---

## G. RDS setup

### Requirements

- **Engine:** PostgreSQL 16 (or 15.2+ with pgvector support)
- **Deployment:** Single-AZ
- **Instance:** smallest eligible for your account (e.g. `db.t4g.micro` or `db.t3.micro`)
- **Storage:** 20 GB gp3 (minimum practical)
- **Multi-AZ:** off
- **Public access:** off
- **Database name:** `iec`
- **Master username:** e.g. `iec_admin`

### pgvector

The application migration `001_initial_foundation` runs:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Use an RDS PostgreSQL version that supports the pgvector extension in your region. After RDS is available, connect from a bastion or one-off ECS task and confirm:

```sql
SELECT extname FROM pg_extension WHERE extname = 'vector';
```

### Security group

Allow inbound **5432** only from the ECS task security group.

### Connection strings (store in Secrets Manager — not in Git)

```text
DATABASE_URL=postgresql+asyncpg://iec_admin:<password>@<rds-endpoint>:5432/iec
DATABASE_URL_SYNC=postgresql+psycopg://iec_admin:<password>@<rds-endpoint>:5432/iec
```

---

## H. S3 setup

Create one **private** bucket:

```powershell
aws s3 mb s3://iec-documents-<unique-suffix> --region $env:AWS_REGION
aws s3api put-public-access-block --bucket iec-documents-<unique-suffix> --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

Backend environment (also in task definition):

```text
MINIO_ENDPOINT=s3.us-east-1.amazonaws.com
MINIO_BUCKET=iec-documents-<unique-suffix>
MINIO_SECURE=true
```

The application uses the MinIO Python client against S3-compatible endpoints. Create an IAM user or task role policy with `s3:PutObject`, `s3:GetObject`, `s3:ListBucket` on this bucket only.

---

## I. Secrets Manager

Create secrets (replace placeholders — **never commit real values**):

| Secret name | Example key | Value shape |
|-------------|-------------|-------------|
| `iec/database-url` | — | `postgresql+asyncpg://...` |
| `iec/database-url-sync` | — | `postgresql+psycopg://...` |
| `iec/groq-api-key` | — | Groq API key string |
| `iec/s3-access-key` | — | IAM access key ID |
| `iec/s3-secret-key` | — | IAM secret access key |

```powershell
aws secretsmanager create-secret --name iec/groq-api-key --secret-string "REPLACE_ME" --region $env:AWS_REGION
```

Grant the ECS task **execution role** permission to read these secrets (`secretsmanager:GetSecretValue`).

The frontend task definition has **no secrets** and never receives `GROQ_API_KEY`.

---

## J. ECS setup

### Cluster

```powershell
aws ecs create-cluster --cluster-name industrial-engineering-copilot --region $env:AWS_REGION
```

### CloudWatch log groups

```powershell
aws logs create-log-group --log-group-name /ecs/industrial-engineering-copilot/backend --region $env:AWS_REGION
aws logs create-log-group --log-group-name /ecs/industrial-engineering-copilot/frontend --region $env:AWS_REGION
```

### Task definitions

Copy and edit:

- [deploy/aws/ecs-backend-task-definition.json.example](../deploy/aws/ecs-backend-task-definition.json.example)
- [deploy/aws/ecs-frontend-task-definition.json.example](../deploy/aws/ecs-frontend-task-definition.json.example)

Replace `<AWS_ACCOUNT_ID>`, `<AWS_REGION>`, `<S3_BUCKET_NAME>`, `<ALB_DNS_NAME>`, and secret ARNs.

Register:

```powershell
aws ecs register-task-definition --cli-input-json file://deploy/aws/ecs-backend-task-definition.json
aws ecs register-task-definition --cli-input-json file://deploy/aws/ecs-frontend-task-definition.json
```

### Task sizing (MVP)

| Service | CPU | Memory |
|---------|-----|--------|
| Backend | 512 | 1024 |
| Frontend | 256 | 512 |

No autoscaling. Desired count: **1** per service.

### Services

Create two Fargate services in **awsvpc** mode:

- `iec-backend` — backend target group, port 8000
- `iec-frontend` — frontend target group, port 80

Assign public subnets with **assignPublicIp=ENABLED** only if you are not using a NAT gateway and tasks need outbound internet (Groq API). This is the simplest MVP networking pattern; restrict security groups tightly.

Set `CORS_ORIGINS` on the backend to the ALB URL once known:

```text
["http://<alb-dns-name>"]
```

---

## K. Application Load Balancer

### Target groups

| Name | Port | Health check path | Expected |
|------|------|-------------------|----------|
| `iec-backend-tg` | 8000 | `/health` | HTTP 200 |
| `iec-frontend-tg` | 80 | `/health` | HTTP 200 |

Backend health is **process liveness** (`GET /health`). Database status is available at `GET /api/v1/health` for manual checks — do not use the DB-aware endpoint for aggressive ALB polling.

### Listener rules

1. **Default action:** forward to `iec-frontend-tg`
2. **Priority rule:** path `/api/*` → forward to `iec-backend-tg`

Also route `/openapi.json`, `/docs`, and `/redoc` to the backend if you want API docs on the same URL (optional):

- `/docs*`, `/redoc*`, `/openapi.json` → backend

### Public URL

After creation, note the ALB DNS name:

```text
http://<alb-dns-name>
```

This is the CEO demo URL. No custom domain required.

Rebuild/redeploy the frontend with `VITE_API_BASE_URL=` (empty) so API calls use same-origin paths.

---

## L. CloudWatch

Logs appear under:

```text
/ecs/industrial-engineering-copilot/backend
/ecs/industrial-engineering-copilot/frontend
```

Console: **CloudWatch → Log groups → /ecs/industrial-engineering-copilot/**

No Container Insights or custom metrics required for the MVP.

---

## M. Database initialization

Run **before** or **immediately after** first backend deploy. Do **not** use `Base.metadata.create_all()`.

### Option 1 — From your workstation (if RDS reachable)

```powershell
cd backend
$env:DATABASE_URL_SYNC = "<from-secrets-manager>"
alembic upgrade head
$env:DATABASE_URL = "<async-url-from-secrets-manager>"
python -m app.seed.catalog
python -m app.seed.followups
python -m app.seed.documents
```

### Option 2 — One-off ECS task (recommended for private RDS)

Run a Fargate task using the **backend image** with command override:

```text
alembic upgrade head && python -m app.seed.catalog && python -m app.seed.followups && python -m app.seed.documents
```

Use the same secrets and environment as the backend service task definition.

### Seed order

```text
1. alembic upgrade head
2. python -m app.seed.catalog
3. python -m app.seed.followups
4. python -m app.seed.documents
```

All seeds are idempotent.

### Demo data preserved

- Products NS-SW-005, VIS-SW-003, AC-SW-008
- Validation: PASS / FAIL / UNKNOWN
- Follow-ups: Apex (P0), ABC from live workflow (P1), Delta (P2)
- Simulated email to `procurement@abcmanufacturing.example`

---

## N. Verification

### Infrastructure

```powershell
aws ecs describe-services --cluster industrial-engineering-copilot --services iec-backend iec-frontend
curl http://<alb-dns-name>/health          # frontend nginx
curl http://<alb-dns-name>/api/v1/health   # backend + database
```

### CEO smoke test

1. Open `http://<alb-dns-name>`
2. Paste ABC Manufacturing demo RFQ → extract requirements
3. Validate → confirm PASS / FAIL / UNKNOWN
4. Show evidence and recommendation (NS-SW-005)
5. Generate quotation → USD 1,850 → approve
6. Customer email → confirm DEMO badge → simulated send
7. Follow-ups → P0/P1/P2, USD 14,500 open value
8. CloudWatch → confirm backend/frontend log streams
9. RDS → confirm `products`, `quotations`, `sales_follow_ups` rows
10. S3 → confirm datasheet objects after document seed

Do not claim deployment success until these checks pass in **your** AWS account.

---

## O. Cleanup (after CEO demo)

Stop ongoing charges. Order may vary; verify in the AWS Console Billing page.

1. **ECS services** — set desired count to 0, then delete services
2. **ALB** — delete listener, target groups, then load balancer
3. **RDS** — delete instance (skip final snapshot for disposable demo, or take one if you need to preserve data)
4. **NAT Gateway** (if created) — delete; this often dominates cost
5. **ECR** — delete images, then repositories (optional)
6. **S3** — empty and delete bucket
7. **Secrets Manager** — delete secrets (scheduled recovery window applies)
8. **CloudWatch Logs** — delete log groups
9. **ECS cluster** — delete after services are gone
10. **Security groups / IAM roles** — remove demo-specific resources

```powershell
# Example: scale down ECS services
aws ecs update-service --cluster industrial-engineering-copilot --service iec-backend --desired-count 0
aws ecs update-service --cluster industrial-engineering-copilot --service iec-frontend --desired-count 0
```

**Free Tier / credits:** eligibility varies by account, region, and service. Monitor **AWS Billing → Free Tier** and set a billing alarm before the demo.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Seed fails: missing tables | Migrations not run | `alembic upgrade head` on RDS |
| Frontend loads, API 404 | ALB rule missing | Add `/api/*` → backend target group |
| CORS errors | Wrong `CORS_ORIGINS` | Set to `http://<alb-dns-name>` |
| Groq errors | Missing/invalid secret | Check `iec/groq-api-key` in Secrets Manager |
| Document ingest fails | S3 permissions or endpoint | Verify `MINIO_*` env vars and IAM policy |
| pgvector error on migrate | RDS version/extension | Use PostgreSQL 16 + pgvector support |

For local development and reset procedures, see the [README](../README.md) and `scripts/reset-demo.ps1`.
