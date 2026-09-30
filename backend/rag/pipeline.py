"""RAG pipeline — retrieval, evidence selection, citation attachment."""
import uuid
import logging
from config import settings

logger = logging.getLogger(__name__)

# ChromaDB client (lazy init to avoid import issues if not installed)
_chroma_client = None
_collection = None


def _get_collection():
    """Lazy-init ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is None:
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            _chroma_client = chromadb.Client(ChromaSettings(
                persist_directory=settings.CHROMA_PERSIST_DIR,
                anonymized_telemetry=False,
            ))
            _collection = _chroma_client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            logger.warning(f"ChromaDB unavailable, using in-memory fallback: {e}")
            # In-memory fallback
            import chromadb
            _chroma_client = chromadb.Client()
            _collection = _chroma_client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION,
            )
    return _collection


def add_documents(texts: list[str], metadatas: list[dict] | None = None,
                  ids: list[str] | None = None) -> list[str]:
    """Add documents to vector store."""
    collection = _get_collection()
    if ids is None:
        ids = [str(uuid.uuid4()) for _ in texts]
    if metadatas is None:
        metadatas = [{}] * len(texts)

    # Ensure metadata values are strings (ChromaDB requirement)
    clean_metadatas = []
    for m in metadatas:
        clean = {}
        for k, v in m.items():
            if isinstance(v, (list, dict)):
                import json
                clean[k] = json.dumps(v)
            else:
                clean[k] = str(v) if v is not None else ""
        clean_metadatas.append(clean)

    collection.add(documents=texts, metadatas=clean_metadatas, ids=ids)
    return ids


def search(query: str, n_results: int = 5,
           where: dict | None = None) -> list[dict]:
    """Search vector store and return results with metadata."""
    collection = _get_collection()

    kwargs = {"query_texts": [query], "n_results": n_results}
    if where:
        kwargs["where"] = where

    try:
        results = collection.query(**kwargs)
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return []

    items = []
    if results and results.get("documents"):
        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
        ids = results["ids"][0] if results.get("ids") else [""] * len(docs)

        for doc, meta, dist, doc_id in zip(docs, metas, distances, ids):
            items.append({
                "id": doc_id,
                "content": doc,
                "metadata": meta,
                "relevance_score": 1.0 - dist,  # Convert distance to similarity
            })

    return items


def retrieve_evidence(query: str, n_results: int = 5,
                      category: str | None = None) -> dict:
    """Full RAG retrieval pipeline: search → filter → rank → cite."""
    where_filter = None
    if category:
        where_filter = {"category": category}

    results = search(query, n_results, where_filter)

    # Filter low-relevance results
    relevant = [r for r in results if r.get("relevance_score", 0) > 0.3]

    # Sort by relevance
    relevant.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    # Build citations
    citations = []
    for i, r in enumerate(relevant):
        citations.append({
            "citation_id": f"[{i+1}]",
            "content": r["content"][:500],
            "source": r["metadata"].get("source", "knowledge_base"),
            "relevance": round(r.get("relevance_score", 0), 3),
            "metadata": r["metadata"],
        })

    return {
        "evidence": relevant,
        "citations": citations,
        "evidence_count": len(relevant),
        "sufficient": len(relevant) >= 2,
        "query": query,
    }


def get_collection_stats() -> dict:
    """Get stats about the vector store."""
    try:
        collection = _get_collection()
        return {"count": collection.count(), "name": collection.name}
    except Exception:
        return {"count": 0, "name": "unavailable"}
