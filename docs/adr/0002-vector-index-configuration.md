# 0002. Vector index configuration: 1024 dimensions, cosine, us-east-1

- **Status:** Accepted
- **Date:** 2026-11-25

## Context

An S3 Vectors index has settings that **cannot be changed after creation**: dimension, distance metric and non-filterable metadata keys. Changing any of them means re-creating the index and re-ingesting every document. The index must also match the embedding model, Amazon Titan Text Embeddings v2, which supports 256, 512 or 1024 dimensions.

## Options considered

**Dimension**

| Option | Pros | Cons |
|---|---|---|
| **1024** | Maximum retrieval quality of Titan v2. Default of the model. | About 4 KB per vector (float32), the most storage and the slowest queries of the three. |
| 512 | Half the storage. AWS reports about 99% of the 1024 accuracy. | Slight quality loss. |
| 256 | A quarter of the storage. About 97% of the 1024 accuracy. | Noticeable quality loss on nuanced queries. |

**Distance metric**

| Option | Pros | Cons |
|---|---|---|
| **Cosine** | Compares the direction of vectors and ignores magnitude, which is the right notion of semantic similarity for text embeddings. | None relevant here. |
| Euclidean (L2) | Useful when magnitude carries meaning. | Magnitude is noise for text similarity. With normalized vectors it gives the same ranking as cosine anyway. |

**Region**

| Option | Pros | Cons |
|---|---|---|
| **us-east-1** | Broadest Amazon Bedrock model availability. Default region of the account. | None relevant here. |
| Other regions | Closer to users outside the US. | Previous experience of missing models and features in Bedrock. |

## Decision

- **1024 dimensions.** It is the standard for Titan v2. At the scale of this lab, the difference with 512 would not be big, and the extra storage cost is negligible, so I keep maximum retrieval quality. This is not a strong constraint, and it can be revisited at scale.
- **Cosine.** It compares the direction of the vectors and not their magnitude (unlike L2), which is the right measure for semantic similarity between texts.
- **us-east-1.** It is the default region. I had problems with model availability in other regions on Amazon Bedrock in the past, and I don't want to deal with that in this project.
- **Non-filterable metadata keys:** `AMAZON_BEDROCK_TEXT` and `AMAZON_BEDROCK_METADATA`. Bedrock Knowledge Bases requires them. Without them, ingestion fails because of the 2 KB limit on filterable metadata.

## Consequences

- ✅ Best retrieval quality available from Titan v2.
- ⚠️ Storage is 2× compared to 512 dimensions. That's irrelevant at lab scale; reconsider at millions of chunks.
- ⚠️ Newer Claude models are called through cross-region inference profiles (`us.anthropic...`) even from us-east-1. IAM policies must allow the inference profile and the underlying regional models.
- 🔁 Any future change to these settings requires a new index and a full re-ingestion. Record it as a new ADR that supersedes this one.
