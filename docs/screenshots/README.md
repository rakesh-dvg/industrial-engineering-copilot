# Demo Screenshots

Automated screenshot capture was not run against a live AWS deployment from this repository.

Capture these screenshots **manually** after the application is running locally or on AWS.

## Required screenshots

| # | Filename (suggested) | What to capture |
|---|----------------------|-----------------|
| 1 | `01-sales-dashboard.png` | Sales Dashboard landing / workflow stepper |
| 2 | `02-rfq-requirements.png` | ABC Manufacturing RFQ pasted and extracted requirements |
| 3 | `03-validation-pass-fail-unknown.png` | Validation results: NS-SW-005 PASS, VIS-SW-003 FAIL, AC-SW-008 UNKNOWN |
| 4 | `04-recommendation.png` | NS-SW-005 recommended with PASS, USD 185, 14 days, evidence coverage |
| 5 | `05-quotation.png` | Quotation Q-2026-0001, 10 units, USD 1,850 total, technical PASS |
| 6 | `06-customer-communication.png` | Email to `procurement@abcmanufacturing.example` with **DEMO CUSTOMER** badge |
| 7 | `07-sales-follow-ups.png` | Today's follow-ups: P0/P1/P2 and Open Quotation Value USD 14,500 |
| 8 | `08-aws-hosted-app.png` | Browser showing the ALB DNS name with the app loaded (AWS only) |

## Capture tips

- Use the demo RFQ from [CEO-demo-script.md](../CEO-demo-script.md).
- Run seeds before capture so Apex/Delta follow-ups appear; complete the live workflow send to add ABC Manufacturing.
- Do **not** include real API keys, passwords, or Secrets Manager values in screenshots.
- For the AWS screenshot, show only the public ALB URL — no need to expose the AWS Console.
