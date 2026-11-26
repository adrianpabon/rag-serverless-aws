# 0007. Cognito user pool with admin-only users

- **Status:** Accepted
- **Date:** 2026-11-26

## Context

The REST API (`/query`, `/upload-url`) must only be used by authenticated users. Amazon Cognito issues the JWT tokens that the API Gateway authorizer will validate. When the user pool is created, we have to decide **who can create accounts**, and how clients get tokens.

Every query calls Bedrock (Titan + Claude Haiku 4.5), and every upload triggers an ingestion job. Each request has a real cost, however small, so open access is a cost and abuse risk.

## Options considered

**Who can create users**

| Option | Pros | Cons |
|---|---|---|
| **Admin-only** (`AllowAdminCreateUserOnly`) | Only the owner creates users. No spam sign-ups, no email delivery setup. Full control over who can spend Bedrock budget. | Each new user must be created by hand (console or CLI). |
| Self sign-up with email verification | Anyone can create an account. More realistic for a public product. | Needs email delivery (Cognito's limited default sender or SES). Opens the API, and Bedrock costs, to strangers. Needs extra protections (WAF, quotas, CAPTCHA). |

**App client**

| Option | Pros | Cons |
|---|---|---|
| **Public client, no secret** | Works for browsers, SPAs and the CLI, which can't keep a secret. | Security relies on the user's password and short-lived tokens. |
| Confidential client with secret | Extra factor for server-side apps. | A secret can't be protected in a browser or a CLI script. |

## Decision

Use **admin-only users**. This is a laboratory, so it isn't necessary to open the application to everyone. When the lab is finished, everything will be deleted, so there is no need to allow sign-ups. And if I decide to leave it running, I don't want a lot of people signing up to my application.

Configuration:

- User pool `rag-serverless-users`, **Essentials** plan (free up to 10,000 monthly active users), sign-in with **email**, MFA off for the lab.
- App client `rag-serverless-client`: **public, no client secret**. Auth flows: `ALLOW_USER_SRP_AUTH`, `ALLOW_REFRESH_TOKEN_AUTH`, `ALLOW_USER_AUTH`, and `ALLOW_USER_PASSWORD_AUTH` **only for CLI tests in this lab**.
- Access and ID tokens valid for 60 minutes. Token revocation and "prevent user existence errors" enabled.
- Deletion protection enabled. It must be turned off before destroying the pool.

## Consequences

- ✅ Nobody outside my control can call the API or spend Bedrock budget.
- ✅ No email infrastructure to set up.
- ⚠️ `ALLOW_USER_PASSWORD_AUTH` sends the password to Cognito (over TLS) instead of using SRP. It's acceptable for lab tests, and it should be removed in production.
- ⚠️ MFA is off. Enable it before sharing the application with anyone.
- 🔁 If the application ever becomes public, a new ADR must cover self sign-up, email delivery (SES), WAF and per-user quotas.
