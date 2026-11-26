# 0005. Use Claude Haiku 4.5 as the generation model

- **Status:** Accepted
- **Date:** 2026-11-25
- **Supersedes:** [0004](0004-use-claude-haiku-5-5-for-generation.md)

## Context

[ADR 0004](0004-use-claude-haiku-5-5-for-generation.md) chose Claude Haiku 5.5 as the model that `query_handler` calls through the Bedrock Converse API. Its reasoning still holds: the lab tests the RAG pipeline, not the model, so a fast and cheap model is the right fit.

After the Bedrock access review of this new account, AWS enabled Bedrock in us-east-1 with **reduced quotas**, and warned that *"some higher-tier foundation models may not be available at this access level"*. Checked on 2026-11-25:

| Model | Applied quota | Test call |
|---|---|---|
| Claude Haiku 5.5 | 0 (quota request case closed) | `AccessDeniedException: anthropic.claude-haiku-5-5 is not available for this account` |
| Claude Haiku 4.5 | 10 requests/min, 5,000,000 tokens/min (cross-region) | OK |

Getting Haiku 5.5 would require contacting AWS Sales, with no clear timeline. That would block the `query_handler` Lambda.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **Claude Haiku 4.5** (`us.anthropic.claude-haiku-4-5-20251001-v1:0`) | Available now. Same role and profile as Haiku 5.5: fast, cheap, enough for answering from retrieved chunks. Already used in production at work. | About 10× the per-token price of Haiku 5.5 ($1 / $5 vs $0.10 / $0.50 per 1M tokens, list prices). Still cents at lab scale. |
| Wait for Haiku 5.5 / contact AWS Sales | Keeps ADR 0004 as it is. | Blocks the query path with no date. |
| Amazon Nova Lite / Micro | Available and cheap. | New model family for me. Keeping Claude keeps the lab close to the work I already do. |

## Decision

Use **Claude Haiku 4.5** (`us.anthropic.claude-haiku-4-5-20251001-v1:0`, cross-region inference profile).

The decision is the same as in ADR 0004: a fast and cheap Haiku model to test the pipeline. Because of the service limitation that AWS applies to this account, Haiku 5.5 is not available, so we use Haiku 4.5.

## Consequences

- ✅ `query_handler` is unblocked today.
- ✅ The model ID is a Lambda setting, so moving to Haiku 5.5 later (if the account gets access) doesn't change the architecture. It's only a new ADR and a config change.
- ⚠️ Higher cost per token than Haiku 5.5. It's negligible at lab scale and covered by `maxTokens`, throttling, reserved concurrency and the $5 AWS Budget.
- ⚠️ 10 requests/min limit. That's enough for one developer. The Lambda must handle `ThrottlingException` with retries.
- ⚠️ The `query_handler` IAM policy must allow `bedrock:InvokeModel` on the Haiku 4.5 inference profile ARN **and** the underlying foundation model in the US regions the profile routes to.
