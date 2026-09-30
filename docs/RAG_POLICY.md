# RAG Policy

## Pipeline
1. **Document Ingestion** — PDF, DOCX, TXT upload and parsing
2. **Chunking** — sentence-boundary splitting with overlap (500 words, 50 overlap)
3. **Embedding** — ChromaDB default embedding (all-MiniLM-L6-v2 ONNX)
4. **Indexing** — ChromaDB cosine similarity collection
5. **Retrieval** — query → top-k results with metadata filtering
6. **Citation** — each result gets citation ID, content, source, relevance score
7. **Validation** — low-relevance (<0.3) results filtered; minimum 2 results for "sufficient"

## Knowledge Base
- Seeded with 10 loan-processing domain items at startup
- Categories: regulation, policy, security_standard, process, guideline, sdlc_rule
- Each item stores: source, jurisdiction, effective date, version, applicability

## Metadata Filtering
- Filter by category, document_id, project_id, doc_type
- String values only (ChromaDB requirement)

## Evidence Handling
- Compliance outputs must cite supporting evidence
- Insufficient evidence triggers escalation to human review
- LLM is never the sole authority — evidence grounding required
