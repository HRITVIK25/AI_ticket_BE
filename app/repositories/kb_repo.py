from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from models.models import KnowledgeBase


class KBRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def insert_chunk(self, chunk: KnowledgeBase) -> KnowledgeBase:
        try:
            self.db.add(chunk)
            await self.db.commit()
            await self.db.refresh(chunk)
            return chunk
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"DB Error: {str(e)}")

    async def get_chunks_by_org(self, org_id: str) -> List[KnowledgeBase]:
        try:
            stmt = select(KnowledgeBase).where(KnowledgeBase.org_id == org_id)
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise Exception(f"DB Error: {str(e)}")

    async def get_chunks_by_ids(self, ids: List[str]) -> List[KnowledgeBase]:
        try:
            stmt = select(KnowledgeBase).where(KnowledgeBase.id.in_(ids))
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise Exception(f"DB Error: {str(e)}")

    async def get_all_chunks_for_search(self, org_id: str) -> List[KnowledgeBase]:
        """Returns all chunks for the org — used for in-memory cosine similarity search."""
        return await self.get_chunks_by_org(org_id)
