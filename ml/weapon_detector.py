# ml/weapon_detector.py
import cv2
import os
from ultralytics import YOLO
import torch # YOLOv8 использует PyTorch

class WeaponDetector:
    def __init__(self, model_path, confidence_threshold=0.4, 
                 target_classes=None, device='cpu'): # device: 'cpu' or 'cuda'
        
        self.device = device
        try:
            self.model = YOLO(model_path)
            self.model.to(self.device) # Перемещаем модель на указанное устройство
            print(f"WeaponDetector: Модель YOLO загружена с {model_path} на устройство {self.device}")
        except Exception as e:
            print(f"WeaponDetector: Ошибка загрузки модели YOLO из {model_path}: {e}")
            self.model = None
            # raise e # Можно пробросить исключение, чтобы Streamlit показал ошибку загрузки

        self.confidence_threshold = confidence_threshold
        
        if self.model:
            self.model_class_names = self.model.names # Словарь {id: 'name'}
            print(f"WeaponDetector: Доступные классы в модели: {self.model_class_names}")
        else:
            self.model_class_names = {}

        # По умолчанию ищем 'knife'. Вы можете расширить этот список.
        # Важно: названия классов должны ТОЧНО соответствовать тем, что в self.model_class_names
        default_targets = ['knife']
        
        _target_classes_lower = [tc.lower() for tc in (target_classes if target_classes else default_targets)]
        
        self.target_class_indices = []
        if self.model:
            self.target_class_indices = [
                k for k, v in self.model_class_names.items() if v.lower() in _target_classes_lower
            ]
            if not self.target_class_indices:
                print(f"ПРЕДУПРЕЖДЕНИЕ: Целевые классы ({_target_classes_lower}) не найдены в модели. Детекция оружия может не работать.")
            else:
                detected_target_names = [self.model_class_names[i] for i in self.target_class_indices]
                print(f"WeaponDetector: Будут отслеживаться классы: {detected_target_names} (индексы: {self.target_class_indices})")
        

    def process_frame(self, image_bgr_np: cv2.Mat):
        detected_weapons = []
        annotated_frame = image_bgr_np.copy()

        if not self.model:
            return {
                "detected_weapons": [],
                "annotated_frame": annotated_frame, # Возвращаем оригинальный кадр
                "error": "Модель YOLO не загружена"
            }

        # verbose=False чтобы уменьшить вывод в консоль от YOLO
        results = self.model.predict(source=image_bgr_np, conf=self.confidence_threshold, device=self.device, verbose=False)
        
        result = results[0] # Результат для одного изображения
        
        for box in result.boxes:
            class_id = int(box.cls)
            conf = float(box.conf)
            
            if class_id in self.target_class_indices:
                x1, y1, x2, y2 = map(int, box.xyxy[0]) # Координаты bounding box
                
                # Ограничиваем координаты границами кадра
                h_img, w_img = annotated_frame.shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w_img - 1, x2), min(h_img - 1, y2)

                weapon_info = {
                    "label": self.model_class_names.get(class_id, f"ID:{class_id}"), # .get для безопасности
                    "confidence": conf,
                    "bbox": [x1, y1, x2 - x1, y2 - y1] # формат x, y, width, height
                }
                detected_weapons.append(weapon_info)
                
                # Аннотация на кадре
                label_text = f"{weapon_info['label']}: {conf:.2f}"
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 0, 255), 2) # Красный бокс
                
                # Рассчитываем позицию текста, чтобы он не выходил за рамки
                text_size, _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                text_x = x1
                text_y = y1 - 10 if y1 - 10 > text_size[1] else y1 + text_size[1] + 5
                # Проверка, чтобы текст не выходил за верхнюю границу изображения
                if text_y < text_size[1] : text_y = y1 + text_size[1] + 5


                cv2.putText(annotated_frame, label_text, (text_x, text_y), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        return {
            "detected_weapons": detected_weapons,
            "annotated_frame": annotated_frame
        }

    # Для YOLO модели явный close() обычно не требуется, если только нет специфических ресурсов
    def close(self):
        if self.model:
            print("WeaponDetector: Модель YOLO была инициализирована.")
            # Если бы были какие-то ресурсы для освобождения, они были бы здесь
        else:
            print("WeaponDetector: Модель YOLO не была инициализирована.")