# pages/5_Қаруды_Анықтау.py
import streamlit as st
import cv2
import numpy as np
import sys
import os
import time # _log_to_ui үшін (егер WeaponDetector-да болса)

# Жобаның түбірлік бумасын sys.path-қа қосу
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Дабыл дыбысы файлының жолы
ALARM_SOUND_PATH = os.path.join(PROJECT_ROOT, "static_assets", "alarm.wav") # Файлдың бар екеніне көз жеткізіңіз

# WeaponDetector негізгі класын импорттау әрекеті
_successfully_imported_real_weapon_detector = False
WeaponDetector_class_to_use = None
weapon_import_error_details = None
try:
    from ml.weapon_detector import WeaponDetector as RealWeaponDetector
    WeaponDetector_class_to_use = RealWeaponDetector
    _successfully_imported_real_weapon_detector = True
except ImportError as e_weapon_imp:
    weapon_import_error_details = f"WeaponDetector класын ml.weapon_detector файлынан импорттау қатесі: {e_weapon_imp}. Ultralytics кітапханасының орнатылғанына көз жеткізіңіз."
except Exception as e_weapon_gen:
    weapon_import_error_details = f"WeaponDetector класын импорттау кезінде БАСҚА қате: {e_weapon_gen}."

# --- ЖАЛПЫ БАПТАУЛАР ---
DEFAULT_MODEL_PATH_WEAPON = os.path.join(PROJECT_ROOT, "ml", "yolov8n.pt")
DEFAULT_TARGET_CLASSES_WEAPON = "knife" 

# -----------------------------------------------------------------------------
st.set_page_config(page_title="Қаруды Анықтау", layout="wide", initial_sidebar_state="expanded")
# -----------------------------------------------------------------------------

if weapon_import_error_details:
    st.error(weapon_import_error_details)

class DummyWeaponDetectorForPage5:
    def __init__(self, model_path=None, confidence_threshold=0.4, target_classes=None, device='cpu', *args, **kwargs):
        if not _successfully_imported_real_weapon_detector:
            st.warning("НАЗАР АУДАРЫҢЫЗ: WeaponDetector ТЫҒЫНЫ қолданылуда!")
        st.info(f"WeaponDetector тығыны инициализацияланды (модель жолы: {model_path}).")
        self.model = True # Имитируем наличие модели
        self.confidence_threshold = confidence_threshold
        self.target_classes = target_classes if target_classes else [DEFAULT_TARGET_CLASSES_WEAPON]

    def process_frame(self, frame): 
        return {"detected_weapons": [], "annotated_frame": frame, "error": "Тығын белсенді"}
    def close(self): 
        st.info("WeaponDetector тығынының close әдісі шақырылды.")

if not _successfully_imported_real_weapon_detector:
    WeaponDetector_class_to_use = DummyWeaponDetectorForPage5

# --- Осы бет үшін метрика кілттерін инициализациялау ---
METRICS_FRAMES_KEY_WEAPON = 'metrics_frames_processed_weapon_pg5'
METRICS_DETECTIONS_KEY_WEAPON = 'metrics_weapons_detected_counts_pg5' # Сөздік үшін

if METRICS_FRAMES_KEY_WEAPON not in st.session_state:
    st.session_state[METRICS_FRAMES_KEY_WEAPON] = 0
if METRICS_DETECTIONS_KEY_WEAPON not in st.session_state:
    st.session_state[METRICS_DETECTIONS_KEY_WEAPON] = {} # Әр қару түрі үшін санауыш

# --- Қосымшаның негізгі бөлігі ---
st.title("Модуль 05: Қаруды Анықтау (YOLO)")
st.markdown("Веб-камерадағы видеодан ықтимал қаруды анықтау үшін YOLO моделін қолданады.")

if not _successfully_imported_real_weapon_detector and WeaponDetector_class_to_use is DummyWeaponDetectorForPage5 : # Егер тек тығын болса
    st.error("Негізгі детектор класы жүктелмеген, функционалдылық шектеулі болады.")

# Сайдбардағы баптаулар

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
st.sidebar.subheader("Қару Детекторының Баптаулары")
model_path_input_pg5 = st.sidebar.text_input("YOLO моделіне жол (.pt)", DEFAULT_MODEL_PATH_WEAPON, key="weapon_model_path_pg5")
confidence_thresh_slider_pg5 = st.sidebar.slider("Анықтау сенімділік шегі", 0.0, 1.0, 0.4, 0.05, key="weapon_conf_slider_pg5")
target_classes_input_pg5 = st.sidebar.text_input("Мақсатты кластар (үтір арқылы)", DEFAULT_TARGET_CLASSES_WEAPON, key="weapon_target_classes_pg5").lower()

