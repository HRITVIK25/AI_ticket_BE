import os
import io
import uuid
import asyncio
from typing import List

from google import genai

from fastapi import UploadFile
from PyPDF2 import PdfReader
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)

from models.models import KnowledgeBase
from repositories.kb_repo import KBRepository
from schemas.kb import KBSearchResult


# -------------------------------
# CONFIG
# -------------------------------

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

qdrant_client = AsyncQdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

COLLECTION_NAME = "knowledge_base"

# ⚠️ IMPORTANT: Confirm this dynamically once
VECTOR_SIZE = 3072


# -------------------------------
# HELPERS
# -------------------------------

def _get_embedding(text: str) -> List[float]:
    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text
    )

    if not result.embeddings:
        raise ValueError("No embeddings returned")

    return list(result.embeddings[0].values)


async def _get_embedding_async(text: str) -> List[float]:
    return await asyncio.to_thread(_get_embedding, text)


def _chunk_text(text: str, size: int = 300, overlap: int = 50) -> List[str]:
    chunks = []
    start = 0

    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap

    return chunks


async def _extract_text(file: UploadFile) -> str:
    content = await file.read()

    if file.filename.endswith(".txt"):
        return content.decode("utf-8", errors="ignore")

    if file.filename.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(content))
        return "".join(page.extract_text() or "" for page in reader.pages)

    return ""


# -------------------------------
# SERVICE
# -------------------------------

class KBService:
    def __init__(self, db: AsyncSession):
        self.repo = KBRepository(db)

    # ---------------------------
    # Ensure collection exists
    # ---------------------------
    async def _ensure_collection(self):
        collections = await qdrant_client.get_collections()
        exists = any(c.name == COLLECTION_NAME for c in collections.collections)

        if not exists:
            await qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE
                )
            )

    # ---------------------------
    # INGEST
    # ---------------------------
    async def ingest(
        self,
        org_id: str,
        title: str,
        description: str | None,
        files: List[UploadFile]
    ) -> str:
        """
        Creates a new kb_id and stores all chunks in ONE collection.
        """

        try:
            await self._ensure_collection()

            kb_id = uuid.uuid4().hex
            file_names = [f.filename for f in files if f.filename]

            points = []

            for file in files:
                extracted = await _extract_text(file)

                if not extracted:
                    continue

                chunks = _chunk_text(extracted)

                for idx, chunk in enumerate(chunks):

                    # Save in DB
                    kb_chunk = KnowledgeBase(
                        org_id=org_id,
                        title=title,
                        description=description,
                        file_names=file_names,
                        kb_id=kb_id,
                        content=chunk,
                        type="manual",
                    )

                    await self.repo.insert_chunk(kb_chunk)

                    embedding = await _get_embedding_async(chunk)

                    points.append(
                        PointStruct(
                            id=str(kb_chunk.id),
                            vector=embedding,
                            payload={
                                "org_id": org_id,
                                "kb_id": kb_id,
                                "text": chunk,
                                "source": file.filename,
                                "chunk_index": idx
                            }
                        )
                    )

            if points:
                await qdrant_client.upsert(
                    collection_name=COLLECTION_NAME,
                    points=points
                )

            return kb_id

        except Exception as e:
            raise Exception(f"Service Error (ingest): {str(e)}")

    # ---------------------------
    # Get all by org
    # ---------------------------
    async def get_by_org(self, org_id: str) -> List[KnowledgeBase]:
        try:
            return await self.repo.get_chunks_by_org(org_id)
        except Exception as e:
            raise Exception(f"Service Error (get_by_org): {str(e)}")

    # ---------------------------
    # SEARCH
    # ---------------------------
    async def search(
        self,
        org_id: str,
        query: str,
        kb_id: str | None = None,
        top_k: int = 5
    ) -> List[KBSearchResult]:

        """
        - If kb_id provided → search within that KB
        - Else → search across all KBs of org
        """

        try:
            query_embedding = await _get_embedding_async(query)

            must_conditions = [
                FieldCondition(
                    key="org_id",
                    match=MatchValue(value=org_id)
                )
            ]

            if kb_id:
                must_conditions.append(
                    FieldCondition(
                        key="kb_id",
                        match=MatchValue(value=kb_id)
                    )
                )

            results = await qdrant_client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding,
                query_filter=Filter(must=must_conditions),
                limit=top_k
            )

            # Map DB chunks
            ids = [str(r.id) for r in results]
            db_chunks = await self.repo.get_chunks_by_ids(ids)
            chunk_map = {str(c.id): c for c in db_chunks}

            response = []

            for hit in results:
                chunk = chunk_map.get(str(hit.id))

                if not chunk:
                    continue

                response.append(
                    KBSearchResult(
                        id=chunk.id,
                        org_id=chunk.org_id,
                        title=chunk.title,
                        description=chunk.description,
                        file_names=chunk.file_names or [],
                        content=chunk.content,
                        type=chunk.type,
                        score=round(hit.score, 6),
                        created_at=chunk.created_at,
                    )
                )

            return response

        except Exception as e:
            raise Exception(f"Service Error (search): {str(e)}")