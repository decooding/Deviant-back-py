# pages/2_Төбелесті_Анықтау.py
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

# FightHeuristicDetector негізгі класын импорттау әрекеті
_successfully_imported_real_fight_detector = False
FightDetector_class_to_use = None
fight_import_error_details = None

try:
    from ml.fight_heuristic_detector import FightHeuristicDetector as RealFightDetector
    FightDetector_class_to_use = RealFightDetector
    _successfully_imported_real_fight_detector = True
except ImportError as e_fight_imp:
    fight_import_error_details = f"FightHeuristicDetector класын ml.fight_heuristic_detector файлынан импорттау қатесі: {e_fight_imp}."
except Exception as e_fight_gen:
    fight_import_error_details = f"FightHeuristicDetector класын импорттау кезінде БАСҚА қате: {e_fight_gen}."

# --- Бірінші Streamlit командасы ---
st.set_page_config(page_title="Төбелесті Анықтау (Эвристика)", layout="wide", initial_sidebar_state="expanded")

# --- Импорт қателерін көрсету және тығын (заглушка) класын анықтау ---
if fight_import_error_details:
    st.error(fight_import_error_details)

class DummyFightDetectorForPage2:
    def __init__(self, velocity_threshold=700, confirmation_frames=4, visibility_threshold=0.6, *args, **kwargs):
        if not _successfully_imported_real_fight_detector:
            st.warning("НАЗАР АУДАРЫҢЫЗ: FightHeuristicDetector ТЫҒЫНЫ қолданылуда!")
        st.info(f"FightHeuristicDetector тығыны инициализацияланды (параметрлері: v_thresh={velocity_threshold}, conf_frames={confirmation_frames}).")
        self.mp_drawing = None
        class DummyPoseSolution: POSE_CONNECTIONS = []
        self.mp_pose_solution = DummyPoseSolution()
        self.velocity_threshold = velocity_threshold
        self.confirmation_frames = confirmation_frames # Дұрыс атрибут аты
        self.visibility_threshold = visibility_threshold
        self.confirmation_frames_threshold = confirmation_frames # Егер класс ішінде осылай аталса

    def process_frame(self, frame): 
        return {"fight_detected": False, "person_detected": False, "left_wrist_velocity": 0.0, "right_wrist_velocity": 0.0, "pose_landmarks_object": None, "debug_info": "Тығын белсенді"}
    def close(self): 
        st.info("FightHeuristicDetector тығынының close әдісі шақырылды.")
    def _log_to_ui(self, message):
        log_key = 'fight_detector_debug_log_page2' 
        if log_key not in st.session_state: st.session_state[log_key] = []
        st.session_state[log_key].insert(0, f"{time.strftime('%H:%M:%S')} - DUMMY: {message}")
        st.session_state[log_key] = st.session_state[log_key][:30]

if not _successfully_imported_real_fight_detector:
    FightDetector_class_to_use = DummyFightDetectorForPage2

# --- Осы бет үшін метрика кілттерін инициализациялау ---
# Уникалды кілттерді қолданамыз
METRICS_FRAMES_KEY_FIGHT = 'metrics_frames_processed_fight_pg2'
METRICS_DETECTIONS_KEY_FIGHT = 'metrics_fights_detected_pg2'

if METRICS_FRAMES_KEY_FIGHT not in st.session_state:
    st.session_state[METRICS_FRAMES_KEY_FIGHT] = 0
if METRICS_DETECTIONS_KEY_FIGHT not in st.session_state:
    st.session_state[METRICS_DETECTIONS_KEY_FIGHT] = 0

# --- Қосымшаның негізгі бөлігі ---

st.title("Модуль 02: Төбелесті Анықтау (Қол қозғалысы бойынша эвристика)")
st.markdown("Ықтимал агрессивті мінез-құлықты анықтау үшін білектердің қозғалыс жылдамдығын талдайды.")

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
st.sidebar.subheader("Төбелес Детекторының Баптаулары (Эвристика)")

# Детекторды Streamlit сессиясының күйінде инициализациялау
fight_detector_session_key = 'fight_detector_instance_pg2' # Осы бет үшін бірегей кілт

