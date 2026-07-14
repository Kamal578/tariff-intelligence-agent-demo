from __future__ import annotations

import hashlib
import math
import re
import shutil
from datetime import date
from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document

from app.ingestion import chunk_documents, load_knowledge_documents
from app.schemas import RetrievedEvidence


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")


class HashingEmbeddings(Embeddings):
    """Small deterministic embedding function for offline demo retrieval."""

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in TOKEN_PATTERN.findall(text.lower()):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def build_vectorstore(
    knowledge_base_dir: Path | str,
    persist_directory: Path | str,
    collection_name: str = "tariff_knowledge",
) -> int:
    persist_path = Path(persist_directory)
    if persist_path.exists():
        shutil.rmtree(persist_path)
    persist_path.mkdir(parents=True, exist_ok=True)
    documents = chunk_documents(load_knowledge_documents(knowledge_base_dir))
    if not documents:
        return 0
    Chroma.from_documents(
        documents=documents,
        embedding=HashingEmbeddings(),
        collection_name=collection_name,
        persist_directory=str(persist_path),
    )
    return len(documents)


def get_vectorstore(
    persist_directory: Path | str,
    collection_name: str = "tariff_knowledge",
) -> Chroma:
    return Chroma(
        collection_name=collection_name,
        persist_directory=str(persist_directory),
        embedding_function=HashingEmbeddings(),
    )


def retrieve_evidence(
    query: str,
    persist_directory: Path | str,
    collection_name: str = "tariff_knowledge",
    k: int = 4,
) -> list[RetrievedEvidence]:
    vectorstore = get_vectorstore(persist_directory, collection_name)
    docs_with_scores = vectorstore.similarity_search_with_score(query, k=k)
    return [_to_evidence(document, 1.0 / (1.0 + float(distance))) for document, distance in docs_with_scores]


def _to_evidence(document: Document, score: float) -> RetrievedEvidence:
    source = str(document.metadata.get("source", "knowledge_base"))
    evidence_date = _parse_date(document.metadata.get("evidence_date"))
    bounded_score = max(0.0, min(1.0, float(score)))
    return RetrievedEvidence(
        source=source,
        content=document.page_content.strip(),
        relevance_score=bounded_score,
        evidence_date=evidence_date,
    )
