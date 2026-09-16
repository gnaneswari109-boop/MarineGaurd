from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from ..database.db import Base

class Survey(Base):
    __tablename__ = "surveys"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    image_path: Mapped[str] = mapped_column(String)
    metadata_path: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    status: Mapped[str] = mapped_column(String, default="completed")

class Detection(Base):
    __tablename__ = "detections"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    survey_id: Mapped[str] = mapped_column(ForeignKey("surveys.id"))
    object_class: Mapped[str] = mapped_column(String)
    confidence: Mapped[float] = mapped_column(Float)
    raw_confidence: Mapped[float] = mapped_column(Float)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    width_m: Mapped[float] = mapped_column(Float)
    height_m: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="Needs Inspection")
    x: Mapped[float] = mapped_column(Float)
    y: Mapped[float] = mapped_column(Float)
    w: Mapped[float] = mapped_column(Float)
    h: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
