from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import Session

async def get_session() -> AsyncGenerator:
    session: AsyncSession = Session()
    try:
        yield session
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await session.close()
