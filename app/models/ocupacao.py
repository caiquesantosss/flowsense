from datetime import datetime
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.config.database import Base
import uuid

class OcupacaoModel(Base):
    __tablename__ = "ocupacao"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    quantidade_atual: Mapped[int] = mapped_column(Integer, nullable=False)
    status_ambiente: Mapped[str] = mapped_column(String, nullable=False) # "VAZIO" ou "PRESENCA"
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)