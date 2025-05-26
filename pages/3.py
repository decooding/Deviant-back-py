# pages/3_Эмоцияларды_Классификациялау.py
# (немесе pages/3_emotion_detection.py, сіздің трейсбектегідей)

# -----------------------------------------------------------------------------
# 1. СТАНДАРТТЫ ИМПОРТТАР ЖӘНЕ STREAMLIT-КЕ ЖАТПАЙТЫН ЛОГИКА (жолдар, айнымалылар)
# -----------------------------------------------------------------------------
import streamlit as st
import cv2
import numpy as np
import sys
import os
import time 

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# --- МАҢЫЗДЫ: ОСЫ ЖЕРДЕ ӨЗІҢІЗДІҢ TFLITE ЭМОЦИЯ МОДЕЛІ ФАЙЛЫНЫҢ ДҰРЫС АТАУЫН КӨРСЕТІҢІЗ ---
# Мысалы, "custom_cnn_model.tflite" MdIrfan325 репозиторийінен
# немесе "emotion_affectnet_mobilenet.tflite" егер сіз оны конверттесеңіз және ол сәйкес кірісті күтсе
MODEL_FILENAME = "emotion_affectnet_mobilenet.tflite"  # ФАЙЛ АТАУЫН ӨЗІҢІЗДІҢ АТАУЫҢЫЗБЕН АЛМАСТЫРЫҢЫЗ
PATH_TO_EMOTION_MODEL_TFLITE = os.path.join(PROJECT_ROOT, "ml_models", MODEL_FILENAME) 

EmotionDetector_class_to_use = None
import_error_details = None
_successfully_imported_real_detector = False # Нақты детекторды сәтті импорттау туы

try:
    from ml.emotion_detector import EmotionDetector as RealEmotionDetector
    EmotionDetector_class_to_use = RealEmotionDetector
    _successfully_imported_real_detector = True
except ImportError as e_imp:
    import_error_details = f"EmotionDetector класын ml.emotion_detector файлынан импорттау қатесі: {e_imp}."
except Exception as e_gen:
    import_error_details = f"EmotionDetector класын импорттау кезінде БАСҚА қате: {e_gen}."

# -----------------------------------------------------------------------------
# 2. st.set_page_config() ШАҚЫРУЫ - ЕҢ БІРІНШІ STREAMLIT КОМАНДАСЫ
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Эмоцияларды Классификациялау (TFLite)", layout="wide", initial_sidebar_state="expanded")

# -----------------------------------------------------------------------------
# 3. ИМПОРТ ҚАТЕЛЕРІН КӨРСЕТУ (ЕГЕР БОЛСА) ЖӘНЕ ТЫҒЫНДЫ (ЗАГЛУШКА) АНЫҚТАУ
# -----------------------------------------------------------------------------
if import_error_details:
    st.error(import_error_details)

# Негізгі импорт сәтсіз болған жағдайда тығын класын анықтаймыз
# Бұл EmotionDetector_class_to_use None болып қалғанда NameError болдырмау үшін
class DummyEmotionDetectorForPage3: 
    def __init__(self, model_path=None, *args, **kwargs):
        if not _successfully_imported_real_detector: 
             st.warning("НАЗАР АУДАРЫҢЫЗ: EmotionDetector ТЫҒЫНЫ қолданылуда (негізгі класс импортталмады)!")
        st.info(f"EmotionDetector тығыны инициализацияланды (модельге күтілетін жол: {model_path}).")
        self.mp_drawing = None; self.mp_face_mesh = type('Dummy', (), {'FACEMESH_TESSELATION': []})(); 
        self.drawing_spec_landmarks = None; self.drawing_spec_connections = None;
        self.target_emotion_map = {}; self.interpreter = None; self.model = None # Keras үлгісі үшін
    def process_frame(self, frame): return {"raw_emotion_english": "N/A (Тығын)", "face_detected": False, "face_landmarks_for_drawing": None}
    def close(self): st.info("EmotionDetector тығынының close әдісі шақырылды.")
    def _log_to_ui(self, message): 
         if 'emotion_detector_debug_log_page3' not in st.session_state: st.session_state.emotion_detector_debug_log_page3 = []
         st.session_state.emotion_detector_debug_log_page3.insert(0, f"{time.strftime('%H:%M:%S')} - DUMMY: {message}")
         st.session_state.emotion_detector_debug_log_page3 = st.session_state.emotion_detector_debug_log_page3[:30]

