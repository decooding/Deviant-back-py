from sqlalchemy import create_engine, Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Загружаем URL базы из переменных окружения
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://admin:password@localhost/video_analysis"
)

# Создаем подключение к БД
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Функция для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from models import Alert, User  # Загружаем модели
