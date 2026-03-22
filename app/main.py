from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from config.database import engine, Base
from models import models
from middleware.token_validation import ClerkAuthMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables in the database asynchronously
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

# Add Clerk authentication middleware
app.add_middleware(ClerkAuthMiddleware)

# Allow CORS for all websites
# Note: CORSMiddleware must be added LAST so that it runs FIRST and can handle
# preflight OPTIONS requests before the auth middleware rejects them.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api/v1")

@api_router.get("/health")
async def health_check():
    return JSONResponse(content={"status": "healthy"}, status_code=200)

@api_router.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(api_router)