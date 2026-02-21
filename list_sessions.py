import asyncio
from src.core.graph import DB_URI
import aiosqlite

async def list_sessions():
    async with aiosqlite.connect(DB_URI) as db:
        async with db.execute("SELECT DISTINCT thread_id FROM checkpoints") as cursor:
            rows = await cursor.fetchall()
            print("Sessions:", rows)

if __name__ == "__main__":
    asyncio.run(list_sessions())
