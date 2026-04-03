from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from models.models import KnowledgeBase


class KBRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_kb(self, kb: KnowledgeBase) -> KnowledgeBase:
        try:
            self.db.add(kb)
            await self.db.commit()
            await self.db.refresh(kb)
            return kb
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"DB Error: {str(e)}")

    async def get_kbs_by_org(self, org_id: str) -> List[KnowledgeBase]:
        try:
            stmt = select(KnowledgeBase).where(KnowledgeBase.org_id == org_id)
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise Exception(f"DB Error: {str(e)}")

    async def get_tags_by_org(self, org_id: str) -> List[str]:
        try:
            stmt = select(KnowledgeBase.tag).where(
                KnowledgeBase.org_id == org_id,
                KnowledgeBase.tag.isnot(None)
            ).distinct()
            result = await self.db.execute(stmt)
            return [tag for tag in result.scalars().all() if tag]
        except Exception as e:
            raise Exception(f"DB Error: {str(e)}")

    async def get_kb_by_tag(self, org_id: str, tag: str) -> KnowledgeBase | None:
        try:
            stmt = select(KnowledgeBase).where(
                KnowledgeBase.org_id == org_id,
                KnowledgeBase.tag == tag
            ).limit(1)
            result = await self.db.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            raise Exception(f"DB Error: {str(e)}")

    async def get_kbs_by_ids(self, ids: List[str]) -> List[KnowledgeBase]:
        try:
            stmt = select(KnowledgeBase).where(KnowledgeBase.id.in_(ids))
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise Exception(f"DB Error: {str(e)}")
