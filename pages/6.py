# pages/6_Дыбыстық_Аномалияларды_Анықтау.py

import streamlit as st
import numpy as np
import sys
import os
import time
from st_audiorec import st_audiorec # streamlit-audio-recorder импорты
import librosa # Аудионы қайта дискреттеу және WAV байттарын өңдеу үшін
import io # Байттармен жұмыс істеу үшін

# Жобаның түбірлік бумасын sys.path-қа қосу
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Модельдер мен ресурстарға жолдар
MODEL_DIR = os.path.join(PROJECT_ROOT, "ml_models")
YAMNET_MODEL_PATH = os.path.join(MODEL_DIR, "yamnet.tflite")
YAMNET_CLASS_MAP_PATH = os.path.join(MODEL_DIR, "yamnet_class_map.csv")
ALARM_SOUND_PATH = os.path.join(PROJECT_ROOT, "static_assets", "alarm.wav")

# SoundAnomalyDetector класын импорттау
SoundAnomalyDetector_class_to_use = None
import_error_details = None
_successfully_imported_real_detector = False
YAMNET_EXPECTED_SAMPLE_RATE_DEFAULT = 16000
YAMNET_EXPECTED_SAMPLE_RATE = YAMNET_EXPECTED_SAMPLE_RATE_DEFAULT

try:
    from ml.sound_anomaly_detector import SoundAnomalyDetector, YAMNET_EXPECTED_SAMPLE_RATE as YAMNET_SR_FROM_MODULE
    SoundAnomalyDetector_class_to_use = SoundAnomalyDetector
    YAMNET_EXPECTED_SAMPLE_RATE = YAMNET_SR_FROM_MODULE
    _successfully_imported_real_detector = True
except ImportError as e_imp:
    import_error_details = f"SoundAnomalyDetector класын ml.sound_anomaly_detector файлынан импорттау қатесі: {e_imp}. TensorFlow/TFLite runtime орнатылғанына көз жеткізіңіз."
except Exception as e_gen:
    import_error_details = f"SoundAnomalyDetector класын импорттау кезінде БАСҚА қате: {e_gen}. ml/sound_anomaly_detector.py файлын тексеріңіз."

# --- Streamlit бетінің конфигурациясы (бірінші команда) ---
st.set_page_config(page_title="Дыбыстық Аномалияларды Анықтау", layout="wide", initial_sidebar_state="expanded")

# --- Импорт қателерін көрсету және тығын класын анықтау ---
if import_error_details:
    st.error(import_error_details)

class DummySoundAnomalyDetectorForPage6:
    def __init__(self, *args, **kwargs):
        if not _successfully_imported_real_detector:
            st.warning("НАЗАР АУДАРЫҢЫЗ: SoundAnomalyDetector ТЫҒЫНЫ қолданылуда!")
        st.info(f"SoundAnomalyDetector тығыны инициализацияланды.")
        self.model = True # Модельдің бар екенін имитациялау
        self.detection_threshold = kwargs.get('detection_threshold', 0.3)

    def process_audio_chunk(self, chunk, sr):
        time.sleep(0.1)
        return [f"Тығын: оқиға {int(time.time() % 5)} (сенімділік: {self.detection_threshold:.2f})"]
    def close(self):
        st.info("SoundAnomalyDetector тығынының close әдісі шақырылды.")
    def _log_to_ui(self, message):
        log_key = 'sound_detector_debug_log_page6'
        if log_key not in st.session_state: st.session_state[log_key] = []
        st.session_state[log_key].insert(0, f"{time.strftime('%H:%M:%S')} - DUMMY: {message}")
        st.session_state[log_key] = st.session_state[log_key][:30]

if not _successfully_imported_real_detector:
    SoundAnomalyDetector_class_to_use = DummySoundAnomalyDetectorForPage6

