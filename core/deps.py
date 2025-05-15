from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import Session
from core.llm import LLMService
from core.configs import settings

async def get_session() -> AsyncGenerator:
    session: AsyncSession = Session()
    try:
        yield session
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await session.close()

async def get_llm_service() -> LLMService:
    # Substitua pelos valores reais de modelo e chave
    return LLMService(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        temperature=settings.LLM_TEMPERATURE
    ) 