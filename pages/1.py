# pages/1_Детекция_Падений.py (yoki pages/1_Құлауды_Анықтау.py deb nomlashingiz mumkin)
import streamlit as st
import cv2
import sys
import os
import time 

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

_successfully_imported_real_fall_detector = False
FallDetector_class_to_use = None
fall_import_error_details = None

try:
    from ml.fall_detector import FallDetector as RealFallDetector
    FallDetector_class_to_use = RealFallDetector
    _successfully_imported_real_fall_detector = True
except ImportError as e_fall_imp:
    fall_import_error_details = f"FallDetector класын ml.fall_detector файлынан импорттау қатесі: {e_fall_imp}."
except Exception as e_fall_gen:
    fall_import_error_details = f"FallDetector класын импорттау кезінде БАСҚА қате: {e_fall_gen}."


st.set_page_config(page_title="Құлауды Анықтау", layout="wide", initial_sidebar_state="expanded")

if fall_import_error_details:
    st.error(fall_import_error_details)

class DummyFallDetectorForPage1: # Тығын үшін бірегей атау
    def __init__(self, *args, **kwargs):
        if not _successfully_imported_real_fall_detector:
            st.warning("НАЗАР АУДАРЫҢЫЗ: FallDetector ТЫҒЫНЫ қолданылуда!")
        st.info(f"FallDetector тығыны инициализацияланды.")
        self.mp_drawing = None
        class DummyPoseSolution: POSE_CONNECTIONS = []
        self.mp_pose_solution = DummyPoseSolution()
        self.fall_aspect_ratio_threshold = kwargs.get('aspect_ratio_threshold', 1.2)
        self.fall_confirmation_frames_threshold = kwargs.get('confirmation_frames', 5)

    def process_frame(self, frame):
        return {"is_fallen": False, "person_detected": False, "aspect_ratio": 0.0, "bounding_box": None, "pose_landmarks_object": None}
    def close(self):
        st.info("FallDetector тығынының close әдісі шақырылды.")

if not _successfully_imported_real_fall_detector:
    FallDetector_class_to_use = DummyFallDetectorForPage1

if 'metrics_frames_processed_fall' not in st.session_state:
    st.session_state.metrics_frames_processed_fall = 0
if 'metrics_falls_detected' not in st.session_state:
    st.session_state.metrics_falls_detected = 0


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

st.title("Модуль 01: Адамның Құлауын Анықтау")
st.markdown("Нақты уақыт режимінде құлауды анықтау үшін MediaPipe Pose қолданады.")

fall_detector_session_key = 'fall_detector_instance_pg1' 

if fall_detector_session_key not in st.session_state:
    if FallDetector_class_to_use:
        aspect_ratio_thresh = st.sidebar.slider("Құлау үшін AR шегі", 0.5, 2.5, 1.2, 0.1, key="fall_ar_thresh_pg1_kz")
        confirm_frames = st.sidebar.number_input("Құлауды растау кадрлары", 1, 20, 5, 1, key="fall_confirm_frames_pg1_kz")
        st.session_state[fall_detector_session_key] = FallDetector_class_to_use(
            aspect_ratio_threshold=aspect_ratio_thresh, 
            confirmation_frames=confirm_frames
        )
    else:
        st.error("Сыни қате: FallDetector класы анықталмаған.")
        st.stop()


col1, col2 = st.columns([3, 1])

with col2:
    st.subheader("Басқару")
    start_button = st.button("Веб-камераны іске қосу", key="start_fall_btn_pg1_kz")
    stop_button = st.button("Веб-камераны тоқтату", key="stop_fall_btn_pg1_kz")
    
    st.markdown("---")
    st.subheader("Детектор параметрлері:")
    current_fall_detector = st.session_state.get(fall_detector_session_key)
    if current_fall_detector:
        st.caption(f"Ағымдағы AR шегі: {current_fall_detector.fall_aspect_ratio_threshold}")
        st.caption(f"Ағымдағы растау кадрлары: {current_fall_detector.fall_confirmation_frames_threshold}")
    else:
        st.caption("Детектор инициализацияланбаған.")


with col1:
    image_placeholder_fall = st.empty() # Плейсхолдер үшін бірегей атау
    if not st.session_state.get('camera_active_fall_pg1', False) and not start_button:
         image_placeholder_fall.info("Анықтауды бастау үшін 'Веб-камераны іске қосу' түймесін басыңыз.")

