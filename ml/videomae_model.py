import torch
import torchvision.transforms as T
import cv2
from transformers import VideoMAEImageProcessor, VideoMAEForVideoClassification
import numpy as np
import os
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ✅ Загрузка предобученной модели и процессора
processor = VideoMAEImageProcessor.from_pretrained("MCG-NJU/videomae-base")
model = VideoMAEForVideoClassification.from_pretrained("MCG-NJU/videomae-base")
model.eval()

# ✅ Трансформация кадров
transform = T.Compose([T.ToPILImage(), T.Resize((224, 224)), T.ToTensor()])


def load_frames(video_path: str, num_frames: int = 16, skip: int = 5) -> torch.Tensor:
    cap = cv2.VideoCapture(video_path)
    frames = []
    total = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if total % skip == 0:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(transform(frame))
        total += 1
        if len(frames) == num_frames:
            break
    cap.release()

    if len(frames) < num_frames:
        logger.warning(f"Недостаточно кадров: {len(frames)} вместо {num_frames}")
        # Дополняем последним кадром
        while len(frames) < num_frames:
            frames.append(frames[-1])

    return torch.stack(frames).unsqueeze(0)  # shape: (1, 16, 3, 224, 224)


def predict_video(video_path: str) -> str:
    logger.info(f"🔍 Анализ видео: {video_path}")
    inputs = load_frames(video_path)
    with torch.no_grad():
        outputs = model(pixel_values=inputs)
        predicted_class = outputs.logits.argmax(-1).item()
        label = model.config.id2label[predicted_class]
    logger.info(f"🎯 Предсказанный класс: {label}")
    return label
