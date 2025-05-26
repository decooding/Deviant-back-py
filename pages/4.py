# pages/4_Көмек_Сигналын_Анықтау.py
# (файл атауын осылай өзгертуге болады)

import streamlit as st
import cv2
import numpy as np
import sys
import os
import time 

# Жобаның түбірлік бумасын sys.path-қа қосу
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Дабыл дыбысы файлының жолы
ALARM_SOUND_PATH = os.path.join(PROJECT_ROOT, "static_assets", "alarm.wav") 

# HelpSignalDetector негізгі класын импорттау әрекеті
HelpSignalDetector_class_to_use = None
import_error_details = None
_successfully_imported_real_detector = False
try:
    from ml.help_signal_detector import HelpSignalDetector as RealHelpSignalDetector
    HelpSignalDetector_class_to_use = RealHelpSignalDetector
    _successfully_imported_real_detector = True
except ImportError as e_imp:
    import_error_details = f"HelpSignalDetector класын ml.help_signal_detector файлынан импорттау қатесі: {e_imp}."
except Exception as e_gen:
    import_error_details = f"HelpSignalDetector класын импорттау кезінде БАСҚА қате: {e_gen}."

# --- Бірінші Streamlit командасы ---
st.set_page_config(page_title="Көмек Сигналы", layout="wide", initial_sidebar_state="expanded")

# --- Импорт қателерін көрсету және тығын (заглушка) класын анықтау ---
if import_error_details:
    st.error(import_error_details)

class DummyHelpSignalDetectorForPage4: 
    def __init__(self, cycles_to_confirm=2, max_time_between_steps_ms=2000, 
                 min_time_for_pose_ms=300, visibility_threshold=0.7, *args, **kwargs):
        if not _successfully_imported_real_detector: 
             st.warning("НАЗАР АУДАРЫҢЫЗ: HelpSignalDetector ТЫҒЫНЫ қолданылуда!")
        st.info(f"HelpSignalDetector тығыны инициализацияланды (параметрлермен).")
        self.mp_drawing = None
        class DummyHandsSolution: HAND_CONNECTIONS = []
        self.mp_hands = DummyHandsSolution()
        class DummyDrawingStyles:
            def get_default_hand_landmarks_style(self): return None
            def get_default_hand_connections_style(self): return None
        self.mp_drawing_styles = DummyDrawingStyles()
        self.cycles_to_confirm_signal = cycles_to_confirm
        self.max_time_between_steps_ms = max_time_between_steps_ms
        self.min_time_for_pose_ms = min_time_for_pose_ms
        self.visibility_threshold = visibility_threshold

    def process_frame(self, frame): 
        return {"help_signal_detected": False, "hand_landmarks_for_drawing": None, "debug_info": "Тығын HelpSignalDetector белсенді"}
    def close(self): 
        st.info("HelpSignalDetector тығынының close әдісі шақырылды.")
    def _log_to_ui(self, message): # Егер негізгі класс оны пайдаланса
        log_key = 'help_signal_detector_debug_log_page4' 
        if log_key not in st.session_state: st.session_state[log_key] = []
        st.session_state[log_key].insert(0, f"{time.strftime('%H:%M:%S')} - DUMMY: {message}")
        st.session_state[log_key] = st.session_state[log_key][:50]

if not _successfully_imported_real_detector:
    HelpSignalDetector_class_to_use = DummyHelpSignalDetectorForPage4

# --- Осы бет үшін метрика кілттерін инициализациялау ---
METRICS_FRAMES_KEY_HELP = 'metrics_frames_processed_help_signal_pg4'
METRICS_DETECTIONS_KEY_HELP = 'metrics_help_signals_detected_pg4'

if METRICS_FRAMES_KEY_HELP not in st.session_state:
    st.session_state[METRICS_FRAMES_KEY_HELP] = 0
if METRICS_DETECTIONS_KEY_HELP not in st.session_state:
    st.session_state[METRICS_DETECTIONS_KEY_HELP] = 0

# --- Қосымшаның негізгі бөлігі ---
st.title("Модуль 04: Халықаралық Көмек Сигналын Анықтау")
st.markdown("Қол қимылын бақылау үшін MediaPipe Hands қолданады.")
st.caption("Қимыл: алақан алға, бас бармақ алақанға қысылған, қалған 4 саусақ бүгіліп, бас бармақты жабады, бірнеше рет қайталанады.")


st.sidebar.title("МОДУЛЬДЕР") # Ваш заголовок для навигации
st.sidebar.markdown("---")
sidebar_pages = {
    "Басты бет": "app.py", # Ссылка на саму себя
    "1. Құлауды Анықтау": "pages/1.py", # Или pages/1_Құлауды_Анықтау.py
    "2. Төбелесті Анықтау": "pages/2.py", # Или pages/2_02_МОДУЛЬ.py
    "3. Эмоцияларды Классификациялау": "pages/3.py",
    "4. Көмек Сигналы": "pages/4.py",
    "5. Қаруды Анықтау": "pages/5.py",
    "6. Дыбыстық Аномалиялар": "pages/6.py",
}

