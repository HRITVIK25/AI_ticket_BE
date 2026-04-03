from typing import List
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import get_db
from schemas.ticket import TicketCreate, TicketResponse
from services.ticket_service import TicketService

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.post("/", response_model=TicketResponse, status_code=201)
async def create_ticket(
    request: Request,
    data: TicketCreate,
    db: AsyncSession = Depends(get_db)
):
    try:
        org_id = getattr(request.state, "org_id", None)
        created_by = getattr(request.state, "user_id", None)

        if not org_id or not created_by:
            raise HTTPException(status_code=401, detail="Unauthorized: org_id or user_id missing")

        service = TicketService(db)
        ticket = await service.create_ticket(data, org_id, created_by)

        if not ticket:
            raise HTTPException(status_code=500, detail="Ticket creation failed")

        return ticket

    except HTTPException:
        raise

    except Exception as e:
        # log this in real system
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.get("/all", response_model=List[TicketResponse])
async def get_tickets(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    try:
        org_id = getattr(request.state, "org_id", None)

        if not org_id:
            raise HTTPException(status_code=401, detail="Unauthorized: org_id missing")

        service = TicketService(db)
        tickets = await service.get_tickets_by_org(org_id)

        return tickets

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post("/{ticket_id}/ai-response", response_model=TicketResponse)
async def rag_ai_response(
    ticket_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    try:
        org_id = getattr(request.state, "org_id", None)

        if not org_id:
            raise HTTPException(status_code=401, detail="Unauthorized: org_id missing")

        service = TicketService(db)
        ticket = await service.generate_rag_ai_response(ticket_id)

        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        if ticket.org_id != org_id:
            raise HTTPException(status_code=403, detail="Forbidden: You cannot access this ticket")

        return ticket

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
