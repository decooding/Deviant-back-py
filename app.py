# БАСТЫ_БЕТ.py (или app_ui.py)
import streamlit as st
import os
st.set_page_config(
    page_title="ДМҚАЖ - Басты бет", # Девиантті Мінез-Құлықты Анықтау Жүйесі - Главная
    page_icon="⚠️", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- КАСТОМНАЯ НАВИГАЦИЯ В САЙДБАРЕ ---
st.sidebar.title("МОДУЛЬДЕР") # Ваш заголовок для навигации
st.sidebar.markdown("---")
# Определяем страницы, которые будут в видимой навигации
# Ключ - как будет отображаться, значение - путь к файлу
# ВАЖНО: Пути должны быть относительно корневой папки вашего приложения (где лежит БАСТЫ_БЕТ.py)
# Файлы страниц должны существовать по этим путям.
# Если файл переименован с '_' в начале (например, _08_Статистика_Модулей.py), он НЕ БУДЕТ здесь отображаться,
# но будет доступен по прямой ссылке из вашего блочного навигатора.

# Список страниц для отображения в сайдбаре
# Убедитесь, что имена файлов точные и соответствуют вашей структуре папки pages/
# Если главный файл (БАСТЫ_БЕТ.py) тоже должен быть в этом списке, добавьте его первым.
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
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    with st.container(border=True): 
        st.subheader("📊 Статистика Модулей") 
        st.markdown("Барлық детекция модульдерінің жұмыс статистикасын қарау.")
        stats_page_file = "pages/static.py" # Убедитесь, что файл скрыт, если не нужен в сайдбаре
        st.markdown("---")
        if os.path.exists(stats_page_file.replace("/", os.sep)):
             st.page_link(stats_page_file, label="📊 Статистикаға өту", use_container_width=True)


with row1_col2:
    with st.container(border=True): # Оставил высоту для примера
        st.subheader("📹 Видеолар")
        st.markdown("Colab-та немесе басқа модульдерде өңдеу үшін видеофайлдарды басқару.")
        st.markdown("---")
        video_resources_page_file = "pages/_static.py" 
        if os.path.exists(video_resources_page_file.replace("/", os.sep)):
            st.page_link(video_resources_page_file, label="🎬 Видеоларды басқару", use_container_width=True, icon="📹")


row2_col1, row2_col2 = st.columns(2) # Предполагаем, что эти блоки тоже есть

with row2_col1:
    st.markdown('<div class="clickable-card-wrapper">', unsafe_allow_html=True)
    with st.container(border=True): # Убрал высоту
        st.subheader("👁️ Детекторлар Демонстрациясы")
        st.markdown("Веб-камера арқылы әртүрлі детекторлардың жұмысын тікелей көрсету.")
        st.markdown("(Прямой доступ к модулям детекции с веб-камеры.)")
        st.markdown(" ")
        first_demo_page_file = "pages/1_Детекция_Падений.py" 
        if os.path.exists(first_demo_page_file.replace("/", os.sep)):
            st.page_link(first_demo_page_file, label="➡️ Демонстрацияларға өту", use_container_width=True, icon="👁️")
        else:
            st.button("➡️ Демонстрацияларға (недоступно)", key="nav_demos_unavailable_main_styled", use_container_width=True, disabled=True)
    st.markdown('</div>', unsafe_allow_html=True)

with row2_col2:
    st.markdown('<div class="clickable-card-wrapper">', unsafe_allow_html=True)
    with st.container(border=True): # Убрал высоту
        st.subheader("🔔 Дабылдар Журналы")
        st.markdown("Жүйеде тіркелген оқиғалар мен дабылдарды қарау.")
        st.markdown("(Просмотр зарегистрированных событий и тревог из системы.)")
        st.markdown(" ")
        # Убедитесь, что имя файла для журнала тревог корректно и уникально
        alerts_log_page_file = "pages/09_Дабылдар_Журналы.py" # Пример, если статистика это 08_
        if os.path.exists(alerts_log_page_file.replace("/", os.sep)):
            st.page_link(alerts_log_page_file, label="🔔 Журналды ашу", use_container_width=True, icon="🔔")
        else:
            st.button("🔔 Журналды ашу (недоступно)", key="nav_alerts_unavailable_main_styled", use_container_width=True, disabled=True)
    st.markdown('</div>', unsafe_allow_html=True)


st.markdown("---")
st.caption("© 2025 Ваше Имя. Барлық құқықтар қорғалған.")