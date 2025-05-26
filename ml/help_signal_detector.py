# ml/help_signal_detector.py
import cv2
import mediapipe as mp
import numpy as np
import time
import streamlit as st # Для логирования в session_state

class HelpSignalDetector:
    def _log_to_ui(self, message):
        log_key = 'help_signal_debug_log_page4' # Уникальный ключ для логов этой страницы
        if log_key not in st.session_state:
            st.session_state[log_key] = []
        log_entry = f"{time.strftime('%H:%M:%S')} - {message}"
        st.session_state[log_key].insert(0, log_entry)
        st.session_state[log_key] = st.session_state[log_key][:50] # Ограничиваем размер лога

    def __init__(self, cycles_to_confirm=2, max_time_between_steps_ms=2500, 
                 min_time_for_pose_ms=250, visibility_threshold=0.5): # Снизил порог видимости по умолчанию
        self._log_to_ui(f"Инициализация HelpSignalDetector: cycles={cycles_to_confirm}, timeout={max_time_between_steps_ms}, pose_time={min_time_for_pose_ms}, vis_thresh={visibility_threshold}")
        self.mp_hands = mp.solutions.hands
        self.hands_processor = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1, 
            min_detection_confidence=0.5, 
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.cycles_to_confirm_signal = cycles_to_confirm
        self.max_time_between_steps_ms = max_time_between_steps_ms
        self.min_time_for_pose_ms = min_time_for_pose_ms
        self.visibility_threshold = visibility_threshold

        self.STATE_IDLE = "IDLE"
        self.STATE_POSE_A_DETECTED = "POSE_A_DETECTED" # Большой палец прижат, остальные вверх
        self.STATE_POSE_B_DETECTED = "POSE_B_DETECTED" # Большой палец прижат, остальные накрывают

        self.current_signal_state = self.STATE_IDLE
        self.signal_cycle_count = 0
        self.last_pose_A_timestamp_ms = 0 # Время последнего подтверждения позы А
        self.current_pose_start_timestamp_ms = 0 # Время начала текущей стабильной позы

    def _check_visibility(self, landmarks_to_check):
        for name, lm in landmarks_to_check.items():
            if lm.visibility < self.visibility_threshold:
                self._log_to_ui(f"Visibility Check FAIL: Landmark '{name}' visibility {lm.visibility:.2f} < threshold {self.visibility_threshold}")
                return False
        return True

    def _is_thumb_tucked(self, hand_landmarks, handedness_str):
        self._log_to_ui(f"--- Evaluating _is_thumb_tucked (Hand: {handedness_str}) ---")
        lm = hand_landmarks.landmark
        # Ключевые точки
        thumb_tip = lm[self.mp_hands.HandLandmark.THUMB_TIP]
        thumb_mcp = lm[self.mp_hands.HandLandmark.THUMB_MCP] # Основание большого пальца
        index_mcp = lm[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]
        pinky_mcp = lm[self.mp_hands.HandLandmark.PINKY_MCP]
        middle_pip = lm[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP] # Примерная точка центра ладони

        if not self._check_visibility({"ThumbTip": thumb_tip, "ThumbMCP": thumb_mcp, "IndexMCP": index_mcp, "PinkyMCP": pinky_mcp}):
            return False
        
        self._log_to_ui(f"  ThumbTip:  x={thumb_tip.x:.2f}, y={thumb_tip.y:.2f}")
        self._log_to_ui(f"  ThumbMCP:  x={thumb_mcp.x:.2f}, y={thumb_mcp.y:.2f}")
        self._log_to_ui(f"  IndexMCP:  x={index_mcp.x:.2f}, y={index_mcp.y:.2f}")
        self._log_to_ui(f"  PinkyMCP:  x={pinky_mcp.x:.2f}, y={pinky_mcp.y:.2f}")
        self._log_to_ui(f"  MiddlePIP: x={middle_pip.x:.2f}, y={middle_pip.y:.2f}")

        # Эвристика 1: Кончик большого пальца находится "внутри" ладони по оси X
        # Для правой руки: THUMB_TIP.x < THUMB_MCP.x (и ближе к центру)
        # Для левой руки: THUMB_TIP.x > THUMB_MCP.x (и ближе к центру)
        # И Y-координата кончика большого пальца не сильно выше центра ладони
        
        tucked_x = False
        if handedness_str == "Right":
            tucked_x = thumb_tip.x < thumb_mcp.x and thumb_tip.x > pinky_mcp.x * 0.9 # Не выходит за мизинец
        elif handedness_str == "Left":
            tucked_x = thumb_tip.x > thumb_mcp.x and thumb_tip.x < pinky_mcp.x * 1.1 # Не выходит за мизинец (с другой стороны)
        
        # Эвристика 2: Кончик большого пальца близко к центру ладони (middle_pip)
        dist_tip_to_palm_center = np.sqrt((thumb_tip.x - middle_pip.x)**2 + (thumb_tip.y - middle_pip.y)**2)
        tucked_dist = dist_tip_to_palm_center < 0.1 # НУЖНО ТЮНИТЬ (0.1 это примерно ширина 2-3 пальцев)

        self._log_to_ui(f"  TuckedX ({handedness_str}): {tucked_x} (TT.x={thumb_tip.x:.2f}, TMCP.x={thumb_mcp.x:.2f}, PnkMCP.x={pinky_mcp.x:.2f})")
        self._log_to_ui(f"  TuckedDist to PalmCenter: {tucked_dist} (Dist={dist_tip_to_palm_center:.3f}, Threshold < 0.1)")

        # Для прижатого пальца, он должен быть согнут (tip.x отличается от mcp.x в нужную сторону)
        # И он должен быть близко к ладони
        result = tucked_x and tucked_dist 
        self._log_to_ui(f"  _is_thumb_tucked result: {result}")
        return result

    def _are_other_fingers_up(self, hand_landmarks): # (Index, Middle, Ring, Pinky)
        self._log_to_ui("--- Evaluating _are_other_fingers_up ---")
        lm = hand_landmarks.landmark
        fingers = [
            ("Index", lm[self.mp_hands.HandLandmark.INDEX_FINGER_TIP], lm[self.mp_hands.HandLandmark.INDEX_FINGER_PIP], lm[self.mp_hands.HandLandmark.INDEX_FINGER_MCP]),
            ("Middle",lm[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP], lm[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP], lm[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP]),
            ("Ring",  lm[self.mp_hands.HandLandmark.RING_FINGER_TIP], lm[self.mp_hands.HandLandmark.RING_FINGER_PIP], lm[self.mp_hands.HandLandmark.RING_FINGER_MCP]),
            ("Pinky", lm[self.mp_hands.HandLandmark.PINKY_TIP], lm[self.mp_hands.HandLandmark.PINKY_PIP], lm[self.mp_hands.HandLandmark.PINKY_MCP]),
        ]
        up_finger_count = 0
        for name, tip, pip, mcp in fingers:
            if not self._check_visibility({f"{name}Tip":tip, f"{name}Pip":pip, f"{name}Mcp":mcp}): continue
            # Палец "вверх": кончик (Y) выше чем PIP, PIP выше чем MCP. И палец достаточно выпрямлен.
            # (Y=0 вверху изображения)
            is_extended_y = (tip.y < pip.y - 0.02) and (pip.y < mcp.y - 0.02) # 0.02 - небольшой зазор, НУЖНО ТЮНИТЬ
            # Проверка на "прямоту" (очень грубая): вертикальное расстояние от MCP до TIP > некоего порога
            vertical_extension = mcp.y - tip.y
            is_straight_enough = vertical_extension > 0.10 # НУЖНО ТЮНИТЬ (10% высоты руки)
            self._log_to_ui(f"  {name}: TipY={tip.y:.2f}, PipY={pip.y:.2f}, McpY={mcp.y:.2f}. ExtY: {is_extended_y}, Straight: {is_straight_enough} (ExtVal={vertical_extension:.2f})")
            if is_extended_y and is_straight_enough:
                up_finger_count += 1
        
        result = up_finger_count >= 3 # Хотя бы 3 пальца подняты
        self._log_to_ui(f"  _are_other_fingers_up result: {result} (Count: {up_finger_count})")
        return result

    def _are_fingers_folded(self, hand_landmarks): # (Index, Middle, Ring, Pinky)
        self._log_to_ui("--- Evaluating _are_fingers_folded ---")
        lm = hand_landmarks.landmark
        fingers_data = [
            ("Index", lm[self.mp_hands.HandLandmark.INDEX_FINGER_TIP], lm[self.mp_hands.HandLandmark.INDEX_FINGER_MCP], lm[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]),
            ("Middle",lm[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP], lm[self.mp_hands.HandLandmark.MIDDLE_FINGER_MCP], lm[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]),
            ("Ring",  lm[self.mp_hands.HandLandmark.RING_FINGER_TIP], lm[self.mp_hands.HandLandmark.RING_FINGER_MCP], lm[self.mp_hands.HandLandmark.RING_FINGER_PIP]),
            ("Pinky", lm[self.mp_hands.HandLandmark.PINKY_TIP], lm[self.mp_hands.HandLandmark.PINKY_MCP], lm[self.mp_hands.HandLandmark.PINKY_PIP]),
        ]
        thumb_tip_y = lm[self.mp_hands.HandLandmark.THUMB_TIP].y # Y-координата прижатого большого пальца

        folded_finger_count = 0
        for name, tip, mcp, pip in fingers_data:
            if not self._check_visibility({f"{name}Tip":tip, f"{name}Mcp":mcp, f"{name}Pip":pip}): continue
            # Палец "сложен": кончик (Y) ниже (больше) чем MCP, или очень близко к Y большого пальца.
            is_bent_down_below_mcp = tip.y > mcp.y + 0.02 # НУЖНО ТЮНИТЬ (кончик ниже основания пальца)
            is_tip_near_thumb_y_level = abs(tip.y - thumb_tip_y) < 0.07 # НУЖНО ТЮНИТЬ (кончик по высоте как большой палец)
            
            self._log_to_ui(f"  {name}: TipY={tip.y:.2f}, McpY={mcp.y:.2f}, ThumbTipY={thumb_tip_y:.2f}. BentDown: {is_bent_down_below_mcp}, NearThumbY: {is_tip_near_thumb_y_level}")

            if is_bent_down_below_mcp and is_tip_near_thumb_y_level:
                folded_finger_count += 1
        
        result = folded_finger_count >= 3 # Хотя бы 3 пальца сложены
        self._log_to_ui(f"  _are_fingers_folded result: {result} (Count: {folded_finger_count})")
        return result

    def process_frame(self, image_bgr_np: np.ndarray):
        self.debug_log = [] # Очищаем лог для нового кадра
        current_time_ms = int(time.time() * 1000)
        
        # --- САМОЕ ПЕРВОЕ ОТЛАДОЧНОЕ СООБЩЕНИЕ ---
        self._log_to_ui(f"process_frame CALLED. Current State: {self.current_signal_state}")
        # -----------------------------------------
        
        rgb_frame = cv2.cvtColor(image_bgr_np, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.hands_processor.process(rgb_frame)
        rgb_frame.flags.writeable = True 

        help_signal_detected_this_frame = False
        hand_landmarks_for_drawing = None 
        
        current_pose_A = False
        current_pose_B = False

        if results.multi_hand_landmarks:
            # --- СООБЩЕНИЕ ОБ ОБНАРУЖЕНИИ РУК ---
            self._log_to_ui(f"Hands DETECTED ({len(results.multi_hand_landmarks)} hand(s)).")
            # ------------------------------------

            hand_landmarks = results.multi_hand_landmarks[0] # Берем первую руку
            hand_landmarks_for_drawing = results.multi_hand_landmarks
            
            handedness_str = "Unknown"
            if results.multi_handedness and results.multi_handedness[0].classification:
                 handedness_str = results.multi_handedness[0].classification[0].label
            
            # Классифицируем текущую позу руки
            is_thumb_currently_tucked = self._is_thumb_tucked(hand_landmarks, handedness_str) # Эта функция теперь будет вызываться
            
            fingers_up_now = False
            fingers_folded_now = False
            if is_thumb_currently_tucked: 
                fingers_up_now = self._are_other_fingers_up(hand_landmarks)
                fingers_folded_now = self._are_fingers_folded(hand_landmarks) # Эта функция будет вызываться, если is_thumb_currently_tucked == True
            
            self._log_to_ui(f"PoseCheck Internal: ThTck={is_thumb_currently_tucked}, FUp={fingers_up_now}, FFold={fingers_folded_now}")

            current_pose_A = is_thumb_currently_tucked and fingers_up_now
            current_pose_B = is_thumb_currently_tucked and fingers_folded_now

            # ... (остальная часть логики машины состояний process_frame как была) ...

        else: # Руки не обнаружены
            # --- СООБЩЕНИЕ ЕСЛИ РУКИ НЕ ОБНАРУЖЕНЫ ---
            self._log_to_ui("No hands detected in this frame.")
            # ---------------------------------------
            if self.current_signal_state != self.STATE_IDLE:
                 self._log_to_ui("Resetting state to IDLE (no hands).")
            self.current_signal_state = self.STATE_IDLE
            self.signal_cycle_count = 0
            self.current_pose_start_timestamp_ms = 0

        # Собираем итоговую отладочную строку (как было)
        final_debug_info = f"State: {self.current_signal_state}, Cycles: {self.signal_cycle_count}\n"
        final_debug_info += "Recent Logs:\n" + "\n".join(self.debug_log) # self.debug_log теперь будет содержать все сообщения от _log_to_ui
            
        return {
            "help_signal_detected": help_signal_detected_this_frame,
            "hand_landmarks_for_drawing": hand_landmarks_for_drawing,
            "debug_info": final_debug_info
        }

    def close(self):
        if self.hands_processor:
            self.hands_processor.close()
        self._log_to_ui("HelpSignalDetector: Ресурсы MediaPipe Hands освобождены.") # Используем _log_to_ui