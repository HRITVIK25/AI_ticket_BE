from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from config.database import get_db
from schemas.kb import KBIngestResponse, KBResponse, KBSearchResult
from services.kb_service import KBService

router = APIRouter(prefix="/kb", tags=["Knowledge Base"])


# ---------------------------------------------------------------------------
# POST /kb/ingest
# Accepts: org_id (Form), title (Form), files (optional multipart uploads)
# Returns: number of chunks stored
# ---------------------------------------------------------------------------
@router.post("/ingest", response_model=KBIngestResponse, status_code=201)
async def ingest_kb(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    files: List[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
):
    try:
        org_id = getattr(request.state, "org_id", None)
        if not org_id:
            raise HTTPException(status_code=401, detail="Unauthorized: org_id missing")

        if not title or not description:
            raise HTTPException(status_code=400, detail="Title and description are required")

        if not files:
            raise HTTPException(status_code=400, detail="Files are required")

        service = KBService(db)
        kb_id = await service.ingest(
            org_id=org_id,
            title=title,
            description=description,
            files=files,
        )

        return KBIngestResponse(
            message="KB ingested successfully",
            kb_id=kb_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# ---------------------------------------------------------------------------
# GET /kb/all
# Returns all KB chunks for the authenticated org
# ---------------------------------------------------------------------------
@router.get("/all", response_model=List[KBResponse])
async def get_all_kb(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    try:
        org_id = getattr(request.state, "org_id", None)
        if not org_id:
            raise HTTPException(status_code=401, detail="Unauthorized: org_id missing")

        service = KBService(db)
        chunks = await service.get_by_org(org_id)
        return chunks

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# ---------------------------------------------------------------------------
# GET /kb/search?query=...&top_k=5
# Embeds the query and returns top-k most similar KB chunks (cosine similarity)
# ---------------------------------------------------------------------------
@router.get("/search", response_model=List[KBSearchResult])
async def search_kb(
    query: str,
    request: Request,
    kb_id: Optional[str] = None,
    top_k: int = 5,
    db: AsyncSession = Depends(get_db),
):
    try:
        org_id = getattr(request.state, "org_id", None)
        if not org_id:
            raise HTTPException(status_code=401, detail="Unauthorized: org_id missing")

        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        service = KBService(db)
        results = await service.search(org_id=org_id, query=query, kb_id=kb_id, top_k=top_k)
        return results

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
