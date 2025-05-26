# ml/sound_anomaly_detector.py
import numpy as np
import pandas as pd
import librosa # Для передискретизации и работы с аудио
import os
import time
import streamlit as st
try:
    import tflite_runtime.interpreter as tflite
except ImportError:
    try:
        # ОСЫ ӘРЕКЕТ ЕНДІ СӘТТІ ОРЫНДАЛУЫ КЕРЕК,
        # себебі толық tensorflow орнатуы tensorflow.lite модулін қамтамасыз етеді
        import tensorflow.lite as tflite
        print("INFO: TensorFlow Lite runtime толық TensorFlow орнатуынан жүктелді.")
    except ImportError:
        tflite = None
        print("ЕСКЕРТУ: TensorFlow Lite tflite-runtime ретінде де, толық TensorFlow ішінде де табылмады.")
        
# Константы для YAMNet
YAMNET_EXPECTED_SAMPLE_RATE = 16000
YAMNET_WINDOW_SIZE_SAMPLES = int(YAMNET_EXPECTED_SAMPLE_RATE * 0.975) # ~15600 samples
YAMNET_HOP_SIZE_SAMPLES = int(YAMNET_EXPECTED_SAMPLE_RATE * 0.4875)   # ~7800 samples
YAMNET_MIN_SAMPLES_FOR_INFERENCE = YAMNET_WINDOW_SIZE_SAMPLES

