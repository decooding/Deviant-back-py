from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from services.minio_service import download_from_minio
from database import get_db
from schemas import AlertCreate
from services.alerts import create_alert
from utils.logger import logger
from ml.pipeline import analyze_video_pipeline
import shutil
import os

router = APIRouter(prefix="/videos", tags=["Videos"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}


@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """📥 Загрузка видео в локальную папку"""
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="❌ Недопустимый формат файла!")

    file_path = os.path.join(UPLOAD_DIR, file.filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info(f"✅ Видео {file.filename} загружено.")
        return {"filename": file.filename, "path": file_path}

    except Exception as e:
        logger.error(f"❌ Ошибка загрузки файла: {str(e)}")
        raise HTTPException(status_code=500, detail="Ошибка при загрузке видео.")


@router.post("/analyze")
def analyze(video_filename: str, db: Session = Depends(get_db)):
    """
    🎬 Анализ видео:
    - скачивает из MinIO
    - применяет YOLOv8 + MoViNet
    - вызывает тревогу при девиации
    """
    try:
        local_path = download_from_minio(video_filename)
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки из MinIO: {str(e)}")
        raise HTTPException(status_code=404, detail="Видео не найдено")

    actions = analyze_video_pipeline(local_path)

    for action in actions:
        if action in ["fighting", "falling", "loitering"]:
            create_alert(
                db, AlertCreate(type="suspicious", description=f"Обнаружено: {action}")
            )

    return {"video": video_filename, "actions": actions}
