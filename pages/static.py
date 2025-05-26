# pages/08_Модульдер_Статистикасы.py (Файл атауын осылай өзгертуге болады)
import streamlit as st
import pandas as pd # Кейбір метрикаларды әдемі көрсету үшін
import os
# --- Streamlit бетінің конфигурациясы (бірінші команда) ---
st.set_page_config(page_title="Модульдер Статистикасы", layout="wide", initial_sidebar_state="expanded")

# --- Бет тақырыбы ---
st.title("📊 Анықтау Модульдерінің Жұмыс Статистикасы")
st.markdown("Бұл бет ағымдағы сессияда әртүрлі анықтау модульдерінің жұмысы бойынша жиналған статистиканы көрсетеді.")
st.markdown("---")

st.sidebar.title("МОДУЛЬДЕР") 
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
    if os.path.exists(page_file_path.replace("/", os.sep)) or page_file_path == "app.py": # Немесе сіздің негізгі файл атауыңыз
        st.sidebar.page_link(page_file_path, label=page_label)
    else:
        st.sidebar.caption(f"{page_label} (бет табылмады: {page_file_path})")
st.sidebar.markdown("---")


# --- Бір модульдің метрикаларын көрсету функциясы ---
def display_module_metrics(module_name_kz, 
                           frames_processed_key, 
                           detections_key, 
                           detection_name_singular_kz, 
                           detection_name_plural_kz=None,
                           is_audio_module=False):
    st.subheader(module_name_kz)
    if detection_name_plural_kz is None:
        detection_name_plural_kz = detection_name_singular_kz

    processed_count = st.session_state.get(frames_processed_key, 0)
    
    col1, col2 = st.columns(2)
    processed_label_kz = "Өңделген аудио фрагменттер" if is_audio_module else "Өңделген кадрлар"
    col1.metric(processed_label_kz, processed_count)

    detections_data_or_count = st.session_state.get(detections_key)

    if isinstance(detections_data_or_count, dict): 
        if detections_data_or_count:
            total_detections = sum(detections_data_or_count.values())
            col2.metric(f"Барлығы {detection_name_plural_kz} анықталды", total_detections)
            st.markdown(f"**Анықталған {detection_name_plural_kz.lower()} түрлері бойынша егжей-тегжейлі:**")
            
            filtered_detections_data = {k: v for k, v in detections_data_or_count.items() if v > 0}
            if filtered_detections_data:
                try:
                    df = pd.DataFrame(list(filtered_detections_data.items()), columns=['Түрі', 'Саны'])
                    df = df.sort_values(by='Саны', ascending=False).reset_index(drop=True)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                except Exception as e:
                    st.error(f"'{module_name_kz}' үшін DataFrame құру кезінде қате: {e}")
                    st.write(filtered_detections_data)
            else:
                st.info(f"{detection_name_plural_kz.capitalize()} әзірге анықталмады.")
        else: 
            col2.metric(f"Анықталған {detection_name_plural_kz}", 0)
            st.info(f"{detection_name_plural_kz.capitalize()} әзірге анықталмады.")
    elif isinstance(detections_data_or_count, (int, float)): 
        col2.metric(f"Анықталған {detection_name_plural_kz}", int(detections_data_or_count))
    elif detections_data_or_count is None: 
        col2.metric(f"Анықталған {detection_name_plural_kz}", 0)
        st.info(f"'{detection_name_plural_kz.capitalize()}' үшін деректер әзірге жоқ.")
    else: 
        col2.info(f"'{detection_name_plural_kz.capitalize()}' үшін күтпеген деректер форматы: {type(detections_data_or_count)}")

    st.markdown("---")

# --- Әрбір модуль үшін метрикаларды көрсету ---
# МАҢЫЗДЫ: frames_processed_key және detections_key мәндері сіздің әрбір модуль бетіңіздегі 
# st.session_state кілттеріне ДӘЛ СӘЙКЕС КЕЛУІ КЕРЕК.

# 1. Құлауды Анықтау
display_module_metrics(
    "🤸 1. Құлауды Анықтау",
    frames_processed_key='metrics_frames_processed_fall_pg1', 
    detections_key='metrics_falls_detected_pg1',
    detection_name_singular_kz="құлау", 
    detection_name_plural_kz="құлаулар"
)

# 2. Төбелесті Анықтау (Эвристика)
display_module_metrics(
    "🥊 2. Төбелесті Анықтау (Эвристика)",
    frames_processed_key='metrics_frames_processed_fight_pg2',
    detections_key='metrics_fights_detected_pg2',
    detection_name_singular_kz="төбелес (эвристика)", 
    detection_name_plural_kz="төбелестер (эвристика)"
)

# 3. Эмоцияларды Классификациялау
display_module_metrics(
    "😊 3. Эмоцияларды Классификациялау",
    frames_processed_key='metrics_frames_processed_emotion_pg3', # _v3 немесе сіздің соңғы кілтіңіз
    detections_key='metrics_emotions_detected_counts_pg3',    # _v3 немесе сіздің соңғы кілтіңіз
    detection_name_singular_kz="эмоция", 
    detection_name_plural_kz="эмоциялар"
)

# 4. Көмек Сигналын Анықтау
display_module_metrics(
    "✋ 4. Көмек Сигналын Анықтау",
    frames_processed_key='metrics_frames_processed_help_signal_pg4', 
    detections_key='metrics_help_signals_detected_pg4',
    detection_name_singular_kz="көмек сигналы", 
    detection_name_plural_kz="көмек сигналдары"
)

# 5. Қаруды Анықтау (YOLO)
display_module_metrics(
    "🔫 5. Қаруды Анықтау (YOLO)",
    frames_processed_key='metrics_frames_processed_weapon_pg5', 
    detections_key='metrics_weapons_detected_counts_pg5', 
    detection_name_singular_kz="қару", 
    detection_name_plural_kz="қарулар"
)

# 6. Дыбыстық Аномалияларды Анықтау
display_module_metrics(
    "🔊 6. Дыбыстық Аномалияларды Анықтау",
    frames_processed_key='metrics_audio_chunks_processed_sound_pg6', 
    detections_key='metrics_sounds_detected_counts_page6', 
    detection_name_singular_kz="дыбыстық аномалия", 
    detection_name_plural_kz="дыбыстық аномалиялар",
    is_audio_module=True 
)

# --- Статистиканы ысыру түймесі ---
st.markdown("---")
if st.button("Ағымдағы сессияның барлық статистикасын ысыру", key="reset_all_metrics_button_pg08_kz"):
    # Біз қолданатын барлық метрика кілттерінің тізімі
    metric_keys_to_reset = [
        'metrics_frames_processed_fall_pg1', 'metrics_falls_detected_pg1',
        'metrics_frames_processed_fight_pg2', 'metrics_fights_detected_pg2',
        'metrics_frames_processed_emotion_pg3', 'metrics_emotions_detected_counts_pg3', # _v3 немесе сіздің соңғы кілтіңіз
        'metrics_frames_processed_help_signal_pg4', 'metrics_help_signals_detected_pg4',
        'metrics_frames_processed_weapon_pg5', 'metrics_weapons_detected_counts_pg5',
        'metrics_audio_chunks_processed_sound_page6', 'metrics_sounds_detected_counts_page6'
    ]
    for key in metric_keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]
    st.success("Ағымдағы сессияның статистикасы сәтті ысырылды!")
    st.rerun()

st.caption("Ескертпе: Статистика браузер беті жабылғанда немесе Streamlit қосымшасы толығымен қайта іске қосылғанда (тек бет емес), сондай-ақ жоғарыдағы түймені басқанда ысырылады.")