# --- Метрика кілттерін инициализациялау ---
METRICS_AUDIO_CHUNKS_KEY_SOUND = 'metrics_audio_chunks_processed_sound_pg6'
METRICS_DETECTIONS_KEY_SOUND = 'metrics_sounds_detected_counts_pg6' # Сөздік үшін

if METRICS_AUDIO_CHUNKS_KEY_SOUND not in st.session_state:
    st.session_state[METRICS_AUDIO_CHUNKS_KEY_SOUND] = 0
if METRICS_DETECTIONS_KEY_SOUND not in st.session_state:
    st.session_state[METRICS_DETECTIONS_KEY_SOUND] = {}

# --- Қосымшаның негізгі UI бөлігі ---
st.title("Модуль : Дыбыстық Аномалияларды Анықтау (YAMNet)")
st.markdown("Микрофоннан нақты уақытта дыбыстарды классификациялау үшін YAMNet моделін қолданады.")

model_files_ok_sound = True
if not os.path.exists(YAMNET_MODEL_PATH):
    st.error(f"YAMNet моделінің файлы табылмады: {YAMNET_MODEL_PATH}")
    model_files_ok_sound = False
if not os.path.exists(YAMNET_CLASS_MAP_PATH):
    st.error(f"YAMNet класс картасының файлы табылмады: {YAMNET_CLASS_MAP_PATH}")
    model_files_ok_sound = False


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
st.sidebar.subheader("Аудиожазба Басқару")
# Детекторды инициализациялау
detector_session_key_sound = 'sound_anomaly_detector_instance_page6_v2' # Кілтті жаңарттық
detection_threshold_slider_val_pg6 = st.sidebar.slider(
    "Дыбыс сенімділік шегі", 0.0, 1.0, 0.3, 0.05, key="sound_thresh_slider_pg6_v2"
)

if detector_session_key_sound not in st.session_state:
    if _successfully_imported_real_detector and model_files_ok_sound and SoundAnomalyDetector_class_to_use:
        custom_target_anomalies_map_sound = {
            "Scream": "АЙҚАЙ!", "Shout": "ҚАТТЫ АЙҚАЙ/ШАҚЫРУ!", "Yell": "БАҚЫРУ!",
            "Child crying": "БАЛА ЖЫЛАУЫ!", "Glass": "ШЫНЫ СЫНҒАН ДЫБЫС!",
            "Gunshot, gunfire": "АТЫС ДЫБЫСЫ!", "Explosion": "ЖАРЫЛЫС!",
            "Alarm": "ДАБЫЛ СИГНАЛЫ (дыбыс)", "Siren": "СИРЕНА"
        }
        st.session_state[detector_session_key_sound] = SoundAnomalyDetector_class_to_use(
            model_path=YAMNET_MODEL_PATH,
            class_map_path=YAMNET_CLASS_MAP_PATH,
            target_anomalies=custom_target_anomalies_map_sound,
            detection_threshold=detection_threshold_slider_val_pg6 # Слайдерден алу
        )
    elif SoundAnomalyDetector_class_to_use: # Тығын класы қолданылса
        st.session_state[detector_session_key_sound] = SoundAnomalyDetector_class_to_use(
            detection_threshold=detection_threshold_slider_val_pg6
        )

# Детектор параметрін жаңарту, егер слайдер өзгерсе
sound_detector_instance = st.session_state.get(detector_session_key_sound)
if sound_detector_instance and hasattr(sound_detector_instance, 'detection_threshold') and \
   sound_detector_instance.detection_threshold != detection_threshold_slider_val_pg6:
    sound_detector_instance.detection_threshold = detection_threshold_slider_val_pg6
    if _successfully_imported_real_detector:
        sound_detector_instance._log_to_ui(f"Детектордың сенімділік шегі жаңартылды: {detection_threshold_slider_val_pg6}")


# st_audiorec компонентін пайдалану
st.write("Дыбысты жазу үшін төмендегі түймені басыңыз, содан кейін талдау үшін тоқтатыңыз.")
audio_bytes = st_audiorec() # Бұл виджет микрофонды іске қосады және жазылған байттарды қайтарады

