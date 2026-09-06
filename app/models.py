from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .database import Base

class Fantasy(Base):
    __tablename__ = "fantasies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    media_filename: Mapped[str] = mapped_column(String(255), nullable=True)  # переименовали для универсальности
    media_type: Mapped[str] = mapped_column(String(20), nullable=True, default="image")  # image, video, text
    category: Mapped[str] = mapped_column(String(100), nullable=True, default="Общее")
    temperature: Mapped[str] = mapped_column(String(20), nullable=True, default="warm")
    target_gender: Mapped[str] = mapped_column(String(10), nullable=True, default="any")
    timer_seconds: Mapped[int] = mapped_column(Integer, nullable=True, default=60)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)