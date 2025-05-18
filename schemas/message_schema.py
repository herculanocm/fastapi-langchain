
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class MessageSchema(BaseModel):
    """
    Esquema de mensagem.
    """
    id: Optional[UUID] = Field(None, title="ID da mensagem")
    thread_id: UUID = Field(..., title="ID do tópico")
    role: str = Field(..., title="Função do remetente", min_length=1, max_length=50)
    created_at: Optional[datetime] = Field(default=None, title="Data de criação da mensagem")
    content: str = Field(..., title="Conteúdo da mensagem", min_length=1)

    class Config:
        extra = "forbid" # Proíbe campos extras