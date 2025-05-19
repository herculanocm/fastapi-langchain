from pydantic import BaseModel, Field
from typing import Optional

class MessageWS(BaseModel):
    """
    Esquema de mensagem para WebSocket.
    """
    role: Optional[str] = Field(default=None, title="Função do remetente")
    content: Optional[str] = Field(default=None, title="Conteúdo da mensagem")