if not _successfully_imported_real_detector: # Егер импорт сәтсіз болса
    EmotionDetector_class_to_use = DummyEmotionDetectorForPage3

# -----------------------------------------------------------------------------
# 4. STREAMLIT ҚОСЫМШАСЫНЫҢ ҚАЛҒАН БӨЛІГІ
# -----------------------------------------------------------------------------

# Метрика кілттерін инициализациялау (осы бетке бірегей)
METRICS_FRAMES_KEY_EMOTION = 'metrics_frames_processed_emotion_pg3'
METRICS_DETECTIONS_KEY_EMOTION = 'metrics_emotions_detected_counts_pg3'

if METRICS_FRAMES_KEY_EMOTION not in st.session_state:
    st.session_state[METRICS_FRAMES_KEY_EMOTION] = 0
if METRICS_DETECTIONS_KEY_EMOTION not in st.session_state:
    st.session_state[METRICS_DETECTIONS_KEY_EMOTION] = {} # Эмоцияларды санау үшін сөздік


st.title("Модуль 03: Бет-әлпет бойынша Эмоцияларды Классификациялау (TFLite)")
st.markdown("Эмоцияларды классификациялау үшін MediaPipe Face Detection/Mesh және **TFLite моделін** қолданады.")

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


# Модель файлының бар-жоғын тексеру
model_file_exists_for_emotion_page = False
if _successfully_imported_real_detector: 
    if os.path.exists(PATH_TO_EMOTION_MODEL_TFLITE):
        model_file_exists_for_emotion_page = True
    else:
        st.error(
            f"TFLite эмоция моделінің файлы ({MODEL_FILENAME}) мына жолда табылмады: {PATH_TO_EMOTION_MODEL_TFLITE}. "
            f"Нақты детектор модельді жүктей алмайды."
        )
elif EmotionDetector_class_to_use is DummyEmotionDetectorForPage3: 
    model_file_exists_for_emotion_page = True 

# Детекторды Streamlit сессиясының күйінде инициализациялау
detector_session_key_emotion = 'emotion_detector_instance_page3_v3' 
if detector_session_key_emotion not in st.session_state:
    if EmotionDetector_class_to_use:
        st.session_state[detector_session_key_emotion] = EmotionDetector_class_to_use(model_tflite_path=PATH_TO_EMOTION_MODEL_TFLITE)
    else:
        st.error("Сыни қате: EmotionDetector класы данасын құру үшін қол жетімді емес.")
        st.stop()

col1, col2 = st.columns([3, 1]) 

with col2:
    st.subheader("Басқару")
    start_button_emotion = st.button("Веб-камераны іске қосу", key="start_emotion_btn_pg3_v3")
    stop_button_emotion = st.button("Веб-камераны тоқтату", key="stop_emotion_btn_pg3_v3")
    st.markdown("---")
    st.subheader("Мақсатты эмоциялар (Көрсетілім):")
    
    current_detector_instance_display = st.session_state.get(detector_session_key_emotion)
    if hasattr(current_detector_instance_display, 'target_emotion_map') and current_detector_instance_display.target_emotion_map:
        main_target_emotions_rus = ["Страх", "Гнев", "Отчаяние/Грусть", "Удивление"] # Сіздің негізгі мақсаттарыңыз
        for eng_emotion, rus_emotion in current_detector_instance_display.target_emotion_map.items():
            if rus_emotion in main_target_emotions_rus: 
                 st.markdown(f"- **{rus_emotion}** (ағыл. *{eng_emotion}*)")
    else: 
        st.markdown("- Қорқыныш\n- Ашу\n- Қайғы/Түңілу\n- Таңдану")

    if _successfully_imported_real_detector:
        if model_file_exists_for_emotion_page:
             if hasattr(current_detector_instance_display, 'interpreter') and \
                current_detector_instance_display.interpreter is not None:
                st.caption(f"Модель жүктелді: {MODEL_FILENAME}")
             else:
                st.caption(f"Модель: {MODEL_FILENAME} (жүктеу қатесі, логтарды қараңыз)")
        else: 
            st.caption(f"{MODEL_FILENAME} модель файлы табылмады.")

