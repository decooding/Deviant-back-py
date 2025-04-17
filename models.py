from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from database import Base


# Таблица пользователей
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)


# Таблица тревог (alerts)
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=True, nullable=False)  # Индексируем для быстрого поиска
    description = Column(String, nullable=False)
    timestamp = Column(DateTime, default=func.now())  # Авто-дата создания
    user_id = Column(Integer, ForeignKey("users.id"))  # Связь с пользователем

    user = relationship("User")  # Связь с пользователем


class VideoAnalysisResult(Base):
    __tablename__ = "video_analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    video_filename = Column(String, nullable=False)
    frames_analyzed = Column(Integer)
    suspicious_detected = Column(String)  # Можно заменить на Boolean
    time_taken = Column(Integer)  # В секундах
    created_at = Column(DateTime, default=func.now())
