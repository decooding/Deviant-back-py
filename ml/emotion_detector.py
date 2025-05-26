# ml/emotion_detector.py
import cv2
import mediapipe as mp
import numpy as np
import os
import time
import streamlit as st # Для логирования в session_state

# Попытка импорта TensorFlow Lite runtime
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        import tensorflow.lite as tflite 
    except ImportError:
        tflite = None
        print("CRITICAL ERROR: TensorFlow Lite runtime not found. Emotion classification will not work.")

class EmotionDetector:
    def _log_to_ui(self, message):
        """Вспомогательная функция для логирования в Streamlit session_state."""
        log_key = 'emotion_detector_debug_log_page3' 
        if log_key not in st.session_state:
            st.session_state[log_key] = []
        log_entry = f"{time.strftime('%H:%M:%S')} - {message}"
        st.session_state[log_key].insert(0, log_entry)
        st.session_state[log_key] = st.session_state[log_key][:30] # Ограничиваем размер лога

    def __init__(self, model_tflite_path=None, input_size=(48, 48)): # По умолчанию для FER-стиль моделей
        self._log_to_ui(f"Инициализация EmotionDetector с TFLite моделью: {model_tflite_path}")
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(min_detection_confidence=0.5)
        
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False, 
            max_num_faces=1,
            refine_landmarks=True, 
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.drawing_spec_landmarks = self.mp_drawing.DrawingSpec(thickness=1, circle_radius=1, color=(0,255,0))
        self.drawing_spec_connections = self.mp_drawing.DrawingSpec(thickness=1, color=(0,200,0)) # Для FACEMESH_TESSELATION

        self.interpreter = None
        self.input_details = None
        self.output_details = None
        self.input_size = input_size 
        self.is_rgb_input = False # FER модели обычно grayscale

        # Стандартные 7 эмоций для FER2013. Проверьте порядок для вашей модели!
        self.emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
        
        # Маппинг для отображения на русском, если потребуется где-то еще, но на видео будем выводить английские.
        self.target_emotion_map = {
            'Angry': 'Гнев', 
            'Disgust': 'Отвращение',
            'Fear': 'Страх', 
            'Happy': 'Радость', 
            'Sad': 'Отчаяние/Грусть',
            'Surprise': 'Удивление',
            'Neutral': 'Нейтрально'
        }

        if not tflite:
            self._log_to_ui("КРИТИЧЕСКАЯ ОШИБКА: TensorFlow Lite runtime не доступен. Невозможно загрузить модель.")
            return 
        
        if model_tflite_path and os.path.exists(model_tflite_path):
            try:
                self.interpreter = tflite.Interpreter(model_path=model_tflite_path)
                self.interpreter.allocate_tensors()
                self.input_details = self.interpreter.get_input_details()
                self.output_details = self.interpreter.get_output_details()

                # Получаем и устанавливаем input_size и is_rgb_input из модели
                if len(self.input_details[0]['shape']) == 4: # Ожидаем [1, height, width, channels]
                    model_height = self.input_details[0]['shape'][1]
                    model_width = self.input_details[0]['shape'][2]
                    model_channels = self.input_details[0]['shape'][3]
                    self.input_size = (model_width, model_height)
                    self.is_rgb_input = (model_channels == 3)
                else:
                    self._log_to_ui(f"ПРЕДУПРЕЖДЕНИЕ: Неожиданная форма входа TFLite модели: {self.input_details[0]['shape']}. Используются input_size={self.input_size} и is_rgb_input={self.is_rgb_input} по умолчанию.")

                self._log_to_ui(f"Модель эмоций TFLite загружена: {os.path.basename(model_tflite_path)}")
                self._log_to_ui(f"  Ожидаемый вход TFLite: {self.input_details[0]['shape']}, тип данных: {self.input_details[0]['dtype']}")
                self._log_to_ui(f"  Установлен is_rgb_input: {self.is_rgb_input}, input_size: {self.input_size}")

            except Exception as e:
                self._log_to_ui(f"ОШИБКА загрузки TFLite модели ({model_tflite_path}): {e}")
                self.interpreter = None 
        elif model_tflite_path: # Путь указан, но файла нет
            self._log_to_ui(f"ОШИБКА: Файл TFLite модели не найден: {model_tflite_path}")
        else: # Путь не указан
            self._log_to_ui("ПРЕДУПРЕЖДЕНИЕ: Путь к TFLite модели не указан. Классификация не будет работать.")

        # Финальная проверка в конструкторе
        if self.interpreter:
            self._log_to_ui("КОНСТРУКТОР (конец): self.interpreter УСПЕШНО создан.")
        else:
            self._log_to_ui("КОНСТРУКТОР (конец): self.interpreter остался None.")


    def process_frame(self, image_bgr_np: np.ndarray):
        frame_height, frame_width = image_bgr_np.shape[:2]
        face_detected = False
        raw_english_emotion_label = "N/A"    # Английская метка для вывода на видео
        face_landmarks_object_for_drawing = None

        rgb_frame_full = cv2.cvtColor(image_bgr_np, cv2.COLOR_BGR2RGB)
        rgb_frame_full.flags.writeable = False

        face_detection_results = self.face_detection.process(rgb_frame_full)
        face_mesh_results = self.face_mesh.process(rgb_frame_full) 

        if face_mesh_results.multi_face_landmarks:
            face_landmarks_object_for_drawing = face_mesh_results.multi_face_landmarks[0]

        if face_detection_results.detections:
            face_detected = True
            detection = face_detection_results.detections[0] 
            
            bboxC = detection.location_data.relative_bounding_box
            xmin = int(bboxC.xmin * frame_width); ymin = int(bboxC.ymin * frame_height)
            width = int(bboxC.width * frame_width); height = int(bboxC.height * frame_height)
            padding_w = int(0.15 * width); padding_h = int(0.20 * height)
            xmin_pad = max(0, xmin - padding_w); ymin_pad = max(0, ymin - padding_h)
            xmax_pad = min(frame_width, xmin + width + padding_w); ymax_pad = min(frame_height, ymin + height + padding_h)

            face_roi_bgr = image_bgr_np[ymin_pad:ymax_pad, xmin_pad:xmax_pad]

            if face_roi_bgr.size > 0 and self.interpreter:
                if self.is_rgb_input:
                    face_to_predict = cv2.cvtColor(face_roi_bgr, cv2.COLOR_BGR2RGB)
                else: 
                    face_to_predict = cv2.cvtColor(face_roi_bgr, cv2.COLOR_BGR2GRAY)
                
                face_resized = cv2.resize(face_to_predict, self.input_size, interpolation=cv2.INTER_AREA)
                input_data = face_resized.astype(np.float32)
                input_data = input_data / 255.0 # Нормализация [0, 1] (типично для FER)
                
                # Подготовка тензора для TFLite
                # Ожидаемая форма self.input_details[0]['shape'] обычно [1, height, width, channels]
                expected_shape = self.input_details[0]['shape']
                if not self.is_rgb_input: # Grayscale
                    if input_data.ndim == 2: # (H, W) -> (H, W, 1)
                        input_data = np.expand_dims(input_data, axis=-1)
                
                # Добавляем batch измерение, если его нет
                if input_data.ndim == len(expected_shape) -1 : # Например, (H,W,C) и модель ждет (1,H,W,C)
                     input_data_batch = np.expand_dims(input_data, axis=0)
                else: # Если форма уже (1,H,W,C) или другая, пытаемся использовать как есть
                     input_data_batch = input_data


                # Проверка типа данных
                if input_data_batch.dtype != self.input_details[0]['dtype']:
                    self._log_to_ui(f"Warning: Input data type {input_data_batch.dtype} mismatch model expected {self.input_details[0]['dtype']}. Casting.")
                    input_data_batch = input_data_batch.astype(self.input_details[0]['dtype'])
                
                try:
                    self.interpreter.set_tensor(self.input_details[0]['index'], input_data_batch)
                    self.interpreter.invoke()
                    predictions = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
                    
                    emotion_index = np.argmax(predictions)
                    if 0 <= emotion_index < len(self.emotion_labels):
                        raw_english_emotion_label = self.emotion_labels[emotion_index]
                        display_label = self.target_emotion_map.get(raw_english_emotion_label, raw_english_emotion_label) # Для лога
                        self._log_to_ui(f"TFLite Pred: {raw_english_emotion_label} ({predictions[emotion_index]:.2f}) -> UI: {display_label}")
                    else:
                        raw_english_emotion_label = "Index Error"
                        self._log_to_ui(f"Emotion index {emotion_index} out of bounds for labels (len: {len(self.emotion_labels)})")
                except Exception as e_infer:
                    self._log_to_ui(f"Ошибка инференса TFLite модели: {e_infer}")
                    raw_english_emotion_label = "Inference Error"

            elif not self.interpreter:
                raw_english_emotion_label = "Model not loaded"
        
        return {
            "raw_emotion_english": raw_english_emotion_label, # Для отображения на видео
            "face_detected": face_detected,
            "face_landmarks_for_drawing": face_landmarks_object_for_drawing
        }

    def close(self):
        if self.face_detection: self.face_detection.close()
        if self.face_mesh: self.face_mesh.close()
        self._log_to_ui("EmotionDetector (TFLite): Ресурсы MediaPipe освобождены.")