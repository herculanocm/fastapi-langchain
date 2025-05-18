from fastapi import APIRouter, Depends, status, HTTPException
from core.deps import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from core.services.thread_service import ThreadService
from schemas.thread_schema import ThreadMessageSchema
from typing import List
import uuid

router = APIRouter()

@router.post(
    "/thread-message",
    response_model=ThreadMessageSchema,
    status_code=status.HTTP_201_CREATED
)
async def create_thread_message(
    thread_message_data: ThreadMessageSchema,
    session: AsyncSession = Depends(get_session)
):
    """
    Cria uma nova mensagem de thread.
    """
    try:
        result = await ThreadService.create(session=session, data=thread_message_data)
        return result
    except Exception as e:
        # Log o erro se desejar
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected Error: {str(e)}"
        )

@router.get(
    "/thread-message/{id}",
    response_model=ThreadMessageSchema,
    status_code=status.HTTP_200_OK
)
async def get_thread_message(
    id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Retorna uma mensagem de thread pelo ID.
    """
    try:
        result = await ThreadService.get_by_id(session=session, id=id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread message not found"
            )
        return result
    except HTTPException as exc:  # Captura HTTPException especificamente
        raise exc  # Re-levanta a HTTPException original (seja 404, 422, etc.)
    except Exception as e:
        # Log o erro se desejar
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected Error: {str(e)}"
        )
    
@router.get(
    "/thread-message/user/{user_id}",
    response_model=List[ThreadMessageSchema],
    status_code=status.HTTP_200_OK
)
async def list_thread_messages_by_user(
    user_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Retorna todas as mensagens de thread de um usuário.
    """
    try:
        result = await ThreadService.list_by_user(session=session, user_id=user_id)
        return result
    except Exception as e:
        # Log o erro se desejar
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected Error: {str(e)}"
        )
    
@router.delete(
    "/thread-message/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_thread_message(
    id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Deleta uma mensagem de thread pelo ID.
    """

    try:
        result = await ThreadService.delete(session=session, id=id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread message not found"
            )
        return None
    except HTTPException as exc:  # Captura HTTPException especificamente
        raise exc  # Re-levanta a HTTPException original (seja 404, 422, etc.)
    except Exception as e:
        # Log o erro se desejar
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected Error: {str(e)}"
        )
    
# Update the subject of a thread message
@router.put(
    "/thread-message/{id}",
    response_model=ThreadMessageSchema,
    status_code=status.HTTP_200_OK
)
async def update_thread_message_subject(
    id: uuid.UUID,
    new_subject: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Atualiza o assunto de uma mensagem de thread pelo ID.
    """

    try:
        result = await ThreadService.update_subject(session=session, id=id, new_subject=new_subject)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Thread message not found"
            )
        return result
    except HTTPException as exc:  # Captura HTTPException especificamente
        raise exc  # Re-levanta a HTTPException original (seja 404, 422, etc.)
    except Exception as e:
        # Log o erro se desejar
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected Error: {str(e)}"
        )
