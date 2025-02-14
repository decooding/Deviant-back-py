from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
import shutil
import os
import time
import random
from sqlalchemy.orm import Session
from services import alerts as alert_service
from database import get_db
from utils.logger import logger
from schemas import AlertCreate  # ✅ Добавляем импорт схемы

# Создаем роутер
router = APIRouter(prefix="/videos", tags=["Videos"])

# Директория для загрузки
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Создаем папку, если нет

# Допустимые форматы видео
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}


@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """📥 Загрузка видеофайла"""

    # Проверяем расширение файла
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="❌ Недопустимый формат файла!")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    # Сохраняем видео
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"✅ Видео {file.filename} загружено.")
        return {"filename": file.filename, "path": file_path}

    except Exception as e:
        logger.error(f"❌ Ошибка загрузки файла: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при загрузке видео.")


@router.post("/analyze")
async def analyze_video(video_filename: str, db: Session = Depends(get_db)):
    """Имитация анализа видео с добавлением тревоги"""
    time.sleep(5)  # Имитация обработки видео

    result = random.choice(
        ["Девиантное поведение обнаружено!", "Ничего подозрительного не найдено."]
    )

    if "обнаружено" in result:
        alert_data = AlertCreate(
            type="suspicious",
            description=f"Обнаружено подозрительное действие в {video_filename}",
        )
        alert_service.create_alert(db, alert_data)  # ✅ Передаем объект схемы

    return {"video": video_filename, "result": result}
