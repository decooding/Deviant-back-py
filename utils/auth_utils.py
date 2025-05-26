# utils/auth_utils.py
from sqlalchemy.orm import Session
from passlib.context import CryptContext # Құпия сөзді хештеу үшін

# Импорттар сіздің models.py және database.py файлдарыңызға сәйкес болуы керек
# Жобаның түбірлік бумасын sys.path-қа қосуды ұмытпаңыз, егер utils басқа деңгейде болса
import sys
import os
# PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # Егер auth_utils utils ішінде болса
# if PROJECT_ROOT not in sys.path:
#     sys.path.append(PROJECT_ROOT)
# Егер utils түбірде болса, жоғарыдағы қажет емес.
# Мына импорттар сіздің models.py және database.py файлдарыңызға дұрыс жолды көрсетуі керек:
from models import User  # models.py файлындағы User моделі
from database import SessionLocal, engine, Base # database.py файлынан

# Құпия сөзді хештеу контексті
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Қарапайым құпия сөзді хештелген құпия сөзбен салыстырады."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Құпия сөзді хештейді."""
    return pwd_context.hash(password)

def get_user_by_username(db: Session, username: str):
    """Пайдаланушыны аты бойынша дерекқордан алады."""
    return db.query(User).filter(User.username == username).first()

def create_db_user(db: Session, username: str, password: str):
    """Жаңа пайдаланушыны дерекқорға тіркейді."""
    existing_user = get_user_by_username(db, username)
    if existing_user:
        return None # Пайдаланушы бұрыннан бар
    hashed_password = get_password_hash(password)
    db_user = User(username=username, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Дерекқор сессиясын алу функциясы (database.py файлынан көшірілген немесе импортталған)
# Егер database.py файлында get_db функциясы болса, оны осы жерде қайта анықтаудың қажеті жоқ,
# оны тікелей Streamlit бетінде импорттауға болады.
# Бірақ ыңғайлылық үшін оны осында да қалдыруға болады.
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Кестелерді құру (егер олар әлі құрылмаған болса)
# Бұл негізгі app_ui.py немесе main.py файлында бір рет шақырылуы керек
def create_tables():
    Base.metadata.create_all(bind=engine)

# create_tables() # Бұл жолды осында шақырмаңыз, оны негізгі скриптте бір рет шақырыңыз