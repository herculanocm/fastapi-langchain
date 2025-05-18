from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from core.database import Session
from core.llm import LLMService
from core.configs import settings
from core.services.connection_manager_service import ConnectionManagerService

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    session: AsyncSession = Session()
    try:
        yield session
        # Se o código do endpoint que usou a sessão cometer um erro
        # e não fizer commit, ou se uma HTTPException for levantada,
        # o ideal é que a transação seja desfeita.
        # No entanto, o commit/rollback é geralmente responsabilidade do endpoint/serviço.
    except HTTPException:
        # Se uma HTTPException foi levantada no endpoint,
        # é importante fazer rollback para não deixar transações pendentes.
        await session.rollback()
        raise # Re-levanta a HTTPException para o FastAPI tratar
    except Exception:
        # Para qualquer outra exceção, faça rollback e re-levante.
        await session.rollback()
        raise # Re-levanta a exceção original
    finally:
        # Sempre feche a sessão.
        await session.close()

async def get_llm_service() -> AsyncGenerator[LLMService, None]:
    if not all([settings.LLM_MODEL, settings.LLM_API_KEY]):
        raise RuntimeError("LLM model ou API key não configurado corretamente.")
    
    get_llm_service =  LLMService(
        model=settings.LLM_MODEL,
        api_key=settings.LLM_API_KEY,
        temperature=settings.LLM_TEMPERATURE
    ) 
    try:
        yield get_llm_service
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await get_llm_service.close()

async def get_connection_manager() -> AsyncGenerator[ConnectionManagerService, None]:
    connection_manager = ConnectionManagerService()
    try:
        yield connection_manager
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await connection_manager.close()