for page_label, page_file_path in sidebar_pages.items():
    if os.path.exists(page_file_path.replace("/", os.sep)) or page_file_path == "app.py":
        st.sidebar.page_link(page_file_path, label=page_label)
    else:
        st.sidebar.caption(f"{page_label} (бет табылмады: {page_file_path})")
st.sidebar.markdown("---") 
st.sidebar.subheader("Көмек Сигналы Детекторының Баптаулары")

# Слайдерлерді сайдбарда анықтаймыз
# Ключтер осы бет үшін бірегей болуы керек
cycles_val_pg4 = st.sidebar.slider("Растау циклдары", 1, 5, 2, 1, key="help_cycles_slider_pg4_kz")
timeout_val_pg4 = st.sidebar.slider("Қадамдар арасындағы макс. уақыт (мс)", 500, 5000, 2500, 100, key="help_timeout_slider_pg4_kz")
pose_time_val_pg4 = st.sidebar.slider("Позаны ұстаудың мин. уақыты (мс)", 100, 1000, 250, 50, key="help_pose_time_slider_pg4_kz")
visibility_val_pg4 = st.sidebar.slider("Қол нүктесінің көріну шегі", 0.1, 1.0, 0.5, 0.05,  key="help_visibility_slider_pg4_kz")

# Детекторды инициализациялау немесе параметрлер өзгерсе қайта инициализациялау
detector_session_key_help = 'help_signal_detector_instance_pg4' # Осы бет үшін бірегей кілт

current_detector_help = st.session_state.get(detector_session_key_help)
should_reinitialize_detector_help = False

if current_detector_help is None:
    should_reinitialize_detector_help = True
elif _successfully_imported_real_detector: # Тек нақты детектор үшін параметрлерді тексереміз
    # Егер HelpSignalDetector ішіндегі атрибуттардың атаулары конструктор параметрлерімен бірдей болса:
    if (getattr(current_detector_help, 'cycles_to_confirm_signal', cycles_val_pg4) != cycles_val_pg4 or
        getattr(current_detector_help, 'max_time_between_steps_ms', timeout_val_pg4) != timeout_val_pg4 or
        getattr(current_detector_help, 'min_time_for_pose_ms', pose_time_val_pg4) != pose_time_val_pg4 or
        getattr(current_detector_help, 'visibility_threshold', visibility_val_pg4) != visibility_val_pg4):
        should_reinitialize_detector_help = True
        st.sidebar.info("Көмек сигналы детекторының параметрлері өзгерді, қайта инициализацияланады.")

if should_reinitialize_detector_help:
    if HelpSignalDetector_class_to_use:
        st.session_state[detector_session_key_help] = HelpSignalDetector_class_to_use(
            cycles_to_confirm=cycles_val_pg4,
            max_time_between_steps_ms=timeout_val_pg4,
            min_time_for_pose_ms=pose_time_val_pg4,
            visibility_threshold=visibility_val_pg4
        )
        if _successfully_imported_real_detector:
             st.sidebar.success("Көмек сигналы детекторы инициализацияланды/жаңартылды.")
    elif detector_session_key_help not in st.session_state : 
        st.error("Сыни қате: HelpSignalDetector класы анықталмаған.")
        st.stop()

# Негізгі UI колонкалары
col1, col2 = st.columns([3, 1]) 

with col2:
    st.subheader("Басқару")
    start_button_help = st.button("Веб-камераны іске қосу", key="start_help_btn_pg4_kz")
    stop_button_help = st.button("Веб-камераны тоқтату", key="stop_help_btn_pg4_kz")
    
    st.markdown("---")
    st.subheader("Сигнал Күйі:")
    status_placeholder_help = st.empty() 
    debug_info_display_container_help = st.empty() 

with col1:
    image_placeholder_help = st.empty()
    if not st.session_state.get('camera_active_help_pg4', False) and not start_button_help : 
         image_placeholder_help.info("Көмек сигналын анықтауды бастау үшін 'Веб-камераны іске қосу' түймесін басыңыз.")

if start_button_help:
    st.session_state.camera_active_help_pg4 = True
    st.session_state.alarm_played_help_signal_pg4 = False 

if stop_button_help:
    st.session_state.camera_active_help_pg4 = False
    st.session_state.alarm_played_help_signal_pg4 = False

