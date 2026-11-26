# Sample documents

Small test documents for the Knowledge Base. They describe a **fictional company**, Lumen Trail Outfitters, so the facts can't come from the model's training data: a correct answer proves that retrieval worked.

Upload them to `s3://<docs-bucket>/uploads/`. Never add copyrighted or confidential documents here.

| File | Topic |
|---|---|
| `01-employee-handbook.md` | Working hours, remote work, vacation, benefits |
| `02-returns-and-warranty-policy.md` | Returns, refunds, warranty, repairs |
| `03-incident-response-runbook.md` | Severity levels, on-call, postmortems |
| `04-product-guide-alpine-tents.md` | Tent models, specs, care, FAQ |
| `05-travel-expense-policy.md` | Travel booking, per diem, expense reports. Used to test uploads through `POST /upload-url`. |

## Test questions

Use them to check retrieval (`Retrieve`) and answers (`query_handler`).

| # | Question | Expected answer | Source |
|---|---|---|---|
| 1 | How many vacation days do employees get after 5 years? | 22 working days | 01 |
| 2 | How many days per week can office staff work remotely? | Up to 3 | 01 |
| 3 | How long do I have to return an unused product? | 45 days from delivery | 02 |
| 4 | What bonus do I get if I choose store credit? | 10% | 02 |
| 5 | What is the first response time for a SEV1? | 15 minutes, 24/7 | 03 |
| 6 | When is the deploy freeze at the end of the year? | December 20 to January 2 (also Black Friday week) | 03 |
| 7 | Which tent should I use on a glacier? | Nevado 2 or Cocuy 3 (4-season) | 04 |
| 8 | What's the lightest tent and how much does it weigh? | Páramo 1, 1.1 kg | 04 |
| 9 | Does the Cocuy 3 have a lifetime warranty? Why? | Yes, on seams, zippers and frames, because it's a Lumen Trail Pro product | 02 + 04 (multi-document) |
| 11 | What's the meal allowance per day for a trip to Europe? | USD 85 (hotel max USD 220) | 05 |
| 10 | What's the CEO's favorite color? | Not in the documents: the assistant should say it doesn't know | none (hallucination check) |
