from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class VectorDocument:
    id: str
    text: str
    metadata: dict[str, Any]
    embedding: list[float]
    score: float = 0.0


class HashEmbeddingProvider:
    def __init__(self, dimensions: int = 128):
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in self._tokens(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            vector[index] += 1.0
        return self._normalize(vector)

    def _tokens(self, text: str) -> list[str]:
        return [token.lower() for token in re.findall(r"[\w\u4e00-\u9fff]+", text)]

    def _normalize(self, vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class PostgresVectorStore:
    def __init__(
        self,
        dsn: str,
        table_name: str = "agent_rag_documents",
        connect_timeout: int = 5,
        embeddings: HashEmbeddingProvider | None = None,
    ):
        self.dsn = dsn
        self.table_name = self._safe_identifier(table_name)
        self.connect_timeout = connect_timeout
        self.embeddings = embeddings or HashEmbeddingProvider()
        self.init_schema()

    def init_schema(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    create table if not exists {self.table_name} (
                        id text primary key,
                        text text not null,
                        metadata jsonb not null default '{{}}'::jsonb,
                        embedding jsonb not null,
                        created_at timestamptz not null default now(),
                        updated_at timestamptz not null default now()
                    )
                    """
                )
                cursor.execute(
                    f"""
                    create index if not exists {self.table_name}_metadata_gin
                    on {self.table_name} using gin (metadata)
                    """
                )
            conn.commit()

    def upsert_text(self, document_id: str, text: str, metadata: dict[str, Any] | None = None) -> None:
        embedding = self.embeddings.embed(text)
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    f"""
                    insert into {self.table_name} (id, text, metadata, embedding)
                    values (%s, %s, %s::jsonb, %s::jsonb)
                    on conflict (id) do update set
                        text = excluded.text,
                        metadata = excluded.metadata,
                        embedding = excluded.embedding,
                        updated_at = now()
                    """,
                    (
                        document_id,
                        text,
                        json.dumps(metadata or {}, ensure_ascii=False),
                        json.dumps(embedding),
                    ),
                )
            conn.commit()

    def search(self, query: str, top_k: int = 4) -> list[VectorDocument]:
        query_embedding = self.embeddings.embed(query)
        candidates = self._load_candidates()
        results: list[VectorDocument] = []
        for document in candidates:
            score = self._cosine(query_embedding, document.embedding)
            if score > 0:
                document.score = score
                results.append(document)

        results.sort(key=lambda item: item.score, reverse=True)
        return results[:top_k]

    def _load_candidates(self) -> list[VectorDocument]:
        with self._connect() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"select id, text, metadata, embedding from {self.table_name}")
                rows = cursor.fetchall()

        documents: list[VectorDocument] = []
        for row in rows:
            metadata = row[2]
            embedding = row[3]
            documents.append(
                VectorDocument(
                    id=row[0],
                    text=row[1],
                    metadata=metadata if isinstance(metadata, dict) else json.loads(metadata),
                    embedding=embedding if isinstance(embedding, list) else json.loads(embedding),
                )
            )
        return documents

    def _connect(self):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("psycopg is required for PostgreSQL RAG storage") from exc

        return psycopg.connect(self.dsn, connect_timeout=self.connect_timeout)

    def _cosine(self, left: list[float], right: list[float]) -> float:
        return sum(a * b for a, b in zip(left, right, strict=False))

    def _safe_identifier(self, value: str) -> str:
        if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", value):
            raise ValueError(f"Invalid PostgreSQL identifier: {value}")
        return value