if start_button:
    st.session_state.camera_active_fall_pg1 = True

if stop_button:
    st.session_state.camera_active_fall_pg1 = False

if st.session_state.get('camera_active_fall_pg1', False):
    cap_fall = cv2.VideoCapture(0) # VideoCapture үшін бірегей атау
    if not cap_fall.isOpened():
        st.error("Веб-камераны ашу мүмкін болмады.")
        st.session_state.camera_active_fall_pg1 = False
    else:
        fall_detector_obj_loop = st.session_state.get(fall_detector_session_key)
        if not fall_detector_obj_loop:
            st.error("Цикл үшін FallDetector данасы сессияда табылмады!")
            st.session_state.camera_active_fall_pg1 = False
        else:
            mp_drawing_utils = getattr(fall_detector_obj_loop, 'mp_drawing', None)
            mp_pose_solution_connections = None
            if hasattr(fall_detector_obj_loop, 'mp_pose_solution') and fall_detector_obj_loop.mp_pose_solution:
                mp_pose_solution_connections = getattr(fall_detector_obj_loop.mp_pose_solution, 'POSE_CONNECTIONS', None)
            
            default_drawing_spec = mp_drawing_utils.DrawingSpec(thickness=1, circle_radius=1) if mp_drawing_utils else None

            while st.session_state.camera_active_fall_pg1: 
                ret, frame = cap_fall.read()
                if not ret:
                    st.warning("Кадр өткізіліп кетті немесе камера күтпеген жерден тоқтатылды.")
                    st.session_state.camera_active_fall_pg1 = False 
                    break

                st.session_state.metrics_frames_processed_fall += 1

                processed_frame_for_drawing = frame.copy()
                result = fall_detector_obj_loop.process_frame(frame.copy()) 

                status_text = "stand" 
                text_color = (0, 255, 0) 

                if not result.get("person_detected", False): 
                    status_text = "person NOT detected"
                    text_color = (100, 100, 100)
                elif result.get("is_fallen", False):
                    status_text = "falling!"
                    text_color = (0, 0, 255) 
                    st.session_state.metrics_falls_detected += 1
                
                if result.get("person_detected") and result.get("pose_landmarks_object") and \
                   mp_drawing_utils and mp_pose_solution_connections:
                    mp_drawing_utils.draw_landmarks(
                        processed_frame_for_drawing,
                        result["pose_landmarks_object"],
                        mp_pose_solution_connections, 
                        landmark_drawing_spec=getattr(fall_detector_obj_loop, 'drawing_spec_landmarks', default_drawing_spec) or default_drawing_spec,
                        connection_drawing_spec=getattr(fall_detector_obj_loop, 'drawing_spec_connections', default_drawing_spec) or default_drawing_spec
                    )
                
                font_scale = min(frame.shape[1], frame.shape[0]) / 500.0 
                cv2.putText(processed_frame_for_drawing, status_text, (20, int(30*font_scale*2)), cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, 2, cv2.LINE_AA)
                cv2.putText(processed_frame_for_drawing, f"AR: {result.get('aspect_ratio', 0.0):.2f}", (20, int(60*font_scale*2)), cv2.FONT_HERSHEY_SIMPLEX, font_scale*0.7, (255,0,0), 2, cv2.LINE_AA)
                
                image_placeholder_fall.image(cv2.cvtColor(processed_frame_for_drawing, cv2.COLOR_BGR2RGB), channels="RGB")
            
            cap_fall.release()
            if st.session_state.get('camera_active_fall_pg1', False): 
                st.info("Құлауды анықтау веб-камерасы тоқтатылды (циклдан шығу).")
                st.session_state.camera_active_fall_pg1 = False 

if not st.session_state.get('camera_active_fall_pg1', False):
    if not start_button: 
        image_placeholder_fall.info("Құлауды анықтау веб-камерасы тоқтатылды.")

st.markdown("---")
st.subheader("Модуль Сипаттамасы:")
st.markdown("- Веб-камерадан дене түйінді нүктелерін анықтау үшін **MediaPipe Pose** қолданады.")
st.markdown("- Поза контурының **тараптар қатынасын** (ені/биіктігі) талдайды.")
st.markdown("- Егер қатынас бірнеше кадр бойы белгіленген шектен асып кетсе, құлау тіркеледі.")