with col1:
    image_placeholder_emotion = st.empty()
    if not st.session_state.get('camera_active_emotion_page3_v3', False) and not start_button_emotion : 
         image_placeholder_emotion.info("Эмоцияларды анықтауды бастау үшін 'Веб-камераны іске қосу' түймесін басыңыз.")

if start_button_emotion:
    st.session_state.camera_active_emotion_page3_v3 = True
if stop_button_emotion:
    st.session_state.camera_active_emotion_page3_v3 = False

detector_ready_for_processing = False
emotion_detector_to_use_in_loop = st.session_state.get(detector_session_key_emotion)

if emotion_detector_to_use_in_loop:
    if not _successfully_imported_real_detector: 
        detector_ready_for_processing = True 
    elif _successfully_imported_real_detector and model_file_exists_for_emotion_page:
        if hasattr(emotion_detector_to_use_in_loop, 'interpreter') and emotion_detector_to_use_in_loop.interpreter is not None:
            detector_ready_for_processing = True
        # else: Логтар конструктордан немесе файлды тексеруден шығуы керек
    # else: Файл табылмады, лог шығуы керек
    
if not detector_ready_for_processing and _successfully_imported_real_detector : 
    st.sidebar.error("Эмоция детекторы дайын емес (модель жүктелмеген немесе файл табылмады). UI логтарын тексеріңіз.")

