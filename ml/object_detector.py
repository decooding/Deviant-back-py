import cv2
from ultralytics import YOLO

# Загрузка YOLO модели
model = YOLO(
    "yolov8n.pt"
)  # Можно заменить на yolov8s.pt или yolov8m.pt при необходимости


def detect_objects(video_path: str, conf_threshold: float = 0.4) -> list:
    """
    Детектирует людей на видео и возвращает bounding boxes.
    Возвращает список словарей: [{frame, bbox: (x1, y1, x2, y2)}]
    """
    cap = cv2.VideoCapture(video_path)
    detections = []
    frame_idx = 0

    if not cap.isOpened():
        raise ValueError(f"❌ Невозможно открыть видео: {video_path}")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)[0]  # Получаем результат из batch
        for box in results.boxes.data.tolist():
            x1, y1, x2, y2, score, cls_id = box
            if int(cls_id) == 0 and score > conf_threshold:  # класс 0 — человек
                detections.append(
                    {"frame": frame_idx, "bbox": (int(x1), int(y1), int(x2), int(y2))}
                )

        frame_idx += 1

    cap.release()
    return detections
