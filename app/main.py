from contextlib import asynccontextmanager
from fastapi import FastAPI
from config.database import engine, Base
from models import models

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables in the database asynchronously
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Hello World"}