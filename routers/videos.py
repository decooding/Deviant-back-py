from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import os, shutil, uuid
from database import get_db
from services.minio_service import download_from_minio
from schemas import AlertCreate
from ml.pipeline import analyze_video_pipeline
from services.alerts import create_alert
from utils.logger import logger

router = APIRouter(prefix="/videos", tags=["Videos"])

@router.post("/analyze")
def analyze_video_background(
    video_filename: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    local_path = download_from_minio(video_filename)

    background_tasks.add_task(process_video_analysis, local_path, db)
    return {"message": f"🎬 Видео {video_filename} передано в фоновую обработку"}

def process_video_analysis(local_path: str, db: Session):
    actions = analyze_video_pipeline(local_path)
    for action in actions:
        if action in ["fighting", "falling", "loitering"]:
            create_alert(db, AlertCreate(type="suspicious", description=action))
