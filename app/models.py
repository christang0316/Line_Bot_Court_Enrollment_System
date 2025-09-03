# app/models.py
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Column, String, Integer, Boolean, Text, UniqueConstraint, DateTime, func, Enum
import enum

class Base(DeclarativeBase):
    pass


class GroupBotState(Base):
    __tablename__ = 'group_bot_state'
    group_id = Column(String(64), primary_key=True)  # Unique identifier for each group
    bot_state = Column(Integer, nullable=False, default=0)  # 0 = OFF, 1 = ON


class AdminPermission(Base):
    __tablename__ = "admin_permission"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)     # LINE userId
    group_id: Mapped[str] = mapped_column(String(64), index=True)    # LINE groupId (scope)
    can_start_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    can_end_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    can_clear: Mapped[bool] = mapped_column(Boolean, default=False)
    
    __table_args__ = (
        UniqueConstraint("user_id", "group_id", name="uq_admin_user_group"),
    )

class CourtEnum(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"

class QueueEntry(Base):
    __tablename__ = "queue_entry"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    court: Mapped[CourtEnum] = mapped_column(Enum(CourtEnum), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    user_name: Mapped[str] = mapped_column(String(128))
    created_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("court", "user_id", name="uq_queue_user_per_court"),
    )