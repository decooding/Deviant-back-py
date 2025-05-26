# ml/fall_detector.py
import cv2
import mediapipe as mp # Убедитесь, что mp импортирован
import numpy as np

class FallDetector:
    def __init__(self, aspect_ratio_threshold=1.2, confirmation_frames=5):
        # Сохраняем утилиты MediaPipe как атрибуты экземпляра
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose_solution = mp.solutions.pose  # Сохраняем сам модуль pose

        # Инициализируем Pose процессор, используя сохраненный модуль
        self.pose_processor = self.mp_pose_solution.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.fall_aspect_ratio_threshold = aspect_ratio_threshold
        self.fall_confirmation_frames_threshold = confirmation_frames
        
        # Состояние
        self.fall_frames_counter = 0
        self.is_fallen_status = False
        self.last_aspect_ratio = 0.0

    def process_frame(self, image_bgr_np: np.ndarray):
        frame_height, frame_width = image_bgr_np.shape[:2]
        
        rgb_frame = cv2.cvtColor(image_bgr_np, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False

        results = self.pose_processor.process(rgb_frame)

        detected_person = False
        current_aspect_ratio = 0.0 
        pose_bbox = None

        if results.pose_landmarks:
            detected_person = True
            # ... (остальная часть вашей логики process_frame без изменений) ...
            # Убедитесь, что вы возвращаете 'pose_landmarks_object': results.pose_landmarks
            # как мы делали в предыдущем примере:
            landmarks = results.pose_landmarks.landmark # Эта строка уже должна быть у вас

            all_x_coords = [lm.x * frame_width for lm in landmarks]
            all_y_coords = [lm.y * frame_height for lm in landmarks]

            if not all_x_coords or not all_y_coords:
                detected_person = False
            else:
                min_x, max_x = min(all_x_coords), max(all_x_coords)
                min_y, max_y = min(all_y_coords), max(all_y_coords)
                pose_bbox = [int(min_x), int(min_y), int(max_x), int(max_y)]

                pose_width = max_x - min_x
                pose_height = max_y - min_y

                if pose_height > 5:
                    current_aspect_ratio = pose_width / pose_height
                else: 
                    current_aspect_ratio = self.fall_aspect_ratio_threshold + 0.1 
            
            self.last_aspect_ratio = current_aspect_ratio

            if current_aspect_ratio > self.fall_aspect_ratio_threshold:
                self.fall_frames_counter += 1
            else:
                if self.is_fallen_status: 
                    print("FallDetector: Человек поднялся.") 
                self.fall_frames_counter = 0
                self.is_fallen_status = False
            
            if self.fall_frames_counter >= self.fall_confirmation_frames_threshold:
                if not self.is_fallen_status:
                    print(f"FallDetector: Обнаружено падение! AR: {current_aspect_ratio:.2f}")
                self.is_fallen_status = True
        else:
            if self.is_fallen_status:
                print("FallDetector: Человек вышел из кадра или не обнаружен, сброс статуса.")
            self.fall_frames_counter = 0
            self.is_fallen_status = False
            self.last_aspect_ratio = 0.0
        
        return {
            "is_fallen": self.is_fallen_status,
            "person_detected": detected_person,
            "aspect_ratio": round(self.last_aspect_ratio, 2),
            "bounding_box": pose_bbox,
            "pose_landmarks_object": results.pose_landmarks if detected_person else None # Важно для отрисовки
        }

    def close(self):
        if self.pose_processor:
            self.pose_processor.close()
            print("FallDetector: Ресурсы MediaPipe Pose освобождены.")