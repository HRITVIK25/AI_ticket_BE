from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
from models.models import Ticket
from repositories.ticket_repo import TicketRepository
from schemas.ticket import TicketCreate

class TicketService:
    def __init__(self, db: AsyncSession):
        self.repo = TicketRepository(db)

    async def create_ticket(self, data: TicketCreate, org_id: str, created_by: str) -> Ticket:
        try:
            from repositories.kb_repo import KBRepository
            kb_repo = KBRepository(self.repo.db)
            
            kb_id = None
            if data.tag:
                kb_match = await kb_repo.get_kb_by_tag(org_id, data.tag)
                if kb_match:
                    kb_id = str(kb_match.id)
                else:
                    raise HTTPException(status_code=404, detail="KB not found")


            # Always start with a fresh messages list containing just the description
            initial_messages = [
                {
                    "senderId": created_by,
                    "senderRole": "customer",
                    "message": data.description,
                    "createdAt": datetime.utcnow().isoformat()
                }
            ]

            new_ticket = Ticket(
                org_id=org_id,
                created_by=created_by,
                assigned_to="AI",
                title=data.title,
                description=data.description,
                tag=data.tag,
                kb_id=kb_id,
                messages=initial_messages
            )

            return await self.repo.create_ticket(new_ticket)

        except Exception as e:
            raise Exception(f"Service Error: {str(e)}")

    async def get_tickets_by_org(self, org_id: str) -> List[Ticket]:
        try:
            return await self.repo.get_tickets_by_org(org_id)
        except Exception as e:
            raise Exception(f"Service Error: {str(e)}")

    async def generate_mock_ai_response(self, ticket_id: str) -> Ticket:
        try:
            ticket = await self.repo.get_ticket_by_id(ticket_id)
            if not ticket:
                return None
            
            # Create a mock AI response
            mock_reply = f"Hello! I am an AI assistant. I have received your ticket '{ticket.title}'. I will look into it."
            
            # Add to messages
            new_message = {
                "senderId": "AI",
                "senderRole": "system",
                "message": mock_reply,
                "createdAt": datetime.utcnow().isoformat()
            }
            
            current_messages = list(ticket.messages) if ticket.messages else []
            current_messages.append(new_message)
            ticket.messages = current_messages
            
            ticket.ai_response = mock_reply
            ticket.status = "AI_RESPONDED"
            
            return await self.repo.update_ticket(ticket)
        except Exception as e:
            raise Exception(f"Service Error: {str(e)}")