# Слайдерлерді сайдбарда анықтаймыз
velocity_thresh_slider_val_pg2 = st.sidebar.slider("Жылдамдық шегі (пикс/сек)", 100, 3000, 700, 50, key="fight_velo_thresh_slider_pg2")
confirmation_frames_slider_val_pg2 = st.sidebar.slider("Растау кадрлары", 1, 15, 4, 1, key="fight_conf_frames_slider_pg2")
visibility_thresh_slider_val_pg2 = st.sidebar.slider("Нүкте көріну шегі", 0.1, 1.0, 0.6, 0.05, key="fight_vis_thresh_slider_pg2")
st.sidebar.markdown("---")

# Детекторды инициализациялау немесе параметрлер өзгерсе қайта инициализациялау
current_detector_fight = st.session_state.get(fight_detector_session_key)
should_reinitialize_detector = False

if current_detector_fight is None:
    should_reinitialize_detector = True
elif _successfully_imported_real_fight_detector: # Тек нақты детектор үшін параметрлерді тексереміз
    # Егер FightHeuristicDetector ішінде confirmation_frames_threshold қолданылса:
    # current_confirmation_frames = getattr(current_detector_fight, 'confirmation_frames_threshold', confirmation_frames_slider_val_pg2)
    # Егер confirmation_frames қолданылса:
    current_confirmation_frames = getattr(current_detector_fight, 'confirmation_frames', confirmation_frames_slider_val_pg2)
    
    if (getattr(current_detector_fight, 'velocity_threshold', velocity_thresh_slider_val_pg2) != velocity_thresh_slider_val_pg2 or
        current_confirmation_frames != confirmation_frames_slider_val_pg2 or
        getattr(current_detector_fight, 'visibility_threshold', visibility_thresh_slider_val_pg2) != visibility_thresh_slider_val_pg2):
        should_reinitialize_detector = True
        st.sidebar.info("Параметрлер өзгерді, детектор қайта инициализацияланады.")

if should_reinitialize_detector:
    if FightDetector_class_to_use:
        st.session_state[fight_detector_session_key] = FightDetector_class_to_use(
            velocity_threshold=velocity_thresh_slider_val_pg2,
            confirmation_frames=confirmation_frames_slider_val_pg2, # Конструктор confirmation_frames күтеді
            visibility_threshold=visibility_thresh_slider_val_pg2
        )
        if _successfully_imported_real_fight_detector : # Тығын үшін бұл хабарламаны көрсетпейміз
             st.sidebar.success("Төбелес детекторы инициализацияланды/жаңартылды.")
    elif fight_detector_session_key not in st.session_state : # Егер класс жоқ болса және данасы да жоқ болса
        st.error("Сыни қате: FightHeuristicDetector класы анықталмаған.")
        st.stop()


col1, col2 = st.columns([3, 1])

with col2:
    st.subheader("Басқару")
    start_button_fight = st.button("Веб-камераны іске қосу", key="start_fight_btn_pg2_v2")
    stop_button_fight = st.button("Веб-камераны тоқтату", key="stop_fight_btn_pg2_v2")
    
    st.markdown("---")
    st.subheader("Ағымдағы Күй:")
    status_placeholder_fight = st.empty()

with col1:
    image_placeholder_fight = st.empty()
    if not st.session_state.get('camera_active_fight_pg2', False) and not start_button_fight:
         image_placeholder_fight.info("Анықтауды бастау үшін 'Веб-камераны іске қосу' түймесін басыңыз.")

if start_button_fight:
    st.session_state.camera_active_fight_pg2 = True

if stop_button_fight:
    st.session_state.camera_active_fight_pg2 = False


