# Architecture Decision Records

Every significant architecture or technology decision in this project is recorded here, with its context, the options considered and the trade-offs.

- Format: `NNNN-kebab-title.md`. Sections: Status/Date, Context, Options considered, Decision, Consequences.
- An accepted ADR is never rewritten. A change of mind is a new ADR that supersedes the old one.

| # | Decision | Status |
|---|---|---|
| [0001](0001-use-s3-vectors-as-vector-store.md) | Use Amazon S3 Vectors as the vector store | Accepted |
| [0002](0002-vector-index-configuration.md) | Vector index configuration: 1024 dimensions, cosine, us-east-1 | Accepted |
| [0003](0003-semantic-chunking.md) | Use semantic chunking in the Knowledge Base | Accepted |