if st.session_state.get('camera_active_emotion_page3_v3', False):
    if not detector_ready_for_processing:
        st.error("Эмоция детекторы жұмысқа дайын емес. Сайдбардағы және логтардағы қате хабарламаларын немесе модель файлының бар-жоғын тексеріңіз.")
        st.session_state.camera_active_emotion_page3_v3 = False 
    else:
        cap_emotion = cv2.VideoCapture(0)
        if not cap_emotion.isOpened():
            st.error("Веб-камераны ашу мүмкін болмады.")
            st.session_state.camera_active_emotion_page3_v3 = False
        else:
            mp_drawing_utils = getattr(emotion_detector_to_use_in_loop, 'mp_drawing', None)
            mp_face_mesh_connections_val = None 
            if hasattr(emotion_detector_to_use_in_loop, 'mp_face_mesh') and emotion_detector_to_use_in_loop.mp_face_mesh:
                 mp_face_mesh_connections_val = getattr(emotion_detector_to_use_in_loop.mp_face_mesh, 'FACEMESH_TESSELATION', None) 
            
            drawing_spec_landmarks = getattr(emotion_detector_to_use_in_loop, 'drawing_spec_landmarks', None)
            drawing_spec_connections = getattr(emotion_detector_to_use_in_loop, 'drawing_spec_connections', None)
            default_drawing_spec = mp_drawing_utils.DrawingSpec(thickness=1, circle_radius=1) if mp_drawing_utils else None

            while st.session_state.camera_active_emotion_page3_v3:
                ret, frame = cap_emotion.read()
                if not ret:
                    st.warning("Кадр өткізіліп кетті (Эмоциялар).")
                    st.session_state.camera_active_emotion_page3_v3 = False; break

                st.session_state[METRICS_FRAMES_KEY_EMOTION] += 1


                frame_to_draw = frame.copy() 
                result = emotion_detector_to_use_in_loop.process_frame(frame.copy()) 

                emotion_text_on_video = result.get("raw_emotion_english", "N/A") # Ағылшынша көрсету үшін
                text_color = (200, 0, 200) 

                if not result.get("face_detected", False):
                    emotion_text_on_video = "Бет анықталмады" # Бет-әлпет табылмады
                    text_color = (100, 100, 100)
                elif not ("N/A" in emotion_text_on_video or "Заглушка" in emotion_text_on_video or "Model not loaded" in emotion_text_on_video or "Inference Error" in emotion_text_on_video or "Index Error" in emotion_text_on_video):
                    # МЕТРИКА: Анықталған эмоцияларды санау
                    current_emotion_counts = st.session_state.get(METRICS_DETECTIONS_KEY_EMOTION, {})
                    current_emotion_counts[emotion_text_on_video] = current_emotion_counts.get(emotion_text_on_video, 0) + 1
                    st.session_state[METRICS_DETECTIONS_KEY_EMOTION] = current_emotion_counts
                    # Түс логикасы (ағылшынша белгілерге негізделген)
                    if "Fear" == emotion_text_on_video: text_color = (0,100,200) 
                    elif "Anger" == emotion_text_on_video: text_color = (0,0,255) 
                    elif "Sad" == emotion_text_on_video: text_color = (150,50,0)
                    elif "Surprise" == emotion_text_on_video: text_color = (0,200,200)
                    elif "Happy" == emotion_text_on_video: text_color = (0,255,0)
                    elif "Neutral" == emotion_text_on_video: text_color = (200,200,200)
                    elif "Disgust" == emotion_text_on_video: text_color = (100,0,100)
                    elif "Contempt" == emotion_text_on_video: text_color = (255,165,0)
                
                if result.get("face_landmarks_for_drawing") and mp_drawing_utils and mp_face_mesh_connections_val:
                    mp_drawing_utils.draw_landmarks(
                        image=frame_to_draw,
                        landmark_list=result["face_landmarks_for_drawing"],
                        connections=mp_face_mesh_connections_val, 
                        landmark_drawing_spec=drawing_spec_landmarks if drawing_spec_landmarks else default_drawing_spec,
                        connection_drawing_spec=drawing_spec_connections if drawing_spec_connections else default_drawing_spec
                    )
                
                font_scale = min(frame.shape[1], frame.shape[0]) / 700.0 
                cv2.putText(frame_to_draw, f"Эмоция: {emotion_text_on_video}", (20, int(30*font_scale*2.5)), 
                            cv2.FONT_HERSHEY_SIMPLEX, font_scale, text_color, 2, cv2.LINE_AA)

                image_placeholder_emotion.image(cv2.cvtColor(frame_to_draw, cv2.COLOR_BGR2RGB), channels="RGB")

            cap_emotion.release()
            if st.session_state.get('camera_active_emotion_page3_v3', False): 
                st.info("Эмоцияларды анықтау веб-камерасы тоқтатылды (циклдан шығу).")
                st.session_state.camera_active_emotion_page3_v3 = False 

if not st.session_state.get('camera_active_emotion_page3_v3', False):
    if not start_button_emotion: 
        image_placeholder_emotion.info("Эмоцияларды анықтау веб-камерасы тоқтатылды.")



st.markdown("---")
st.subheader("Модуль Сипаттамасы:")
st.markdown("""
- Бет-әлпетті анықтау үшін **MediaPipe Face Detection** қолданады.
- Анықталған бет-әлпеттің кесілген суреті эмоцияларды классификациялау үшін **TensorFlow Lite (.tflite)** моделіне беріледі.
- Бет-әлпеттің негізгі нүктелерінің торын визуализациялау үшін **MediaPipe Face Mesh** қолданады.
- Көрсетілетін эмоциялар (егер модель оларды болжаса): Қорқыныш, Ашу, Қайғы/Түңілу, Таңдану, Қуаныш, Бейтарап, Жиіркеніш, Менсінбеу.
""")