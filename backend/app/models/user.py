import enum
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.analysis import Analysis


class UserRole(str, enum.Enum):
    VIEWER = "viewer"
    OPERATOR = "operator"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("sub", name="uq_users_sub"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sub: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    analyses: Mapped[list["Analysis"]] = relationship(back_populates="user")