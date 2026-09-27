# Limitations and Future Roadmap

## CURRENT MVP

### Product and intelligence

- **Groq dependency** — RFQ extraction requires a Groq API key
- **Deterministic MVP embedding provider** — not a production semantic model
- **Synthetic demo catalog** — products and datasheets are seeded, not live supplier feeds
- **Demo/historical follow-ups** — Apex and Delta are fictional opportunities, not CRM records
- **Simulated email sending** — no real SMTP or customer email delivery
- **No real CRM integration** — no Salesforce, HubSpot, or ERP sync
- **No automated customer follow-up** — sales manually completes follow-ups in the UI
- **Client-side sales decision audit trail** — not a full enterprise audit log
- **No enterprise authentication / RBAC** — org models exist but auth is foundation-level only

### AWS deployment (Phase 10)

- **Single-region AWS MVP** — one region, one ALB, one task per service
- **No high availability** — single-AZ RDS, no Multi-AZ, no replicas
- **No autoscaling** — fixed Fargate task count
- **No production CI/CD** — manual image build and push
- **No automated infrastructure provisioning** — JSON task definition examples, not Terraform
- **No CloudFront / custom domain** — CEO opens the ALB DNS name directly
- **No WAF or advanced security hardening**
- **Cost not optimized for 24/7 production** — sized for demo; cleanup required after the meeting

### Operations

- **Manual database initialization** — Alembic + seeds run outside normal ECS service startup
- **Alembic is required** — schema is never created via `Base.metadata.create_all()` in deployment
- **AWS Free Tier / credits vary** — monitor the AWS Billing dashboard

---

## FUTURE

1. **Real CRM integration** — sync opportunities, accounts, and activities
2. **Real email integration** — SMTP or provider-backed customer delivery with approval gates
3. **PDF quotation generation** — customer-ready quotation documents
4. **Richer customer/contact history** — persistent CRM-like timeline
5. **Stronger semantic embeddings** — production embedding models and re-indexing pipeline
6. **Supplier/manufacturer data ingestion** — live catalog and datasheet feeds
7. **ERP integration** — pricing, inventory, and order flow
8. **Enterprise authentication / RBAC** — SSO, org roles, audit trails
9. **Production observability** — metrics, tracing, alerting beyond basic CloudWatch Logs
10. **Infrastructure as code** — Terraform or CloudFormation for reproducible environments
11. **Autoscaling and HA** — Multi-AZ RDS, multiple ECS tasks, health-based scaling
12. **Advanced analytics** — win rates, validation patterns, quotation cycle time
