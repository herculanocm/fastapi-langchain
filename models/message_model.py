from typing import Optional
from sqlmodel import Field, SQLModel
import sqlalchemy as sa
import uuid
import datetime

class MessageModel(SQLModel, table=True):
    """
    Modelo de mensagem.
    """
    __tablename__ = "user_message"

    __table_args__ = (
        sa.PrimaryKeyConstraint("mes_pk_uuid", name="pk_user_message"),
        sa.Index(
            "ix_user_thread_created",
            "mes_tx_user_id",
            "mes_tx_thread_id",
            "mes_dt_created_at"
        ),
    )

    id: Optional[uuid.UUID] = Field(
        default=None, 
        sa_column=sa.Column("mes_pk_uuid", sa.Uuid(as_uuid=True), default=uuid.uuid4)
        )
    
    thread_id: Optional[str] = Field(default=None, sa_column=sa.Column("mes_tx_thread_id", sa.String(255)))
    user_id: Optional[str] = Field(default=None, sa_column=sa.Column("mes_tx_user_id", sa.String(255)))
    role: str = Field(sa_column=sa.Column("mes_tx_role",sa.String(50)))
    created_at: Optional[datetime.datetime] = Field(default=None, sa_column=sa.Column("mes_dt_created_at",sa.DateTime, server_default=sa.func.now()))
    # content is text no limit on postgres
    content: str = Field("mes_tx_content", sa_column=sa.Column(sa.Text))
    