# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import videos, alerts, stream  # ⬅️ Добавляем stream

from database import Base, engine
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(
    title="🚨 Deviant Behavior Detection API",
    description="API для анализа видео и обнаружения девиантного поведения",
    version="1.0.0",
)

# ✅ Создание таблиц при запуске
Base.metadata.create_all(bind=engine)

# ✅ Подключение роутеров
app.include_router(videos.router)
app.include_router(alerts.router)
app.include_router(stream.router)  # ⬅️ Подключаем стриминг

# ✅ Prometheus метрики
Instrumentator().instrument(app).expose(app)

# ✅ CORS для взаимодействия с фронтом (если нужен)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # замените на свой домен
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
