from fastapi import APIRouter, Depends, status, HTTPException
from core.deps import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from core.services.message_service import MessageService
from schemas.message_schema import MessageSchema
from typing import List
import uuid

router = APIRouter(
    tags=["Message"],
)

# Get all messages by thread_id
@router.get(
    "/message/thread/{thread_id}",
    response_model=List[MessageSchema],
    status_code=status.HTTP_200_OK
)
async def get_messages_by_thread_id(
    thread_id: uuid.UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Retorna as mensagens de thread pelo ID do thread.
    """
    try:
        result = await MessageService.list_by_thread_id(session=session, thread_id=thread_id)
        if not result:
            result = []
        return result
    except Exception as e:
        # Log o erro se desejar
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected Error: {str(e)}"
        )
    
# Create a new message
@router.post(
    "/message",
    response_model=MessageSchema,
    status_code=status.HTTP_201_CREATED
)
async def create_message(
    message_data: MessageSchema,
    session: AsyncSession = Depends(get_session)
):
    """
    Cria uma nova mensagem.
    """
    try:
        result = await MessageService.create(session=session, data=message_data)
        return result
    except Exception as e:
        # Log o erro se desejar
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected Error: {str(e)}"
        )
    
# Delete a message by id
@router.delete(
    "/message/{id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_message(
    id: uuid.UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Deleta uma mensagem pelo ID.
    """
    try:
        result = await MessageService.delete(session=session, id=id)
        if result == False:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        return None
    except HTTPException as exc:
        raise exc
    except Exception as e:
        # Log o erro se desejar
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected Error: {str(e)}"
        )
    