detected_anomalies_display_sound = st.empty()
alarm_sound_played_sound_pg6 = st.session_state.get('alarm_played_sound_pg6', False)

if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")
    st.info("Аудио жазылды, талдау жүргізілуде...")
    
    sound_detector = st.session_state.get(detector_session_key_sound)
    if sound_detector:
        try:
            # librosa WAV байттарын оқу үшін
            # streamlit-audio-recorder WAV форматында қайтарады
            audio_np, sr = librosa.load(io.BytesIO(audio_bytes), sr=None, mono=True) # sr=None түпнұсқа жиілікті алу үшін
            
            # Метрика: өңделген аудио фрагменттер
            st.session_state[METRICS_AUDIO_CHUNKS_KEY_SOUND] += 1

            # Аудио фрагментті өңдеу
            detected_anomalies = sound_detector.process_audio_chunk(audio_np, sr)

            if detected_anomalies:
                anomalies_str = ", ".join(detected_anomalies)
                detected_anomalies_display_sound.error(f"🚨 Аномалиялар анықталды: {anomalies_str}")
                
                # Метрика: анықталған дыбыстық аномалиялар
                current_sound_counts = st.session_state.get(METRICS_DETECTIONS_KEY_SOUND, {})
                for anomaly_full_str in detected_anomalies:
                    # Тек таза атауын алу (сенімділіксіз)
                    anomaly_name = anomaly_full_str.split(' (')[0] 
                    current_sound_counts[anomaly_name] = current_sound_counts.get(anomaly_name, 0) + 1
                st.session_state[METRICS_DETECTIONS_KEY_SOUND] = current_sound_counts
                
                if not alarm_sound_played_sound_pg6:
                    if os.path.exists(ALARM_SOUND_PATH):
                        try:
                            with open(ALARM_SOUND_PATH, "rb") as audio_file_bytes_main:
                                st.audio(audio_file_bytes_main.read(), format="audio/wav", start_time=0)
                            st.toast("🎶 Дабыл сигналы ойнатылуда (дыбыс)!", icon="🚨")
                        except Exception as e_audio_main_thread:
                            st.warning(f"Дыбысты ойнату мүмкін болмады: {e_audio_main_thread}")
                    else:
                        st.warning(f"Дабыл дыбысы файлы табылмады: {ALARM_SOUND_PATH}")
                    st.session_state.alarm_played_sound_pg6 = True # Бір рет ойнату
            else:
                detected_anomalies_display_sound.success("Жазылған аудиода аномалиялар анықталмады.")
                st.session_state.alarm_played_sound_pg6 = False # Егер аномалия жоқ болса, дабылды қайта қосуға болады
        except Exception as e:
            st.error(f"Аудионы өңдеу кезінде қате: {e}")
            detected_anomalies_display_sound.empty()
            st.session_state.alarm_played_sound_pg6 = False
    else:
        st.error("Дыбыс детекторы жүктелмеген.")
        detected_anomalies_display_sound.empty()
        st.session_state.alarm_played_sound_pg6 = False
else:
    detected_anomalies_display_sound.info("Аномалды дыбыстарды анықтау үшін аудио жазыңыз.")
    st.session_state.alarm_played_sound_pg6 = False



st.markdown("---")
st.subheader("Модуль Сипаттамасы:")
st.markdown("""
- Микрофоннан жазылған дыбыстық оқиғаларды классификациялау үшін **YAMNet** (TensorFlow Lite моделі) қолданады.
- Ықтимал аномалды дыбыстарды (айқай, шыны сынуы, атыс т.б.) анықтап, көрсетеді.
- **Жұмыс істеу үшін микрофонға рұқсат қажет.** `streamlit-audio-recorder` компоненті аудио жазу үшін микрофонды пайдаланады.
- **Дәлдік YAMNet моделінің сапасына және қоршаған ортадағы шу деңгейіне байланысты.**
""")