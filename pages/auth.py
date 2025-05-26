# pages/00_Авторизация.py
import streamlit as st
import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

try:
    from utils.auth_utils import verify_password, get_user_by_username, create_db_user, get_db_session, create_tables
    AUTH_UTILS_AVAILABLE = True
except ImportError as e:
    st.error(f"Авторизация утилиталарын импорттау қатесі: {e}. utils/auth_utils.py файлын тексеріңіз.")
    AUTH_UTILS_AVAILABLE = False

# Streamlit бетінің конфигурациясы
st.set_page_config(page_title="Авторизация", layout="centered", initial_sidebar_state="collapsed")

if AUTH_UTILS_AVAILABLE and 'db_tables_created_auth_page' not in st.session_state:
    try:
        create_tables()
        st.session_state.db_tables_created_auth_page = True
        # st.toast("Дерекқор кестелері тексерілді/құрылды.")
    except Exception as e_db:
        st.error(f"Дерекқор кестелерін құру қатесі: {e_db}")


# Сессия күйінде кіру статусын инициализациялау
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'login_error' not in st.session_state:
    st.session_state.login_error = None
if 'register_message' not in st.session_state:
    st.session_state.register_message = None


def handle_login(username_login, password_login, db_session):
    user = get_user_by_username(db_session, username_login)
    if user and verify_password(password_login, user.password_hash):
        st.session_state.logged_in = True
        st.session_state.username = username_login
        st.session_state.login_error = None
        st.session_state.register_message = None # Басқа хабарламаларды тазалау
        st.success(f"Сәтті кірдіңіз, {username_login}!")
        st.rerun() # Басты бетке немесе басқа бетке өту үшін (немесе UI жаңарту)
    else:
        st.session_state.login_error = "Қате логин немесе құпия сөз."
        st.rerun()

def handle_registration(username_reg, password_reg, password_confirm_reg, db_session):
    if password_reg != password_confirm_reg:
        st.session_state.register_message = {"error": "Құпия сөздер сәйкес келмейді."}
        st.rerun()
        return
    if len(password_reg) < 6: # Қарапайым тексеру
        st.session_state.register_message = {"error": "Құпия сөз кем дегенде 6 таңбадан тұруы керек."}
        st.rerun()
        return

    user = create_db_user(db_session, username_reg, password_reg)
    if user:
        st.session_state.register_message = {"success": f"{username_reg} пайдаланушысы сәтті тіркелді! Енді жүйеге кіре аласыз."}
    else:
        st.session_state.register_message = {"error": f"{username_reg} пайдаланушысы бұрыннан бар немесе басқа қате."}
    st.rerun()

# Егер пайдаланушы жүйеге кірген болса, оны негізгі бетке бағыттауға немесе басқа әрекет жасауға болады.
# Бұл беттің мақсаты - кіру/тіркелу формаларын көрсету.
if st.session_state.logged_in:
    st.success(f"Сіз жүйеге {st.session_state.username} болып кірдіңіз.")
    st.markdown("Басты бетке өту үшін сайдбарды пайдаланыңыз немесе [осы жерді басыңыз](app.py).") # app.py сіздің негізгі файлыңыздың аты
    if st.button("Шығу", key="logout_button_authpage"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.login_error = None
        st.session_state.register_message = None
        st.rerun()
else:
    st.title("🔐 Авторизация")

    if not AUTH_UTILS_AVAILABLE:
        st.error("Авторизация модулі қазір қолжетімсіз. Импорттау қателерін тексеріңіз.")
        st.stop()

    tab1, tab2 = st.tabs(["🔑 Кіру", "📝 Тіркелу"])

    with tab1:
        st.subheader("Жүйеге кіру")
        with st.form("login_form"):
            username_login = st.text_input("Логин", key="login_username")
            password_login = st.text_input("Құпия сөз", type="password", key="login_password")
            submitted_login = st.form_submit_button("Кіру")

            if st.session_state.login_error:
                st.error(st.session_state.login_error)
                st.session_state.login_error = None # Қатені бір рет көрсету

            if submitted_login:
                if not username_login or not password_login:
                    st.warning("Логин мен құпия сөзді енгізіңіз.")
                else:
                    db_gen = get_db_session()
                    db = next(db_gen)
                    try:
                        handle_login(username_login, password_login, db)
                    finally:
                        db.close()
                        
    with tab2:
        st.subheader("Жаңа аккаунт құру")
        with st.form("registration_form"):
            username_reg = st.text_input("Логин таңдаңыз", key="reg_username")
            password_reg = st.text_input("Құпия сөз ойлап табыңыз", type="password", key="reg_password")
            password_confirm_reg = st.text_input("Құпия сөзді қайталаңыз", type="password", key="reg_password_confirm")
            submitted_registration = st.form_submit_button("Тіркелу")

            if st.session_state.register_message:
                msg_data = st.session_state.register_message
                if "success" in msg_data:
                    st.success(msg_data["success"])
                elif "error" in msg_data:
                    st.error(msg_data["error"])
                st.session_state.register_message = None # Хабарламаны бір рет көрсету


            if submitted_registration:
                if not username_reg or not password_reg or not password_confirm_reg:
                    st.warning("Барлық өрістерді толтырыңыз.")
                else:
                    db_gen = get_db_session()
                    db = next(db_gen)
                    try:
                        handle_registration(username_reg, password_reg, password_confirm_reg, db)
                    finally:
                        db.close()