# Architecture Decision Records

Every significant architecture or technology decision in this project is recorded here, with its context, the options considered and the trade-offs.

- Format: `NNNN-kebab-title.md`. Sections: Status/Date, Context, Options considered, Decision, Consequences.
- An accepted ADR is never rewritten. A change of mind is a new ADR that supersedes the old one.

| # | Decision | Status |
|---|---|---|
| [0001](0001-use-s3-vectors-as-vector-store.md) | Use Amazon S3 Vectors as the vector store | Accepted |
| [0002](0002-vector-index-configuration.md) | Vector index configuration: 1024 dimensions, cosine, us-east-1 | Accepted |
| [0003](0003-semantic-chunking.md) | Use semantic chunking in the Knowledge Base | Accepted |
| [0004](0004-use-claude-haiku-5-5-for-generation.md) | Use Claude Haiku 5.5 as the generation model | Superseded by [0005](0005-use-claude-haiku-4-5-for-generation.md) |
| [0005](0005-use-claude-haiku-4-5-for-generation.md) | Use Claude Haiku 4.5 as the generation model | Accepted |
| [0006](0006-ingestion-trigger-sqs-batching-lambda-retry.md) | Ingestion trigger: SQS batching, Lambda and retry on conflict | Accepted |
| [0007](0007-cognito-admin-only-users.md) | Cognito user pool with admin-only users | Accepted |
