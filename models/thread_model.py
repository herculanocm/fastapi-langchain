from typing import Optional
from sqlmodel import Field, SQLModel
import sqlalchemy as sa
import uuid
from datetime import datetime
from core.utils import now_sp

class ThreadMessageModel(SQLModel, table=True):
    """
    Modelo de thread.
    """
    __tablename__ = "user_thread_message"

    __table_args__ = (
        sa.PrimaryKeyConstraint("thr_pk_uuid", name="pk_user_thread_message"),
        sa.Index(
            "ix_user_thread_created",
            "thr_tx_user_id",
            "thr_dt_created_at"
        ),
    )

    id: Optional[uuid.UUID] = Field(
        default=None, 
        sa_column=sa.Column("thr_pk_uuid", sa.Uuid(as_uuid=True), default=uuid.uuid4)
        )
    
    user_id: str = Field(default=None, sa_column=sa.Column("thr_tx_user_id", sa.String(255)))
    created_at: Optional[datetime] = Field(default_factory=now_sp, sa_column=sa.Column("thr_dt_created_at",sa.DateTime, server_default=sa.func.now()))
    updated_at: Optional[datetime] = Field(default_factory=now_sp, sa_column=sa.Column("thr_dt_updated_at", sa.DateTime, server_default=sa.func.now()))
    subject: Optional[str] = Field(sa_column=sa.Column("thr_tx_subject", sa.String(255)))
    qtd_subject_updated: Optional[int] = Field(sa_column=sa.Column("thr_qt_subject_updated", sa.Integer, default=0))
