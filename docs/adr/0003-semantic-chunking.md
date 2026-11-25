# 0003. Use semantic chunking in the Knowledge Base

- **Status:** Accepted
- **Date:** 2026-11-25

## Context

Before embedding, the Bedrock Knowledge Base splits every document into chunks. The chunk is the unit that gets retrieved and passed to the model as context. If a chunk cuts an idea in half, retrieval returns incomplete context and answer quality drops. The chunking strategy is set per data source, and changing it requires a full re-ingestion.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| Fixed-size (≈300 tokens, 20% overlap) | Simple and predictable. No extra ingestion cost. Bedrock default. | Splits by token count, not by meaning, so it can cut a sentence or an idea in half. Overlap only partly compensates. |
| **Semantic** | Splits where the meaning changes, using embedding similarity between consecutive sentences. Chunks are coherent units of meaning, which gives better retrieval. | Extra embedding calls during ingestion (small cost). Chunk sizes vary. More parameters to tune (max tokens, buffer size, breakpoint threshold). |
| Hierarchical | Small child chunks for precise search, with the larger parent chunk returned as context. Good for long, structured documents. | More complex. Returns more tokens per query, which raises LLM cost. |
| No chunking | Each file is one chunk. | Only valid for very small documents. |

## Decision

Use **semantic chunking**. I have worked with fixed-size chunking before. Its problem is that it doesn't always cut at the right phrase, so we can lose meaning. Semantic chunking keeps each chunk as a coherent unit of meaning, which is better for retrieval.

Initial parameters (Bedrock defaults, to be tuned with real documents):

- Max tokens per chunk: 300
- Buffer size: 0 (sentences compared one by one)
- Breakpoint percentile threshold: 95

## Consequences

- ✅ More coherent chunks, so better retrieval relevance and better citations.
- ⚠️ Higher ingestion cost: Titan computes extra embeddings to detect breakpoints. That's negligible at lab scale.
- ⚠️ Chunk sizes vary, so retrieval quality depends on the threshold. Validate with the sample documents.
- 🔁 Changing the strategy or its parameters requires re-ingesting all documents.
