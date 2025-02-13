import logging
from fastapi import FastAPI
from database import engine, Base
import routers.alerts
from prometheus_fastapi_instrumentator import Instrumentator

# 🔹 Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Создание таблиц в БД (если их нет)
Base.metadata.create_all(bind=engine)

# Подключение API-роутов
app.include_router(routers.alerts.router)

# 🔹 Подключаем мониторинг Prometheus
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# @app.middleware("http")
# async def log_requests(request, call_next):
#     logger.info(f"Запрос: {request.method} {request.url}")
#     response = await call_next(request)
#     logger.info(f"Ответ: {response.status_code}")
#     return response


@app.get("/")
def read_root():
    return {"message": "API is working!"}
