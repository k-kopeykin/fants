from sqlalchemy import String, Integer, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .database import Base

class Fantasy(Base):
    __tablename__ = "fantasies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    media_filename: Mapped[str] = mapped_column(String(255), nullable=True)
    media_type: Mapped[str] = mapped_column(String(20), nullable=True, default="text")
    category: Mapped[str] = mapped_column(String(20), nullable=True, default="prelude")  # flirt/prelude/intimacy
    temperature: Mapped[str] = mapped_column(String(20), nullable=True, default="warm")  # warm/hot/fire
    target_gender: Mapped[str] = mapped_column(String(10), nullable=True, default="both")  # m/f/both
    timer_seconds: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    boldness: Mapped[int] = mapped_column(Integer, nullable=True, default=50)  # 0-100
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GameSession(Base):
    """Хранит состояние активной игры"""
    __tablename__ = "game_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    current_level: Mapped[str] = mapped_column(String(20), default="flirt")  # flirt/prelude/intimacy
    current_temperature: Mapped[str] = mapped_column(String(20), default="warm")  # warm/hot/fire
    current_turn: Mapped[str] = mapped_column(String(10), default="m")  # m/f — чей ход
    slider_value: Mapped[int] = mapped_column(Integer, default=50)  # 0-100
    fantasies_shown: Mapped[str] = mapped_column(Text, default="")  # JSON-список ID показанных фантов
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    is_active: Mapped[int] = mapped_column(Integer, default=1)