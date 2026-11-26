# Lumen Trail Outfitters — Incident Response Runbook (Platform Engineering)

> Fictional company. All names, numbers and policies in this document are invented for testing a RAG system.

## 1. Severity levels

| Severity | Definition | Example | First response |
|---|---|---|---|
| **SEV1** | Checkout or payments down for all customers | Payment gateway returns errors for every order | **15 minutes**, 24/7 |
| **SEV2** | Major feature degraded, workaround exists | Search is slow (> 5 s) but works | **1 hour**, business hours |
| **SEV3** | Minor issue, few customers affected | A product image doesn't load | Next business day |

## 2. On-call

- On-call rotations last **one week**, starting Monday at 10:00.
- The on-call engineer must acknowledge a page within **5 minutes**. If not acknowledged, it escalates to the secondary on-call, then to the Head of Platform, **Andrés Vela**.
- On-call engineers receive an extra **COP 400,000** per week, plus one day off after any week with a SEV1 incident.

## 3. Running an incident

1. Open a channel in the chat tool named `#inc-YYYYMMDD-short-name`.
2. Assign roles: **Incident Commander** (coordinates, doesn't fix), **Ops lead** (fixes) and **Comms lead** (updates the status page).
3. For SEV1, update the public status page every **30 minutes**, even if there is no news.
4. Prefer **rollback** over a hotfix when the incident started after a deploy in the last 2 hours.
5. Close the incident only after the error rate stays under 1% for 30 minutes.

## 4. Postmortems

- A postmortem is mandatory for every SEV1 and SEV2, due within **5 business days**.
- Postmortems are **blameless**: they describe systems and decisions, not people.
- Each postmortem must have at least one action item with an owner and a due date.
- Postmortems are reviewed in the **Thursday reliability meeting**.

## 5. Change freeze

There is a deploy freeze during **Black Friday week** and from **December 20 to January 2**. Only SEV1 fixes are allowed, with approval from the Head of Platform.
