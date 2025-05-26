# utils/image_utils.py
import base64
import numpy as np
import cv2

def base64_to_cv2_image(base64_string: str):
    """Декодирует base64 строку в изображение OpenCV (NumPy array BGR)."""
    try:
        # Убираем префикс data:image/jpeg;base64, если он есть
        if ',' in base64_string:
            base64_string = base64_string.split(',', 1)[1]
        
        img_bytes = base64.b64decode(base64_string)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Не удалось декодировать изображение")
        return img
    except Exception as e:
        print(f"Ошибка декодирования base64: {e}")
        return None