# Детекторды Streamlit сессиясының күйінде инициализациялау
session_key_detector_wpn = "weapon_detector_instance_page5_v2"
session_key_model_path_wpn = "weapon_detector_model_path_page5_v2"
session_key_target_classes_wpn = "weapon_detector_target_classes_page5_v2"

target_classes_list_wpn = [cls.strip() for cls in target_classes_input_pg5.split(',') if cls.strip()]

current_detector_weapon = st.session_state.get(session_key_detector_wpn)
should_reinitialize_detector_weapon = False

if current_detector_weapon is None:
    should_reinitialize_detector_weapon = True
elif _successfully_imported_real_weapon_detector: # Тек нақты детектор үшін параметрлерді тексереміз
    # Бұл атрибуттар WeaponDetector класында болуы керек
    current_model_path = getattr(current_detector_weapon, 'model_path_loaded_with', model_path_input_pg5) # Модель сақтаған жолды алу керек
    current_target_classes = getattr(current_detector_weapon, 'target_classes_loaded', target_classes_list_wpn)

    if (current_model_path != model_path_input_pg5 or
        set(current_target_classes) != set(target_classes_list_wpn) ): # Тізімдерді салыстыру үшін жиындарды қолданамыз
        should_reinitialize_detector_weapon = True
        st.sidebar.info("Қару детекторының параметрлері өзгерді, қайта инициализацияланады.")


if should_reinitialize_detector_weapon:
    if WeaponDetector_class_to_use:
        st.session_state[session_key_detector_wpn] = WeaponDetector_class_to_use(
            model_path=model_path_input_pg5,
            # confidence_threshold конструкторға берілмейді, бірақ процесс кезінде қолданылады
            target_classes=target_classes_list_wpn,
            device='cuda' if cv2.cuda.getCudaEnabledDeviceCount() > 0 else 'cpu'
        )
        # Сақталған параметрлерді жаңарту (егер WeaponDetector оларды сақтаса)
        st.session_state[session_key_model_path_wpn] = model_path_input_pg5
        st.session_state[session_key_target_classes_wpn] = target_classes_list_wpn
        
        # Жаңадан инициализацияланған детекторды аламыз
        reinitialized_detector = st.session_state.get(session_key_detector_wpn)
        if _successfully_imported_real_weapon_detector:
            if hasattr(reinitialized_detector, 'model') and reinitialized_detector.model is not None:
                st.sidebar.success(f"Қару детекторы '{os.path.basename(model_path_input_pg5)}' моделімен инициализацияланды.")
                # Детектор ішіндегі target_class_indices тексеруі дұрыс жұмыс істеуі керек
            else:
                st.sidebar.error("YOLO моделі жүктелмеді. Жолды және файлды тексеріңіз.")
    elif session_key_detector_wpn not in st.session_state :
        st.error("Сыни қате: WeaponDetector класы анықталмаған.")
        st.stop()

col1, col2 = st.columns([3, 1])

with col2:
    st.subheader("Басқару")
    start_button_weapon = st.button("Веб-камераны іске қосу", key="start_weapon_btn_pg5_kz")
    stop_button_weapon = st.button("Веб-камераны тоқтату", key="stop_weapon_btn_pg5_kz")
    
    st.markdown("---")
    st.subheader("Күйі:")
    status_placeholder_weapon = st.empty()

with col1:
    image_placeholder_weapon = st.empty()
    if not st.session_state.get('camera_active_weapon_pg5', False) and not start_button_weapon:
         image_placeholder_weapon.info("Қаруды анықтауды бастау үшін 'Веб-камераны іске қосу' түймесін басыңыз.")

if start_button_weapon:
    st.session_state.camera_active_weapon_pg5 = True
    st.session_state.alarm_played_weapon_pg5 = False

if stop_button_weapon:
    st.session_state.camera_active_weapon_pg5 = False
    st.session_state.alarm_played_weapon_pg5 = False


# Детектордың дайындығын тексеру
detector_ready_weapon = False
weapon_detector_instance_loop = st.session_state.get(session_key_detector_wpn)
if weapon_detector_instance_loop:
    if isinstance(weapon_detector_instance_loop, DummyWeaponDetectorForPage5): # Егер тығын болса
        detector_ready_weapon = True
    elif _successfully_imported_real_weapon_detector and hasattr(weapon_detector_instance_loop, 'model') and weapon_detector_instance_loop.model is not None:
        detector_ready_weapon = True

if not detector_ready_weapon and _successfully_imported_real_weapon_detector :
    st.sidebar.error("Қару детекторы дайын емес (модель жүктелмеген немесе файл табылмады). UI логтарын тексеріңіз (егер WeaponDetector-да _log_to_ui болса).")


