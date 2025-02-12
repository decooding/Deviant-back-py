from fastapi import FastAPI
from database import engine, Base
import routers.alerts

app = FastAPI()

# Создаем таблицы в БД (если их нет)
Base.metadata.create_all(bind=engine)

# Подключаем роуты
app.include_router(routers.alerts.router)


@app.get("/")
def read_root():
    return {"message": "API is working!"}
