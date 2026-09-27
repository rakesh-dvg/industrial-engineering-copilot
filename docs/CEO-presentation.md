# CEO Presentation — Industrial Engineering Copilot

## Problem

Engineering knowledge is disconnected from sales quotation workflows.

When a customer sends an RFQ, sales teams often depend on engineers to:

- interpret technical requirements
- compare products manually
- find supporting evidence
- decide whether a product truly fits
- calculate price and lead time
- remember to follow up after the quotation is sent

That handoff is slow, inconsistent, and hard to audit.

## Current pain

Sales needs engineering information to determine:

- **which product fits** the stated requirements
- **whether requirements are satisfied** (not just "similar")
- **what evidence supports** the recommendation
- **what price and lead time** to quote
- **when to follow up** after the quotation is sent

Today these steps often live in email threads, spreadsheets, and tribal knowledge.

## Solution

Industrial Engineering Copilot connects the engineering decision path to the sales execution path:

```text
RFQ
→ structured engineering requirements
→ validated products (PASS / FAIL / UNKNOWN)
→ evidence from datasheets
→ ranked recommendation
→ quotation
→ customer communication
→ sales follow-up queue
```

The AI helps **extract and explain**. The engineering compliance decision is **deterministic and auditable**.

## Business value

- **Faster quotation preparation** — requirements are structured immediately from customer text
- **Consistent engineering validation** — every product is checked the same way
- **Traceable technical evidence** — recommendations link to datasheet content
- **Reduced manual comparison** — PASS/FAIL/UNKNOWN is computed, not guessed
- **Better sales follow-up visibility** — prioritized open opportunities after quotations are sent
- **Connection between engineering data and sales execution** — the workflow does not stop at the PDF/email step

This MVP demonstrates the workflow with synthetic demo data. It is not a CRM replacement.

## Demo scenario

**Customer:** ABC Manufacturing

Sales receives an RFQ for industrial Ethernet switches, validates three candidate products, recommends the PASS product, generates a USD 1,850 quotation, simulates customer email, and surfaces follow-up opportunities alongside historical demo accounts.

## What this is not

- Not autonomous sales — a human selects the product and approves the quotation
- Not real email delivery — demo mode records sends without external delivery
- Not a CRM — follow-ups are demo/historical opportunities, not Salesforce records
