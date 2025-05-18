
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class ThreadMessageSchema(BaseModel):

    """
    Schema de criação de mensagem.
    """
    id: Optional[UUID] = Field(None, title="ID da mensagem")
    user_id: str = Field(..., title="ID do usuário")
    created_at: Optional[datetime] = Field(
        default=None, 
        title="Data de criação da mensagem"
    )
    updated_at: Optional[datetime] = Field(
        default=None, 
        title="Data de atualização da mensagem"
    )
    subject: str = Field(..., title="Assunto da mensagem", min_length=5, max_length=255)

    class Config:
        extra = "forbid" # Proíbe campos extras
