from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from models.models import Ticket
from repositories.ticket_repo import TicketRepository
from schemas.ticket import TicketCreate

class TicketService:
    def __init__(self, db: AsyncSession):
        self.repo = TicketRepository(db)

    async def create_ticket(self, data: TicketCreate, org_id: str, created_by: str) -> Ticket:
        try:
            new_ticket = Ticket(
                org_id=org_id,
                created_by=created_by,
                assigned_to="AI",  # important fix
                title=data.title,
                description=data.description
            )

            return await self.repo.create_ticket(new_ticket)

        except Exception as e:
            raise Exception(f"Service Error: {str(e)}")

    async def get_tickets_by_org(self, org_id: str) -> List[Ticket]:
        try:
            return await self.repo.get_tickets_by_org(org_id)
        except Exception as e:
            raise Exception(f"Service Error: {str(e)}")