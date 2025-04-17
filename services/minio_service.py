from minio import Minio
import os
import uuid

# Загружаем параметры из переменных окружения
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ROOT_USER = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_ROOT_PASSWORD = os.getenv("MINIO_ROOT_PASSWORD", "minioadmin")
BUCKET_NAME = os.getenv("BUCKET_NAME", "videos")
MINIO_SECURE = os.getenv("MINIO_SECURE", "False").lower() == "true"

# Инициализируем клиента MinIO
minio_client = Minio(
    MINIO_ENDPOINT,
    access_key=MINIO_ROOT_USER,
    secret_key=MINIO_ROOT_PASSWORD,
    secure=MINIO_SECURE,
)

# Создаём бакет, если не существует
if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME)


def upload_to_minio(local_file_path: str) -> str:
    """
    Загружает локальный файл в MinIO и возвращает имя объекта.
    """
    object_name = os.path.basename(local_file_path)
    minio_client.fput_object(BUCKET_NAME, object_name, local_file_path)
    return object_name


def download_from_minio(object_name: str) -> str:
    """
    Скачивает файл из MinIO во временную папку и возвращает путь.
    """
    os.makedirs("temp", exist_ok=True)
    local_path = os.path.join("temp", f"{uuid.uuid4()}_{object_name}")
    minio_client.fget_object(BUCKET_NAME, object_name, local_path)
    return local_path
