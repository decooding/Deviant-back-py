import os
import cv2
import torch
import numpy as np
from time import time

from services.alerts import create_alert
from schemas import AlertCreate
from models import VideoAnalysisResult
from .model_loader import predict_video


def analyze_video(video_path: str, db, skip: int = 5) -> dict:
    start = time()
    cap = cv2.VideoCapture(video_path)
    frames = []
    frame_idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % skip == 0:
            frames.append(frame)
        frame_idx += 1

    cap.release()

    if not frames:
        return {"detail": "Нет подходящих кадров"}

    prediction_label = predict_video(video_path)
    suspicious = "normal" not in prediction_label.lower()

    result = VideoAnalysisResult(
        video_filename=os.path.basename(video_path),
        frames_analyzed=len(frames),
        suspicious_detected=suspicious,
        time_taken=round(time() - start),
    )
    db.add(result)
    db.commit()
    db.refresh(result)

    if suspicious:
        create_alert(
            db,
            AlertCreate(
                type="suspicious",
                description=f"Обнаружено отклонение в {result.video_filename}",
            ),
        )

    return {
        "video": result.video_filename,
        "frames_analyzed": result.frames_analyzed,
        "suspicious_detected": suspicious,
        "time_taken": result.time_taken,
    }