if st.session_state.get('camera_active_weapon_pg5', False):
    if not detector_ready_weapon:
        st.error("Қару детекторы жұмысқа дайын емес. Сайдбардағы баптауларды және модель файлының жолын тексеріңіз.")
        st.session_state.camera_active_weapon_pg5 = False
    else:
        cap_weapon = cv2.VideoCapture(0)
        if not cap_weapon.isOpened():
            st.error("Веб-камераны ашу мүмкін болмады.")
            st.session_state.camera_active_weapon_pg5 = False
        else:
            # confidence_threshold тікелей детектор экземплярына орнатылады
            weapon_detector_instance_loop.confidence_threshold = confidence_thresh_slider_pg5

            while st.session_state.camera_active_weapon_pg5:
                ret, frame = cap_weapon.read()
                if not ret:
                    st.warning("Кадр өткізіліп кетті (Қару).")
                    st.session_state.camera_active_weapon_pg5 = False
                    break
                
                # --- МЕТРИКА: ӨҢДЕЛГЕН КАДРЛАР ---
                st.session_state[METRICS_FRAMES_KEY_WEAPON] += 1
                # ---------------------------------

                result = weapon_detector_instance_loop.process_frame(frame)
                annotated_display_frame = result.get("annotated_frame", frame)

                if result.get("error"):
                    status_placeholder_weapon.error(f"Детектор қатесі: {result['error']}")
                elif result.get("detected_weapons"):
                    weapon_list_text = [f"{w['label']} ({w['confidence']:.2f})" for w in result["detected_weapons"]]
                    status_placeholder_weapon.error(f"🚨 ҚАРУ АНЫҚТАЛДЫ: {', '.join(weapon_list_text)} 🚨")
                    
                    # --- МЕТРИКА: АНЫҚТАЛҒАН ҚАРУ ТҮРЛЕРІ ---
                    current_weapon_counts = st.session_state.get(METRICS_DETECTIONS_KEY_WEAPON, {})
                    for w_info in result["detected_weapons"]:
                        weapon_label = w_info['label']
                        current_weapon_counts[weapon_label] = current_weapon_counts.get(weapon_label, 0) + 1
                    st.session_state[METRICS_DETECTIONS_KEY_WEAPON] = current_weapon_counts
                    # -----------------------------------------
                    
                    if not st.session_state.get('alarm_played_weapon_pg5', False):
                        if os.path.exists(ALARM_SOUND_PATH):
                            try:
                                with open(ALARM_SOUND_PATH, "rb") as audio_file:
                                    audio_bytes = audio_file.read()
                                st.audio(audio_bytes, format="audio/wav", start_time=0)
                                st.toast("🎶 Дабыл сигналы ойнатылуда (қару)!", icon="🚨")
                            except Exception as e_audio:
                                st.warning(f"Дыбысты ойнату мүмкін болмады: {e_audio}")
                        else:
                            st.warning(f"Дабыл дыбысы файлы табылмады: {ALARM_SOUND_PATH}")
                        st.session_state.alarm_played_weapon_pg5 = True
                else:
                    status_placeholder_weapon.success("Қару анықталмады.")
                    if st.session_state.get('alarm_played_weapon_pg5', False):
                         st.session_state.alarm_played_weapon_pg5 = False

                image_placeholder_weapon.image(cv2.cvtColor(annotated_display_frame, cv2.COLOR_BGR2RGB), channels="RGB")
            
            cap_weapon.release()
            if st.session_state.get('camera_active_weapon_pg5', False):
                st.info("Қаруды анықтау веб-камерасы тоқтатылды (циклдан шығу).")
                st.session_state.camera_active_weapon_pg5 = False

if not st.session_state.get('camera_active_weapon_pg5', False):
    status_placeholder_weapon.empty()
    if not start_button_weapon:
        image_placeholder_weapon.info("Қаруды анықтау веб-камерасы тоқтатылды.")

st.sidebar.markdown("---")
st.sidebar.subheader("Қару Детекторының Логтары (UI):")
weapon_detector_log_key = 'weapon_detector_debug_log_page5' # WeaponDetector ішіндегі кілтпен сәйкес келуі керек
if weapon_detector_log_key in st.session_state and st.session_state[weapon_detector_log_key]:
    log_text_ui_weapon = "\n".join(st.session_state[weapon_detector_log_key])
    st.sidebar.text_area("Лог:", value=log_text_ui_weapon, height=150, key="weapon_debug_log_area_ui_pg5_kz")
else:
    st.sidebar.text("UI логтары әзірге жоқ.")


st.markdown("---")
st.subheader("Модуль Сипаттамасы:")
st.markdown("- Веб-камерадағы нысандарды анықтау үшін **YOLO** моделін қолданады.")
st.markdown("- Қару ретінде жіктелген нысандарды анықтауға тырысады (әдепкі бойынша 'knife', тізімді өзгертуге болады).")
st.markdown("- **Дәлдік қолданылатын YOLO моделіне және оның қару кластарында оқытылуына байланысты.** Стандартты `yolov8n.pt` шектеулі.")