if st.session_state.get('camera_active_fight_pg2', False):
    cap_fight = cv2.VideoCapture(0)
    if not cap_fight.isOpened():
        st.error("Веб-камераны ашу мүмкін болмады.")
        st.session_state.camera_active_fight_pg2 = False
    else:
        fight_detector_obj_loop = st.session_state.get(fight_detector_session_key)
        if not fight_detector_obj_loop:
            st.error("Цикл үшін FightHeuristicDetector данасы сессияда табылмады!")
            st.session_state.camera_active_fight_pg2 = False
        else:
            mp_drawing_utils = getattr(fight_detector_obj_loop, 'mp_drawing', None)
            mp_pose_connections = None # MediaPipe Pose үшін
            if hasattr(fight_detector_obj_loop, 'mp_pose_solution') and fight_detector_obj_loop.mp_pose_solution:
                mp_pose_connections = getattr(fight_detector_obj_loop.mp_pose_solution, 'POSE_CONNECTIONS', None)

            default_drawing_spec = mp_drawing_utils.DrawingSpec(thickness=1, circle_radius=1) if mp_drawing_utils else None

            while st.session_state.camera_active_fight_pg2: 
                ret, frame = cap_fight.read()
                if not ret:
                    st.warning("Кадр өткізіліп кетті (Төбелес).")
                    st.session_state.camera_active_fight_pg2 = False
                    break

                # --- МЕТРИКА ЖИНАУ ---
                st.session_state[METRICS_FRAMES_KEY_FIGHT] += 1
                # ---------------------

                frame_to_draw = frame.copy()
                result = fight_detector_obj_loop.process_frame(frame.copy()) 

                status_text = "Қалыпты белсенділік"
                text_color = (0, 255, 0) # Жасыл

                if not result.get("person_detected", False):
                    status_text = "Адам анықталмады"
                    text_color = (100, 100, 100) # Сұр
                elif result.get("fight_detected", False):
                    status_text = "ТӨБЕЛЕС ЫҚТИМАЛДЫҒЫ!"
                    text_color = (0, 0, 255) # Қызыл
                    # --- МЕТРИКА ЖИНАУ ---
                    st.session_state[METRICS_DETECTIONS_KEY_FIGHT] += 1
                    # ---------------------
                
                status_placeholder_fight.markdown(f"<h5 style='color:rgb{text_color[2], text_color[1], text_color[0]};'>{status_text}</h5>", unsafe_allow_html=True) # BGR to RGB for HTML color


                if result.get("pose_landmarks_object") and mp_drawing_utils and mp_pose_connections:
                    mp_drawing_utils.draw_landmarks(
                        frame_to_draw,
                        result["pose_landmarks_object"],
                        mp_pose_connections,
                        landmark_drawing_spec=default_drawing_spec, # Қарапайым стиль
                        connection_drawing_spec=default_drawing_spec # Қарапайым стиль
                    )
                
                font_scale = min(frame.shape[1], frame.shape[0]) / 700.0
                cv2.putText(frame_to_draw, f"L.Wrist Vel: {result.get('left_wrist_velocity', 0.0):.1f}", (20, int(30*font_scale*2.5)), cv2.FONT_HERSHEY_SIMPLEX, font_scale*0.8, (255,100,0), 2)
                cv2.putText(frame_to_draw, f"R.Wrist Vel: {result.get('right_wrist_velocity', 0.0):.1f}", (20, int(55*font_scale*2.5)), cv2.FONT_HERSHEY_SIMPLEX, font_scale*0.8, (255,100,0), 2)

                image_placeholder_fight.image(cv2.cvtColor(frame_to_draw, cv2.COLOR_BGR2RGB), channels="RGB")
            
            cap_fight.release()
            if st.session_state.get('camera_active_fight_pg2', False):
                st.info("Төбелесті анықтау веб-камерасы тоқтатылды (циклдан шығу).")
                st.session_state.camera_active_fight_pg2 = False

if not st.session_state.get('camera_active_fight_pg2', False):
    if not start_button_fight:
        image_placeholder_fight.info("Төбелесті анықтау веб-камерасы тоқтатылды.")
        status_placeholder_fight.empty()


st.markdown("---")
st.subheader("Модуль Сипаттамасы:")
st.markdown("- Ықтимал агрессивті мінез-құлықты анықтау үшін білектердің қозғалыс жылдамдығын талдайды.")
st.markdown("- Дене/қол түйінді нүктелерін анықтау үшін **MediaPipe Pose** (немесе сіздің конфигурацияңызға байланысты Hands) қолданылады.")
st.markdown("- Бұл қарапайым эвристика және **жалған нәтижелер беруі мүмкін.** Мұқият тестілеу және параметрлерді дәлдеу қажет.")

