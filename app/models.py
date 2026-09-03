from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Fantasy(Base):
    __tablename__ = "fantasies"  # <-- Исправлено

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)  
    gif_filename: Mapped[str] = mapped_column(String(255), nullable=False)  