class SoundAnomalyDetector:
    def _log_to_ui(self, message): # <--- ОСЫ ӘДІС БАР
        """Streamlit session_state-ке логикалық ақпаратты жазуға арналған қосалқы функция."""
        # Осы беттің логтары үшін бірегей кілтті пайдаланыңыз
        log_key = 'sound_detector_debug_log_page6' 
        if log_key not in st.session_state:
            st.session_state[log_key] = []
        log_entry = f"{time.strftime('%H:%M:%S')} - {message}"
        st.session_state[log_key].insert(0, log_entry) # Жаңа логтарды жоғарыдан қосу
        # Лог өлшемін шектеу, жадты/UI-ді толтырып алмау үшін
        st.session_state[log_key] = st.session_state[log_key][:30] 

    def __init__(self, model_path, class_map_path, 
                 target_anomalies=None, detection_threshold=0.3):
        self.model = None
        self.class_map_df = None
        self.target_anomalies_map = target_anomalies if target_anomalies else {
            # Примеры классов из YAMNet (нужно проверить точные названия в yamnet_class_map.csv)
            "Speech": "Речь",
            "Screaming": "КРИК",
            "Shout": "Громкий крик/возглас",
            "Yell": "Вопль",
            "Children shouting": "Детский плач",
            "Glass": "ЗВУК СТЕКЛА", # Обычно 'Glass' или 'Breaking'
            "Gunshot, gunfire": "ВЫСТРЕЛ",
            "Explosion": "ВЗРЫВ",
            "Alarm": "СИГНАЛ ТРЕВОГИ (звук)",
            "Siren": "СИРЕНА"
        }
        self.detection_threshold = detection_threshold # Порог уверенности для детекции
        self.audio_buffer = np.array([], dtype=np.float32)

        if not tflite:
            print("SoundAnomalyDetector: TensorFlow Lite не доступен.")
            return
            
        if not os.path.exists(model_path):
            print(f"SoundAnomalyDetector: Файл модели YAMNet не найден: {model_path}")
            return
        
        if not os.path.exists(class_map_path):
            print(f"SoundAnomalyDetector: Файл карты классов YAMNet не найден: {class_map_path}")
            return

        try:
            self.model = tflite.Interpreter(model_path=model_path)
            self.model.allocate_tensors()
            self.input_details = self.model.get_input_details()
            self.output_details = self.model.get_output_details()
            
            # YAMNet ожидает вход формы (1, 15600) - это один фрейм аудио
            # Входной тензор обычно float32 в диапазоне [-1.0, 1.0]
            print(f"SoundAnomalyDetector: Модель YAMNet загружена. Вход: {self.input_details[0]['shape']}, тип: {self.input_details[0]['dtype']}")

            self.class_map_df = pd.read_csv(class_map_path)
            # Проверяем, что 'displayName' есть в CSV, AudioSet использует это поле для читаемых имен
            if 'displayName' not in self.class_map_df.columns and 'display_name' in self.class_map_df.columns:
                 self.class_map_df.rename(columns={'display_name': 'displayName'}, inplace=True)

            if 'displayName' not in self.class_map_df.columns:
                print("ПРЕДУПРЕЖДЕНИЕ: В CSV файле карты классов отсутствует колонка 'displayName'. Используется первая колонка.")
                self.class_map_df['displayName'] = self.class_map_df.iloc[:,0]


            print("SoundAnomalyDetector: Карта классов YAMNet загружена.")

        except Exception as e:
            print(f"SoundAnomalyDetector: Ошибка инициализации - {e}")
            self.model = None
            self.class_map_df = None

    def _preprocess_audio_chunk(self, audio_chunk_np, input_sample_rate):
        self._log_to_ui(f"Preprocessing: input shape {audio_chunk_np.shape}, input SR {input_sample_rate}")
        
        # Аудионы міндетті түрде 1D массивке айналдыру
        if audio_chunk_np.ndim > 1:
            self._log_to_ui(f"  Input chunk is {audio_chunk_np.ndim}D, attempting to flatten to 1D.")
            # Егер (N, 1) немесе (1, N) болса, .flatten() немесе .ravel() қолдануға болады
            # Немесе егер стерео болса, орташалау (біз мұны librosa.load-та mono=True арқылы жасаймыз)
            audio_chunk_np = audio_chunk_np.ravel() # Массивті 1D етеді

        if input_sample_rate != YAMNET_EXPECTED_SAMPLE_RATE:
            self._log_to_ui(f"Resampling from {input_sample_rate} to {YAMNET_EXPECTED_SAMPLE_RATE}")
            audio_chunk_np = librosa.resample(audio_chunk_np, orig_sr=input_sample_rate, target_sr=YAMNET_EXPECTED_SAMPLE_RATE)
        
        min_val, max_val = np.min(audio_chunk_np), np.max(audio_chunk_np)
        self._log_to_ui(f"Audio chunk after processing: shape {audio_chunk_np.shape}, min {min_val:.2f}, max {max_val:.2f}")
        if max_val > 1.0 or min_val < -1.0:
            self._log_to_ui("WARNING: Audio chunk values out of [-1, 1] range. Clamping.")
            audio_chunk_np = np.clip(audio_chunk_np, -1.0, 1.0)
        return audio_chunk_np

    def process_audio_chunk(self, audio_chunk_np, input_sample_rate):
        if not self.model or self.class_map_df is None:
            self._log_to_ui("Model or class map not loaded, skipping processing.")
            return []

        # Алдын ала өңдеу (бұл жерде audio_chunk_np 1D болуы керек)
        processed_chunk = self._preprocess_audio_chunk(audio_chunk_np, input_sample_rate)
        
        # processed_chunk 1D екеніне көз жеткізу
        if processed_chunk.ndim > 1:
            self._log_to_ui(f"ERROR: Processed chunk is still {processed_chunk.ndim}D before buffer. Flattening.")
            processed_chunk = processed_chunk.ravel()

        self.audio_buffer = np.concatenate([self.audio_buffer, processed_chunk])
        self._log_to_ui(f"Buffer size: {len(self.audio_buffer)}")

        detected_anomalies_in_chunk = []

        while len(self.audio_buffer) >= YAMNET_MIN_SAMPLES_FOR_INFERENCE:
            self._log_to_ui(f"Processing window from buffer. Buffer remaining: {len(self.audio_buffer)}")
            waveform_to_predict = self.audio_buffer[:YAMNET_WINDOW_SIZE_SAMPLES].astype(self.input_details[0]['dtype'])
            
            self.audio_buffer = self.audio_buffer[YAMNET_HOP_SIZE_SAMPLES:]
            
            # --- ОСЫ ЖЕРДЕ ТЕКСЕРУ ЖӘНЕ ТҮЗЕТУ ---
            # YAMNet кіріс формасы әдетте (N,) немесе (15600,) болады, бірақ set_tensor үшін (1, 15600) қажет.
            # Егер input_details[0]['shape'] [15600] болса (кейбір TFLite модельдері осылай көрсетеді),
            # бірақ set_tensor batch өлшемін күтсе, біз оны қосуымыз керек.
            # Егер input_details[0]['shape'] [1, 15600] болса, онда waveform_to_predict-ке batch өлшемі қажет емес.

            input_tensor_shape = self.input_details[0]['shape']
            self._log_to_ui(f"  Waveform to predict shape: {waveform_to_predict.shape}")
            self._log_to_ui(f"  Model expected input shape (from input_details): {input_tensor_shape}")

            # Егер waveform_to_predict 1D болса, бірақ модель 2D (batch, samples) күтсе:
            if waveform_to_predict.ndim == 1 and len(input_tensor_shape) == 2 and input_tensor_shape[0] == 1:
                input_for_model = np.expand_dims(waveform_to_predict, axis=0)
                self._log_to_ui(f"  Expanded waveform to shape: {input_for_model.shape} for model.")
            elif waveform_to_predict.ndim == 1 and len(input_tensor_shape) == 1 and waveform_to_predict.shape[0] == input_tensor_shape[0]:
                # Модель 1D күтеді (N_samples), бірақ set_tensor кейде batch өлшемін қажет етеді.
                # Бұл жағдай сирек кездеседі, әдетте модельдер batch өлшемін күтеді.
                # Егер модель шынымен 1D күтсе, онда np.expand_dims қажет емес.
                # Дегенмен, TFLite Interpreter жиі batch өлшемі бар кірісті күтеді.
                # Көп жағдайда, егер waveform_to_predict (15600,) болса, оны (1, 15600) ету керек.
                input_for_model = np.expand_dims(waveform_to_predict, axis=0) # Қауіпсіздік үшін batch қосамыз
                self._log_to_ui(f"  Model expects 1D input, but added batch dim for safety: {input_for_model.shape}")
            elif waveform_to_predict.shape == tuple(input_tensor_shape): # Егер формалар дәл келсе
                 input_for_model = waveform_to_predict # Batch өлшемі қазірдің өзінде бар (мысалы, (1, 15600) )
                 self._log_to_ui(f"  Waveform shape matches model input_details shape: {input_for_model.shape}")
            else:
                # Егер waveform_to_predict 1D болса және модель де 1D күтсе (бірақ set_tensor үшін batch керек)
                # немесе басқа сәйкессіздік болса, стандартты batch қосуды қолданамыз.
                # Бұл ең жиі кездесетін жағдай: waveform_to_predict (15600,) -> input_for_model (1, 15600)
                if waveform_to_predict.ndim == 1:
                    input_for_model = np.expand_dims(waveform_to_predict, axis=0)
                    self._log_to_ui(f"  Defaulting to adding batch dimension: {input_for_model.shape}")
                else:
                    self._log_to_ui(f"ERROR: Waveform shape {waveform_to_predict.shape} cannot be directly reshaped to model input {input_tensor_shape}")
                    continue # Бұл терезені өткізіп жіберу


            # Қайта тексеру, модель кірісінің формасы дұрыс екеніне көз жеткізу
            if tuple(input_for_model.shape) != tuple(self.input_details[0]['shape']):
                 # Егер модель, мысалы, [15600] күтсе, бірақ біз [1, 15600] жіберсек,
                 # кейбір Interpreter-лер мұны қабылдауы мүмкін.
                 # Бірақ қате "Got 2 but expected 1" керісінше жағдайды білдіреді:
                 # модель 1D күтеді, бірақ 2D (batch, samples) жіберілді.
                 # Бұл YAMNet үшін өте сирек жағдай, ол әдетте batch өлшемі бар кірісті күтеді.
                 # Егер input_details[0]['shape'] == [15600] болса:
                 if list(self.input_details[0]['shape']) == [YAMNET_WINDOW_SIZE_SAMPLES] and input_for_model.ndim == 2 and input_for_model.shape[0] == 1:
                     input_for_model = input_for_model.squeeze(axis=0) # Batch өлшемін алып тастау
                     self._log_to_ui(f"  Squeezed input for model to shape: {input_for_model.shape}")
                 else:
                    self._log_to_ui(f"ERROR: Final input shape {input_for_model.shape} STILL MISMATCHES model expected {self.input_details[0]['shape']}")
                    continue


            self.model.set_tensor(self.input_details[0]['index'], input_for_model)
            self.model.invoke()
            scores = self.model.get_tensor(self.output_details[0]['index'])[0] 

            # ... (қалған код өзгеріссіз) ...
            self._log_to_ui("--- Top YAMNet Scores ---")
            # ...
        return list(set(detected_anomalies_in_chunk))
    
    def close(self):
        # Для TFLite Interpreter нет явного метода close()
        print("SoundAnomalyDetector: Ресурсы освобождены (если были).")