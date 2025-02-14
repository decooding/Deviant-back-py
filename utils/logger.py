import logging
import os

# Создаем папку logs, если её нет
if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/api.log", encoding="utf-8"),
        logging.StreamHandler(),  # Вывод в консоль
    ],
)

logger = logging.getLogger("app_logger")
