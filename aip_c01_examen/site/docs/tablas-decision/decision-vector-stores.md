---
id: decision-vector-stores
sidebar_position: 2
title: Vector & Search Stores
---

RAG (Retrieval-Augmented Generation = feeding a model relevant documents at query time) needs somewhere to store and search embeddings (numeric vector representations of text). AIP-C01 repeatedly asks you to pick the **right** store for a given constraint. Memorize this table.

Back to [course home](/) · [Domain 1](/blueprint/dominio-1-fundacion-datos) · [master constraint table](/tablas-decision/decision-por-restriccion).

## The table

| Store | Primary use case | Search capabilities | Management overhead | When to pick | When NOT to pick |
|---|---|---|---|---|---|
| **Amazon Bedrock Knowledge Bases** | Turn-key managed RAG — ingest, chunk, embed, retrieve with little setup | Vector (semantic); can front OpenSearch/Aurora as the underlying index; optional reranking | Lowest — fully managed | "Least operational overhead", "fastest to build a RAG app", managed end-to-end | You need fine-grained control over the index internals or a very exotic search config |
| **Amazon OpenSearch Serverless** | Scalable vector + lexical search | **Hybrid**: BM25 sparse (keyword) + k-NN dense (semantic) | Medium — serverless but you design the index | "Hybrid search", "keyword + semantic", large scale with relevance tuning | Simplest-possible managed RAG (Knowledge Bases is less work) |
| **Aurora PostgreSQL + pgvector** | Vector search inside an existing relational DB | Vector via the `pgvector` extension; SQL filters alongside | Medium — you run the DB | "Reuse our existing relational database", keep vectors next to transactional data | Greenfield RAG with no existing Postgres footprint |
| **Amazon Kendra** | Enterprise semantic document search with connectors | Semantic search + ML relevance ranking; built-in enterprise connectors | Low–medium — managed | "Enterprise document search", connectors to SharePoint/S3/etc., natural-language Q&A over docs | Pure embedding store for a custom RAG pipeline (overkill/cost) |
| **Amazon S3 Vectors** | Ultra-large-scale, cost-sensitive vector storage | Vector similarity at very large scale | Low — storage-tier economics | "Billions of vectors", "largest scale", "scale + cost" together | Low-latency real-time search where a hot index matters more than storage cost *(confirm current latency characteristics in AWS docs)* |

## How to read a stem

| Keyword in the scenario | Points to |
|---|---|
| "minimal setup", "managed", "turn-key RAG" | Bedrock Knowledge Bases |
| "hybrid", "keyword and semantic", "relevance tuning at scale" | OpenSearch Serverless |
| "we already run PostgreSQL / Aurora" | Aurora pgvector |
| "enterprise search", "connectors", "natural-language search over internal docs" | Kendra |
| "billions of vectors", "lowest storage cost at huge scale" | S3 Vectors |

## Common distractor traps

- **Knowledge Bases vs OpenSearch Serverless:** Knowledge Bases can *use* OpenSearch underneath. If the stem stresses *least effort*, pick Knowledge Bases; if it stresses *hybrid search control*, pick OpenSearch Serverless directly.
- **Kendra vs a vector store:** Kendra is for enterprise *document search*, not a raw embedding store for a hand-built RAG pipeline. Choosing Kendra just to store embeddings is usually the trap.
- **pgvector only when Postgres already exists:** picking Aurora pgvector for a greenfield app that has no relational workload is the classic distractor.
- **S3 Vectors is about scale + cost, not speed.** If the stem demands sub-second real-time latency, do not reflexively pick it — verify the latency need.

Apply these in the [question bank](/practica/banco-preguntas).
