from typing import Optional
from sqlmodel import Field, SQLModel
import sqlalchemy as sa
import uuid
from datetime import datetime
from core.utils import now_sp

class MessageModel(SQLModel, table=True):
    """
    Modelo de mensagem.
    """
    __tablename__ = "user_message"

    __table_args__ = (
        sa.PrimaryKeyConstraint("mes_pk_uuid", name="pk_user_message"),
        sa.ForeignKeyConstraint(
            ["mes_fk_thread_id"],
            ["user_thread_message.thr_pk_uuid"],
            name="fk_user_message_thread_id"
        ),
        sa.Index(
            "ix_thread_created",
            "mes_fk_thread_id",
            "mes_dt_created_at"
        ),
    )

    id: Optional[uuid.UUID] = Field(
        default=None, 
        sa_column=sa.Column("mes_pk_uuid", sa.Uuid(as_uuid=True), default=uuid.uuid4)
        )
    
    thread_id: Optional[uuid.UUID] = Field(default=None, sa_column=sa.Column("mes_fk_thread_id", sa.Uuid(as_uuid=True), default=uuid.uuid4))

    role: str = Field(sa_column=sa.Column("mes_tx_role",sa.String(50)))
    created_at: Optional[datetime] = Field(default_factory=now_sp, sa_column=sa.Column("mes_dt_created_at",sa.DateTime, server_default=sa.func.now()))
    # content is text no limit on postgres
    content: str = Field(sa_column=sa.Column("mes_tx_content", sa.Text))
    