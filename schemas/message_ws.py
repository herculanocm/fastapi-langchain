from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class MessageWS(BaseModel):
    """
    Esquema de mensagem para WebSocket.
    """

    id: Optional[str] = Field(None, title="ID da mensagem")
    thread_id: Optional[str] = Field(None, title="ThreadID da mensagem")
    role: Optional[str] = Field(default=None, title="Função do remetente")
    created_at: Optional[str] = Field(default=None, title="Data de criação da mensagem")
    content: Optional[str] = Field(default=None, title="Conteúdo da mensagem")