if st.session_state.get('camera_active_help_pg4', False):
    cap_help = cv2.VideoCapture(0)
    if not cap_help.isOpened():
        st.error("Веб-камераны ашу мүмкін болмады.")
        st.session_state.camera_active_help_pg4 = False
    else:
        help_detector_instance_loop = st.session_state.get(detector_session_key_help)
        if not help_detector_instance_loop: 
            st.error("Детектор данасы сессияда табылмады!")
            st.session_state.camera_active_help_pg4 = False
        else:
            while st.session_state.camera_active_help_pg4: 
                ret, frame = cap_help.read()
                if not ret:
                    st.warning("Кадр өткізіліп кетті (Көмек Сигналы).")
                    st.session_state.camera_active_help_pg4 = False; break

                # --- МЕТРИКА: ӨҢДЕЛГЕН КАДРЛАР ---
                st.session_state[METRICS_FRAMES_KEY_HELP] += 1
                # ---------------------------------

                frame_to_draw = frame.copy() 
                result = help_detector_instance_loop.process_frame(frame.copy()) 

                debug_info_text = result.get("debug_info", "Деректер күтілуде...")
                debug_info_display_container_help.markdown(f"```\n{debug_info_text}\n```")

                # Қол нүктелерін салу
                if result.get("hand_landmarks_for_drawing") and \
                   hasattr(help_detector_instance_loop, 'mp_drawing') and help_detector_instance_loop.mp_drawing and \
                   hasattr(help_detector_instance_loop, 'mp_hands') and help_detector_instance_loop.mp_hands and \
                   hasattr(help_detector_instance_loop, 'mp_drawing_styles') and help_detector_instance_loop.mp_drawing_styles:
                    for hand_landmarks_single in result["hand_landmarks_for_drawing"]:
                        help_detector_instance_loop.mp_drawing.draw_landmarks(
                            frame_to_draw, hand_landmarks_single,
                            help_detector_instance_loop.mp_hands.HAND_CONNECTIONS, 
                            help_detector_instance_loop.mp_drawing_styles.get_default_hand_landmarks_style(),
                            help_detector_instance_loop.mp_drawing_styles.get_default_hand_connections_style()
                        )
                
                if result.get("help_signal_detected", False):
                    alert_message_kaz = "🚨 КӨМЕК СИГНАЛЫ АНЫҚТАЛДЫ! 🚨"
                    status_placeholder_help.error(alert_message_kaz)
                    cv2.putText(frame_to_draw, "!!! KOMEK SIGNALY !!!", (10, frame_to_draw.shape[0] - 20), 
                                cv2.FONT_HERSHEY_TRIPLEX, 1.2, (0, 0, 255), 2, cv2.LINE_AA)
                    
                    # --- МЕТРИКА: АНЫҚТАЛҒАН СИГНАЛДАР ---
                    st.session_state[METRICS_DETECTIONS_KEY_HELP] += 1
                    # ------------------------------------
                    
                    if not st.session_state.get('alarm_played_help_signal_pg4', False):
                        if os.path.exists(ALARM_SOUND_PATH):
                            try:
                                with open(ALARM_SOUND_PATH, "rb") as audio_file:
                                    audio_bytes = audio_file.read()
                                st.audio(audio_bytes, format="audio/wav", start_time=0)
                                st.toast("🎶 Дабыл сигналы ойнатылуда!", icon="🚨")
                            except Exception as e_audio:
                                st.warning(f"Дыбысты ойнату мүмкін болмады: {e_audio}")
                        else:
                            st.warning(f"Дабыл дыбысы файлы табылмады: {ALARM_SOUND_PATH}")
                        st.session_state.alarm_played_help_signal_pg4 = True 
                else:
                    status_placeholder_help.empty() 
                    if st.session_state.get('alarm_played_help_signal_pg4', False): 
                        st.session_state.alarm_played_help_signal_pg4 = False

                image_placeholder_help.image(cv2.cvtColor(frame_to_draw, cv2.COLOR_BGR2RGB), channels="RGB")
            
            cap_help.release()
            if st.session_state.get('camera_active_help_pg4', False): 
                st.info("Көмек сигналын анықтау веб-камерасы тоқтатылды (циклдан шығу).")
                st.session_state.camera_active_help_pg4 = False 

if not st.session_state.get('camera_active_help_pg4', False):
    if not start_button_help: 
        image_placeholder_help.info("Көмек сигналын анықтау веб-камерасы тоқтатылды.")
        status_placeholder_help.empty()
        debug_info_display_container_help.empty()


st.markdown("---")
st.subheader("Модуль Сипаттамасы:")
st.markdown("- Қол қимылын бақылау үшін **MediaPipe Hands** қолданады.")
st.markdown("- Халықаралық көмек сигналын анықтау үшін позалардың реттілігін талдайды.")
st.markdown("- **Дәлдік жарықтандыру шарттарына, камера бұрышына және қимылдың анықтығына байланысты.** Бұл эвристикалық детектор.")