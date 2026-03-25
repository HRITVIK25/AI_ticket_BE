from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.models import Ticket

class TicketRepository:
    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_ticket(self, ticket: Ticket) -> Ticket:
        try:
            self.db.add(ticket)
            await self.db.commit()
            await self.db.refresh(ticket)
            return ticket

        except Exception as e:
            await self.db.rollback()
            raise Exception(f"DB Error: {str(e)}")

    async def get_tickets_by_org(self, org_id: str):
        try:
            stmt = select(Ticket).where(Ticket.org_id == org_id)
            result = await self.db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            raise Exception(f"DB Error: {str(e)}")

    async def get_ticket_by_id(self, ticket_id: str) -> Ticket:
        try:
            stmt = select(Ticket).where(Ticket.id == ticket_id)
            result = await self.db.execute(stmt)
            return result.scalars().first()
        except Exception as e:
            raise Exception(f"DB Error: {str(e)}")

    async def update_ticket(self, ticket: Ticket) -> Ticket:
        try:
            await self.db.commit()
            await self.db.refresh(ticket)
            return ticket
        except Exception as e:
            await self.db.rollback()
            raise Exception(f"DB Error: {str(e)}")