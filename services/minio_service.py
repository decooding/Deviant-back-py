import os
import uuid
import logging
from minio import Minio

# Логирование
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Конфигурация из переменных окружения
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
BUCKET_NAME = os.getenv("BUCKET_NAME", "videos")

# Инициализация клиента MinIO
client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False,
)

# Проверка и создание бакета
try:
    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)
        logger.info(f"🪣 MinIO: Бакет `{BUCKET_NAME}` создан")
    else:
        logger.info(f"✅ MinIO: Бакет `{BUCKET_NAME}` уже существует")
except Exception as e:
    logger.error(f"❌ Ошибка подключения к MinIO: {str(e)}")


# 📥 Функция скачивания файла из MinIO
def download_from_minio(object_name: str) -> str:
    """
    Скачивает объект object_name из MinIO и сохраняет его во временную директорию.
    Возвращает путь к локальному файлу.
    """
    os.makedirs("temp", exist_ok=True)
    local_path = os.path.join("temp", f"{uuid.uuid4()}_{object_name}")

    try:
        client.fget_object(BUCKET_NAME, object_name, local_path)
        logger.info(f"⬇️ Видео {object_name} скачано в {local_path}")
        return local_path
    except Exception as e:
        logger.error(f"❌ Ошибка при скачивании {object_name} из MinIO: {str(e)}")
        raise
