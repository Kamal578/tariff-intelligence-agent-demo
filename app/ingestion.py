from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


DATE_PATTERN = re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")


def extract_evidence_date(text: str) -> date | None:
    matches = DATE_PATTERN.findall(text)
    values: list[date] = []
    for year, month, day in matches:
        try:
            values.append(date(int(year), int(month), int(day)))
        except ValueError:
            continue
    return max(values) if values else None


def load_knowledge_documents(knowledge_base_dir: Path | str) -> list[Document]:
    root = Path(knowledge_base_dir)
    documents: list[Document] = []
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        documents.append(
            Document(
                page_content=text,
                metadata={
                    "source": path.name,
                    "evidence_date": (
                        extract_evidence_date(text).isoformat()
                        if extract_evidence_date(text)
                        else None
                    ),
                },
            )
        )
    return documents


def chunk_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=120,
        separators=["\n## ", "\n- ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(documents)
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = index
        chunk.metadata["evidence_date"] = (
            extract_evidence_date(chunk.page_content).isoformat()
            if extract_evidence_date(chunk.page_content)
            else chunk.metadata.get("evidence_date")
        )
    return chunks
