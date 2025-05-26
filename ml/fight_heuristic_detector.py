# ml/fight_heuristic_detector.py
import cv2
import mediapipe as mp
import numpy as np
import time # Для получения временных меток

class FightHeuristicDetector:
    def __init__(self, velocity_threshold=500, confirmation_frames=4, visibility_threshold=0.6):
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_pose_solution = mp.solutions.pose
        self.pose_processor = self.mp_pose_solution.Pose(
            static_image_mode=False,
            model_complexity=1, # Можно начать с 0 для скорости, потом увеличить до 1
            smooth_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.velocity_threshold = velocity_threshold  # Пикселей в секунду (примерное значение, нужно тюнить)
        self.confirmation_frames_threshold = confirmation_frames
        self.visibility_threshold = visibility_threshold

        # Состояние для отслеживания предыдущих позиций и времени
        self.prev_left_wrist_data = None  # Будет хранить (x, y, timestamp_ms)
        self.prev_right_wrist_data = None # Будет хранить (x, y, timestamp_ms)

        self.left_wrist_rapid_streak = 0
        self.right_wrist_rapid_streak = 0
        self.fight_detected_status = False

    def _calculate_pixel_velocity(self, p1_data, p2_coords_normalized, current_timestamp_ms, frame_width, frame_height):
        """
        Вычисляет скорость в пикселях в секунду.
        p1_data: (x_prev_norm, y_prev_norm, timestamp_prev_ms) - нормализованные координаты
        p2_coords_normalized: (x_curr_norm, y_curr_norm) - нормализованные координаты
        """
        if p1_data is None or p2_coords_normalized is None:
            return 0

        x_prev_norm, y_prev_norm, ts_prev_ms = p1_data
        x_curr_norm, y_curr_norm = p2_coords_normalized

        time_delta_s = (current_timestamp_ms - ts_prev_ms) / 1000.0
        if time_delta_s <= 0: # Избегаем деления на ноль или отрицательное время
            return 0

        # Денормализуем координаты в пиксели
        dx_pixels = (x_curr_norm - x_prev_norm) * frame_width
        dy_pixels = (y_curr_norm - y_prev_norm) * frame_height
        
        distance_pixels = np.sqrt(dx_pixels**2 + dy_pixels**2)
        velocity_pixels_per_second = distance_pixels / time_delta_s
        
        return velocity_pixels_per_second

    def process_frame(self, image_bgr_np: np.ndarray):
        current_timestamp_ms = int(time.time() * 1000) # Текущее время в миллисекундах
        frame_height, frame_width = image_bgr_np.shape[:2]
        
        rgb_frame = cv2.cvtColor(image_bgr_np, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.pose_processor.process(rgb_frame)
        rgb_frame.flags.writeable = True

        person_detected = False
        left_wrist_velocity = 0
        right_wrist_velocity = 0
        
        # Сбрасываем флаг детекции на каждом кадре, будем устанавливать если есть подтверждение
        # self.fight_detected_status = False # Это приведет к тому, что статус будет держаться только один кадр
                                          # Лучше управлять сбросом более аккуратно

        if results.pose_landmarks:
            person_detected = True
            landmarks = results.pose_landmarks.landmark

            # Левое запястье (LEFT_WRIST = 15)
            left_wrist_lm = landmarks[self.mp_pose_solution.PoseLandmark.LEFT_WRIST.value]
            if left_wrist_lm.visibility > self.visibility_threshold:
                current_left_wrist_coords_norm = (left_wrist_lm.x, left_wrist_lm.y)
                left_wrist_velocity = self._calculate_pixel_velocity(
                    self.prev_left_wrist_data, current_left_wrist_coords_norm, 
                    current_timestamp_ms, frame_width, frame_height
                )
                self.prev_left_wrist_data = (left_wrist_lm.x, left_wrist_lm.y, current_timestamp_ms)
                
                if left_wrist_velocity > self.velocity_threshold:
                    self.left_wrist_rapid_streak += 1
                else:
                    self.left_wrist_rapid_streak = 0
            else:
                self.prev_left_wrist_data = None # Сбрасываем, если не видно
                self.left_wrist_rapid_streak = 0

            # Правое запястье (RIGHT_WRIST = 16)
            right_wrist_lm = landmarks[self.mp_pose_solution.PoseLandmark.RIGHT_WRIST.value]
            if right_wrist_lm.visibility > self.visibility_threshold:
                current_right_wrist_coords_norm = (right_wrist_lm.x, right_wrist_lm.y)
                right_wrist_velocity = self._calculate_pixel_velocity(
                    self.prev_right_wrist_data, current_right_wrist_coords_norm,
                    current_timestamp_ms, frame_width, frame_height
                )
                self.prev_right_wrist_data = (right_wrist_lm.x, right_wrist_lm.y, current_timestamp_ms)

                if right_wrist_velocity > self.velocity_threshold:
                    self.right_wrist_rapid_streak += 1
                else:
                    self.right_wrist_rapid_streak = 0
            else:
                self.prev_right_wrist_data = None # Сбрасываем, если не видно
                self.right_wrist_rapid_streak = 0

            # Логика определения "драки"
            if self.left_wrist_rapid_streak >= self.confirmation_frames_threshold or \
               self.right_wrist_rapid_streak >= self.confirmation_frames_threshold:
                self.fight_detected_status = True
            else:
                # Сбрасываем статус, только если ни одно из запястий не двигалось быстро достаточно долго
                if self.left_wrist_rapid_streak == 0 and self.right_wrist_rapid_streak == 0:
                    self.fight_detected_status = False
        
        else: # Человек не обнаружен
            self.prev_left_wrist_data = None
            self.prev_right_wrist_data = None
            self.left_wrist_rapid_streak = 0
            self.right_wrist_rapid_streak = 0
            self.fight_detected_status = False
            
        return {
            "fight_detected": self.fight_detected_status,
            "person_detected": person_detected,
            "left_wrist_velocity": round(left_wrist_velocity, 2),
            "right_wrist_velocity": round(right_wrist_velocity, 2),
            "pose_landmarks_object": results.pose_landmarks if person_detected else None
        }

    def close(self):
        if self.pose_processor:
            self.pose_processor.close()
            print("FightHeuristicDetector: Ресурсы MediaPipe Pose освобождены.")