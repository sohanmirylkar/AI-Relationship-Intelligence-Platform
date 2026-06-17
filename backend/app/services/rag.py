import math
import re
from collections import Counter
from typing import Any

import numpy as np

from backend.app.models.schemas import RagQueryRequest, RagQueryResponse
from backend.app.services.storage import store


def embed_text(text: str, dim: int = 384) -> np.ndarray:
    vector = np.zeros(dim, dtype="float32")
    for token in re.findall(r"[a-zA-Z0-9]+", text.lower()):
        vector[hash(token) % dim] += 1.0
    norm = np.linalg.norm(vector)
    return vector / norm if norm else vector


def search_chunks(req: RagQueryRequest) -> list[dict[str, Any]]:
    state = store.read()
    chunks = state.get("chunks", [])
    if req.source_type:
        chunks = [c for c in chunks if c.get("metadata", {}).get("source_type") == req.source_type]
    query_vec = embed_text(req.query)
    query_terms = Counter(re.findall(r"[a-zA-Z0-9]+", req.query.lower()))
    scored = []
    for chunk in chunks:
        content = chunk.get("content", "")
        chunk_vec = embed_text(content)
        semantic = float(np.dot(query_vec, chunk_vec))
        keyword = _keyword_score(query_terms, content)
        recency_boost = 0.03 if "2026" in content else 0.0
        score = semantic + keyword + recency_boost
        scored.append({"score": score, **chunk})
    return sorted(scored, key=lambda item: item["score"], reverse=True)[: req.top_k]


def answer_query(req: RagQueryRequest) -> RagQueryResponse:
    results = search_chunks(req)
    citations = [
        {
            "chunk_id": item["id"],
            "doc_title": item.get("metadata", {}).get("doc_title"),
            "score": round(item["score"], 4),
        }
        for item in results
    ]
    if not results:
        answer = "No indexed internal source matched the query. Upload approved notes or documents first."
    else:
        snippets = " ".join(item["content"][:260] for item in results[:3])
        answer = (
            "Based on the indexed internal sources, the strongest relevant evidence is: "
            f"{snippets[:900]}"
        )
    return RagQueryResponse(answer=answer, citations=citations, chunks=results)


def _keyword_score(query_terms: Counter[str], content: str) -> float:
    terms = Counter(re.findall(r"[a-zA-Z0-9]+", content.lower()))
    if not query_terms:
        return 0.0
    overlap = sum(min(count, terms.get(term, 0)) for term, count in query_terms.items())
    return math.log1p(overlap) / 10
