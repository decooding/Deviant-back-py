from pathlib import Path
from typing import List
import cv2
import numpy as np
from ultralytics import YOLO
from ml.action_classifier import classify_action_from_clip, extract_clip
from utils.logger import logger


def analyze_video_pipeline(
    video_path: str, max_frames: int = 300, stride: int = 5
) -> List[str]:
    """
    Анализ видео с использованием каскада YOLO + action classifier.
    Обрабатывает не более `max_frames` кадров с шагом `stride`.
    """
    logger.info(f"🚀 Анализ видео: {video_path}")
    cap = cv2.VideoCapture(video_path)
    yolo_model = YOLO("yolov8n.pt")

    frame_idx = 0
    actions = []

    frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or frame_idx > max_frames:
            break

        if frame_idx % stride == 0:
            results = yolo_model(frame)[0]
            for box in results.boxes.data.tolist():
                x1, y1, x2, y2, score, cls = box
                if int(cls) == 0:  # только 'person'
                    person = frame[int(y1) : int(y2), int(x1) : int(x2)]
                    if person.size == 0:
                        continue
                    person_rgb = cv2.cvtColor(person, cv2.COLOR_BGR2RGB)
                    frames.append(person_rgb)

        frame_idx += 1

    cap.release()

    if len(frames) < 16:
        logger.warning(f"⚠️ Слишком мало кадров для анализа действия: {len(frames)}")
        return []

    # Классификация по собранным кадрам
    try:
        label = classify_action_from_clip(frames)
        actions.append(label)
    except Exception as e:
        logger.error(f"❌ Ошибка классификации: {e}")

    logger.info(f"✅ Завершено: обнаружено {len(actions)} действий")
    return actions
