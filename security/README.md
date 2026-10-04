# Security documentation

Industrial Engineering Copilot security notes for reviewers and operators.

| Document | Topic |
|----------|--------|
| [agent-security.md](agent-security.md) | Agent tool boundaries |
| [ai-data-policy.md](ai-data-policy.md) | Groq data handling |
| [dependency-audit.md](dependency-audit.md) | How to run audits |
| [bandit-report.txt](bandit-report.txt) | Latest Bandit scan output (backend `app/`) |

Application auth is MVP-grade (`JWT_SECRET_KEY` placeholder). Production would add SSO and secret rotation.
