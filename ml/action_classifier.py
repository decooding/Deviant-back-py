import torch
import torchvision.transforms as T
import torchvision.models.video as models
import cv2
from PIL import Image
import numpy as np
import logging
from typing import List

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ✅ Загружаем модель R(2+1)D с предобученными весами
weights = models.R2Plus1D_18_Weights.DEFAULT
model = models.r2plus1d_18(weights=weights)
model.eval()

# ✅ Маппинг классов
id2label = weights.meta["categories"]

# ✅ Преобразования для одного кадра
preprocess = T.Compose(
    [
        T.Resize((112, 112)),
        T.ToTensor(),
        T.Normalize(mean=[0.45, 0.45, 0.45], std=[0.225, 0.225, 0.225]),
    ]
)


def extract_clip(
    video_path: str, num_frames: int = 16, skip: int = 4
) -> List[np.ndarray]:
    cap = cv2.VideoCapture(video_path)
    frames = []
    total = 0

    if not cap.isOpened():
        raise ValueError(f"❌ Невозможно открыть видео: {video_path}")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if total % skip == 0:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame)
        total += 1
        if len(frames) == num_frames:
            break

    cap.release()

    if len(frames) < num_frames:
        logger.warning(f"⚠️ Недостаточно кадров: {len(frames)} / {num_frames}")
        frames += [frames[-1]] * (num_frames - len(frames))

    return frames


def classify_action(video_path: str) -> str:
    try:
        frames = extract_clip(video_path)
        return classify_action_from_clip(frames)
    except Exception as e:
        logger.error(f"❌ Ошибка в classify_action: {e}")
        return "unknown"


def classify_action_from_clip(frames: List[np.ndarray]) -> str:
    try:
        processed = [preprocess(Image.fromarray(f)) for f in frames]
        clip_tensor = (
            torch.stack(processed).permute(1, 0, 2, 3).unsqueeze(0)
        )  # (1, 3, T, H, W)

        with torch.no_grad():
            outputs = model(clip_tensor)
            predicted = outputs.argmax(dim=1).item()
            label = id2label[predicted]

        logger.info(f"🎬 Класс действия: {label}")
        return label

    except Exception as e:
        logger.error(f"❌ Ошибка в classify_action_from_clip: {e}")
        return "unknown"
