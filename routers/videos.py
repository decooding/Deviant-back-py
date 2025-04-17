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
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.minio_service import download_from_minio
from ml.video_processing import analyze_video

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
def analyze_uploaded_video(
    video_filename: str,
    skip: int = 5,
    db: Session = Depends(get_db),
):
    try:
        video_path = download_from_minio(video_filename)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Ошибка загрузки: {str(e)}")

    return analyze_video(video_path, db, skip)
