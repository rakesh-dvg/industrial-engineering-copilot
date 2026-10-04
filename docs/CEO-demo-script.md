# CEO Demo Script (3–5 minutes)

Use the **Sales Dashboard** at `/` or `/sales`.

## 0:00–0:30 — Problem

> "Today, engineering information and sales quotation activity are often separated. Engineers validate products one way; sales quotes another way in email and spreadsheets. This prototype connects them into one workflow."

## 0:30–1:00 — RFQ

Paste the ABC Manufacturing demo RFQ:

```text
Customer: ABC Manufacturing

We need 10 industrial Ethernet switches.

Requirements:
- 24 VDC
- minimum 5 Ethernet ports
- DIN rail mounting
- Modbus TCP
- operating temperature down to -20°C
```

Click **Extract Requirements**. Show structured requirements extracted by Groq.

> "The AI reads the RFQ, but the engineering decision is not delegated to the model."

## 1:00–1:45 — Engineering validation

Run validation. Show:

| Product | Result |
|---------|--------|
| NS-SW-005 | **PASS** |
| VIS-SW-003 | **FAIL** (3 ports) |
| AC-SW-008 | **UNKNOWN** (missing min temp) |

> "PASS, FAIL, and UNKNOWN are deterministic rules — the same requirement always produces the same result."

## 1:45–2:15 — Evidence + recommendation

Show datasheet evidence for NS-SW-005.

Show recommendation:

```text
NS-SW-005
PASS
USD 185
14 days
5/5 evidence coverage
```

## 2:15–3:00 — Quotation

Accept the recommendation. Set quantity **10**. Generate quotation:

```text
Q-2026-0001
10 × USD 185 = USD 1,850
Technical compliance: PASS
Validity: 30 days | Lead time: 14 days
```

Approve the quotation.

## 3:00–3:30 — Customer communication

Show recipient:

```text
procurement@abcmanufacturing.example
```

Point out the badge:

```text
DEMO CUSTOMER — No external email will be sent
```

Send the simulated email.

> "This records the send for the demo. No real customer email is delivered."

## 3:30–4:00 — Sales follow-up

Show **Today's Sales Follow-ups**:

```text
3 Customers Need Attention Today

P0  Apex Manufacturing     Q-2026-0003   USD 8,450
P1  ABC Manufacturing      Q-2026-0001   USD 1,850
P2  Delta Automation       Q-2026-0002   USD 4,200

Open Quotation Value: USD 14,500
```

> "The system doesn't stop when the quotation is created. It gives sales a prioritized list of customers to contact today."

Optionally click **Contact Today** on one follow-up to show OPEN → COMPLETED.

## 4:00–4:30 — AWS (if deployed)

Open the public ALB URL in the browser.

> "This same workflow is running on AWS — one URL, containers on ECS, database on RDS. We don't need to explain the infrastructure; the business story is the same."

Keep this section brief unless the CEO asks technical questions.
