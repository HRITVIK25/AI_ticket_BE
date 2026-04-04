from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime
import os
import asyncio

from google import genai
# Reuse the already-working AsyncQdrantClient instance from kb_service
from services.kb_service import qdrant_client as _qdrant
from qdrant_client.models import Filter, FieldCondition, MatchValue

from models.models import Ticket
from repositories.ticket_repo import TicketRepository
from schemas.ticket import TicketCreate

# ── Clients ──────────────────────────────────────────────────────────────────
_gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

COLLECTION_NAME = "knowledge_base"
TOP_K = 5


# ── Helpers ───────────────────────────────────────────────────────────────────
def _embed(text: str) -> list[float]:
    result = _gemini.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )
    if not result.embeddings:
        raise ValueError("No embedding returned")
    return list(result.embeddings[0].values)


async def _embed_async(text: str) -> list[float]:
    return await asyncio.to_thread(_embed, text)


def _call_gemini(prompt: str) -> str:
    """Synchronous Gemini call — wrapped via to_thread to stay async-friendly."""
    response = _gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text.strip()


# ── Service ───────────────────────────────────────────────────────────────────
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
                    raise Exception("KB not found for the provided tag")

            initial_messages = [
                {
                    "senderId": created_by,
                    "senderRole": "customer",
                    "message": data.description,
                    "createdAt": datetime.utcnow().isoformat(),
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
                messages=initial_messages,
            )

            return await self.repo.create_ticket(new_ticket)

        except Exception as e:
            raise Exception(f"Service Error: {str(e)}")

    async def get_tickets_by_org(self, org_id: str) -> List[Ticket]:
        try:
            return await self.repo.get_tickets_by_org(org_id)
        except Exception as e:
            raise Exception(f"Service Error: {str(e)}")

    async def get_tickets_for_user(self, org_id: str, role: str, user_id: str) -> List[Ticket]:
        try:
            if role == "ticket_admin":
                return await self.repo.get_tickets_by_org(org_id)
            elif role == "customer":
                return await self.repo.get_tickets_by_org_and_customer(org_id, user_id)
            else:
                return []
        except Exception as e:
            raise Exception(f"Service Error: {str(e)}")

    async def update_ticket_status(self, ticket_id: str, status: str) -> Ticket:
        try:
            ticket = await self.repo.get_ticket_by_id(ticket_id)
            if not ticket:
                return None
            ticket.status = status
            return await self.repo.update_ticket(ticket)
        except Exception as e:
            raise Exception(f"Service Error: {str(e)}")

    async def add_message_to_ticket(
        self, ticket_id: str, message: str, sender_id: str, sender_role: str
    ) -> Ticket:
        try:
            ticket = await self.repo.get_ticket_by_id(ticket_id)
            if not ticket:
                return None

            new_message = {
                "senderId": sender_id,
                "senderRole": sender_role,
                "message": message,
                "createdAt": datetime.utcnow().isoformat(),
            }

            current_messages = list(ticket.messages) if ticket.messages else []
            current_messages.append(new_message)
            ticket.messages = current_messages

            return await self.repo.update_ticket(ticket)
        except Exception as e:
            raise Exception(f"Service Error: {str(e)}")

    # ── RAG AI Response ───────────────────────────────────────────────────────
    async def generate_rag_ai_response(self, ticket_id: str) -> Ticket:
        try:
            ticket = await self.repo.get_ticket_by_id(ticket_id)
            if not ticket:
                return None

            # ── 1. Retrieve relevant chunks from Qdrant ───────────────────
            query_text = f"{ticket.title}\n{ticket.description}"
            query_vector = await _embed_async(query_text)

            must_conditions = [
                FieldCondition(
                    key="org_id",
                    match=MatchValue(value=ticket.org_id),
                )
            ]

            # Scope to the ticket's linked KB if one was mapped
            if ticket.kb_id:
                must_conditions.append(
                    FieldCondition(
                        key="kb_id",
                        match=MatchValue(value=ticket.kb_id),
                    )
                )

            search_results = await _qdrant.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                query_filter=Filter(must=must_conditions),
                limit=TOP_K,
                with_payload=True,
            )

            # ── 2. Build context from retrieved chunks ────────────────────
            context_parts = []
            hits = search_results.points if hasattr(search_results, "points") else search_results
            for i, hit in enumerate(hits, 1):
                text = (hit.payload or {}).get("text", "").strip()
                if text:
                    context_parts.append(f"[{i}] {text}")

            context = "\n\n".join(context_parts)

            # ── 3. Build grounded prompt ──────────────────────────────────
            if context:
                prompt = f"""You are a knowledgeable and empathetic customer support assistant for our helpdesk.

        Your job is to resolve the customer's issue using the reference documentation provided below.

        INSTRUCTIONS:
        - Answer directly and conversationally — do NOT copy-paste from the docs
        - Synthesize the relevant information into a clear, step-by-step response tailored to the customer's specific issue
        - If the docs cover the topic partially, answer what you can and flag what's uncertain
        - If the docs don't cover it at all, admit it honestly and escalate gracefully
        - Keep your tone warm, professional, and solution-focused
        - Avoid jargon unless the customer used it first
        - End with a follow-up offer (e.g. "Let me know if that resolves it!")

        --- REFERENCE DOCUMENTATION ---
        {context}
        --- END DOCUMENTATION ---

        TICKET TITLE: {ticket.title}
        CUSTOMER MESSAGE:
        {ticket.description}

        Your response (address the customer directly, do not mention "the docs" or "the context"):"""

            else:
                prompt = f"""You are a knowledgeable and empathetic customer support assistant for our helpdesk.

            You don't have specific internal documentation for this query, so rely on general best practices and product knowledge.

            INSTRUCTIONS:
            - Be honest that you may not have full details specific to their account or setup
            - Offer the most helpful general guidance you can
            - Clearly recommend escalation to a human agent for anything account-specific, billing-related, or urgent
            - Keep your tone warm, professional, and solution-focused
            - Do not make up specific policies, prices, or procedures you're unsure of

            TICKET TITLE: {ticket.title}
            CUSTOMER MESSAGE:
            {ticket.description}

        Your response (address the customer directly):"""
            # ── 4. Call Gemini (free tier — gemini-2.0-flash) ────────────
            ai_reply = await asyncio.to_thread(_call_gemini, prompt)

            # ── 5. Persist response to ticket ─────────────────────────────
            ai_message = {
                "senderId": "AI",
                "senderRole": "system",
                "message": ai_reply,
                "createdAt": datetime.utcnow().isoformat(),
            }

            current_messages = list(ticket.messages) if ticket.messages else []
            current_messages.append(ai_message)
            ticket.messages = current_messages
            ticket.ai_response = ai_reply
            ticket.status = "AI_RESPONDED"

            return await self.repo.update_ticket(ticket)

        except Exception as e:
            raise Exception(f"Service Error (RAG): {str(e)}")