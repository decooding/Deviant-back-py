from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from schemas import AlertCreate
from services.alerts import create_alert
from ml.action_classifier import classify_action
import threading
import cv2
import time
import tempfile
import os

router = APIRouter(prefix="/stream", tags=["Live Stream"])

is_streaming = False  # Флаг, чтобы избежать повторных запусков


def stream_worker(db_session: Session):
    cap = cv2.VideoCapture(0)  # Или RTSP-поток
    skip = 4
    num_frames = 16
    frames = []
    frame_idx = 0

    global is_streaming
    is_streaming = True

    while is_streaming and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % skip == 0:
            frames.append(frame)

        if len(frames) == num_frames:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                path = tmp.name
                h, w = frames[0].shape[:2]
                out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), 5, (w, h))
                for f in frames:
                    out.write(f)
                out.release()

            label = classify_action(path)
            os.remove(path)
            print(f"🎬 [LIVE] Action: {label}")

            if label.lower() in ["fighting", "falling", "loitering"]:
                create_alert(
                    db_session,
                    AlertCreate(type="suspicious", description=f"[Live] {label}"),
                )

            frames = []  # Очистить

        frame_idx += 1
        time.sleep(0.1)  # Чуть снизить нагрузку

    cap.release()
    print("📴 Поток остановлен")


@router.post("/start")
def start_stream(db: Session = Depends(get_db)):
    global is_streaming
    if is_streaming:
        return {"status": "Уже запущено"}

    threading.Thread(target=stream_worker, args=(db,), daemon=True).start()
    return {"status": "✅ Поток запущен"}


@router.post("/stop")
def stop_stream():
    global is_streaming
    is_streaming = False
    return {"status": "🛑 Поток остановлен"}
