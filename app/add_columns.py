import os
import sys
sys.path.append('d:/xebia-proj/AI_system_BE/app')
from dotenv import load_dotenv
load_dotenv('d:/xebia-proj/AI_system_BE/.env')

import asyncio
from sqlalchemy import text
from config.database import engine

async def run():
    async with engine.begin() as conn:
        try:
            await conn.execute(text('ALTER TABLE tickets ADD COLUMN tag VARCHAR;'))
            print('Added tag to tickets')
        except Exception as e: pass
        
        try:
            await conn.execute(text('ALTER TABLE tickets ADD COLUMN kb_id VARCHAR;'))
            print('Added kb_id to tickets')
        except Exception as e: pass
        
        try:
            await conn.execute(text('ALTER TABLE knowledge_bases ADD COLUMN tag TEXT;'))
            print('Added tag to knowledge_bases')
        except Exception as e: pass
            
    await engine.dispose()

asyncio.run(run())
