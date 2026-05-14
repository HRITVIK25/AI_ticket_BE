# AI Ticket Backend System

A robust, AI-powered support ticket management backend system built with **FastAPI**. It leverages generative AI capabilities for automatic ticket responses, vector databases for semantic search in knowledge bases, and comprehensive role-based access control.

## 🚀 Features

- **Role-Based Access Control (RBAC):** Distinct privileges for `ticket_admin` (can view all organization tickets, reply/close tickets, manage knowledge bases) and `customer` (can only view and manage their own tickets). Authenticated via **Clerk**.
- **AI-Powered Customer Support:** Automatically generates initial responses to customer tickets using **Google Gemini** Retrieval-Augmented Generation (RAG).
- **Knowledge Base (KB) Management:** Ingests documents (PDF, DOCX, TXT) to create an organization-specific knowledge base. Uses semantic chunking and embedding.
- **Advanced Vector Search:** Employs **Qdrant** for lightning-fast semantic search of ingested knowledge base documents.
- **Live Ticket Chat:** Allows bidirectional communication between customers and admins on individual tickets.
- **Asynchronous Architecture:** Built on modern async Python using FastAPI and async SQLAlchemy with PostgreSQL.

## 🛠️ Tech Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
- **Database:** PostgreSQL (via asyncpg/psycopg2) + SQLAlchemy 2.0 ORM
- **Authentication:** [Clerk](https://clerk.com/)
- **Vector Database:** [Qdrant](https://qdrant.tech/)
- **Large Language Model (LLM):** Google Gemini (`google-genai`)
- **Document Processing:** PyPDF2
- **Server:** Uvicorn

## 📂 Project Structure

```text
app/
├── api/
│   └── routers/        # API route definitions (tickets, kb)
├── config/             # Configuration and Database engine setup
├── middleware/         # Custom middlewares (e.g., Clerk Auth)
├── models/             # SQLAlchemy declarative models
├── repositories/       # Database access layer pattern
├── schemas/            # Pydantic models for validation / serialization
├── services/           # Business logic (ticket processing, KB ingestion, RAG)
└── workflows/          # Extended workflow logic
```

## ⚙️ Setup and Installation

### Prerequisites
- Python 3.9+
- PostgreSQL database
- Qdrant Cluster (cloud or local)
- Clerk account
- Google Gemini API Key

### 1. Clone the repository
```bash
git clone <repository_url>
cd <repository_directory>
```

### 2. Set up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate       # On Windows use `venv\Scripts\activate`
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Variables
Create a `.env` file in the root directory and populate it with the required secrets:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/db_name
CLERK_SECRET_KEY=your_clerk_secret_key
QDRANT_URL=your_qdrant_cluster_url
QDRANT_API_KEY=your_qdrant_api_key
GEMINI_API_KEY=your_gemini_api_key
```
*(Note: Replace placeholders with your actual service credentials.)*

### 5. Run the Application
Start the FastAPI server utilizing Uvicorn:
```bash
uvicorn app.main:app --reload
```

The server should now be running at `http://localhost:8000`. You can access the automatic interactive API documentation at `http://localhost:8000/docs`.

## 🔄 Core Workflows

1. **Knowledge Base Ingestion:** Administrators upload documents to a specific KB. The backend uses PyPDF2 (or other parsers) to extract text, chunks the text, computes embeddings via Google Gemini, and stores them in Qdrant with associated metadata (`kb_id`, `org_id`).
2. **Ticket Generation & AI Response:** When a customer creates a ticket, the backend records the issue and initiates a semantic search against the organization's Knowledge Base. Relevant context is injected into a prompt for Gemini, which returns a helpful, auto-generated reply for the user.
3. **Admin Resolution:** Admins monitor their "Open Tickets" dashboard. They can communicate directly with customers via the ticket chat endpoint (`/api/v1/tickets/{ticket_id}/messages`) and ultimately mark the ticket as `CLOSED` when resolved.
