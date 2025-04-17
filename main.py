from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from routers import alerts, videos
from utils.logger import logger

# from routers import alerts, users  # ✅ Импортируем users.py

from database import Base, engine
import models

Base.metadata.create_all(bind=engine)


app = FastAPI(title="Deviant Behavior Detection API", version="1.0.0")


@app.get("/")
def read_root():
    return {"message": "API is working!"}


# Подключаем Prometheus для мониторинга
Instrumentator().instrument(app).expose(app)


# Подключаем роутеры
app.include_router(alerts.router)
app.include_router(videos.router)
# app.include_router(users.router)

# Логируем запуск API
logger.info("🚀 FastAPI сервер запущен!")
