import torch
import torchvision.transforms as T
import cv2
from transformers import VideoMAEImageProcessor, VideoMAEForVideoClassification
import numpy as np

# Загрузка модели и процессора
processor = VideoMAEImageProcessor.from_pretrained("MCG-NJU/videomae-base")
model = VideoMAEForVideoClassification.from_pretrained("MCG-NJU/videomae-base")
model.eval()

transform = T.Compose([T.ToPILImage(), T.Resize((224, 224)), T.ToTensor()])


def predict_video(video_path: str, skip=5, max_frames=16) -> str:
    cap = cv2.VideoCapture(video_path)
    frames = []
    idx = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if idx % skip == 0:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(transform(frame))
        if len(frames) == max_frames:
            break
        idx += 1
    cap.release()

    if not frames:
        return "Нет подходящих кадров"

    pixel_values = torch.stack(frames).unsqueeze(0)  # (1, T, C, H, W)
    with torch.no_grad():
        outputs = model(pixel_values=pixel_values)
        predicted = outputs.logits.argmax(-1).item()
        label = model.config.id2label[predicted]

    return label
