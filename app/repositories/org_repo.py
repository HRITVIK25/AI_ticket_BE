from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import Organization

async def check_org_exists(db: AsyncSession, org_id: str) -> bool:
    """
    Check if an organization with the given ID exists in the database
    and is active.
    """
    stmt = select(Organization.id).where(
        Organization.id == org_id,
        Organization.is_active == True
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None
